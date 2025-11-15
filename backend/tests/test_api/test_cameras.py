"""Integration tests for camera API endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import Base, get_db
from app.models.camera import Camera


# Create test database (file-based to avoid threading issues)
import tempfile
import os

# Use file-based SQLite for testing to avoid threading issues
test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.close(test_db_fd)

TEST_DATABASE_URL = f"sqlite:///{test_db_path}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Override database dependency
app.dependency_overrides[get_db] = override_get_db

# Create tables once
Base.metadata.create_all(bind=engine)

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def cleanup_database():
    """Clean up database between tests"""
    yield
    # Delete all cameras after each test
    db = TestingSessionLocal()
    try:
        db.query(Camera).delete()
        db.commit()
    finally:
        db.close()


class TestCameraAPI:
    """Test suite for camera CRUD API endpoints"""

    @patch('app.services.camera_service.cv2.VideoCapture')
    def test_create_camera_rtsp(self, mock_videocapture):
        """POST /cameras should create RTSP camera"""
        # Mock camera service to prevent actual camera connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_videocapture.return_value = mock_cap

        camera_data = {
            "name": "Test Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://192.168.1.50:554/stream1",
            "username": "admin",
            "password": "secret123",
            "frame_rate": 5,
            "is_enabled": False  # Disable to avoid starting thread in test
        }

        response = client.post("/api/v1/cameras", json=camera_data)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Test Camera"
        assert data["type"] == "rtsp"
        assert data["rtsp_url"] == "rtsp://192.168.1.50:554/stream1"
        assert data["username"] == "admin"
        assert "password" not in data  # Password should not be returned
        assert data["frame_rate"] == 5
        assert data["is_enabled"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_camera_usb(self):
        """POST /cameras should create USB camera"""
        camera_data = {
            "name": "Webcam",
            "type": "usb",
            "device_index": 0,
            "frame_rate": 15,
            "is_enabled": False
        }

        response = client.post("/api/v1/cameras", json=camera_data)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Webcam"
        assert data["type"] == "usb"
        assert data["device_index"] == 0
        assert data["frame_rate"] == 15

    def test_create_camera_duplicate_name(self):
        """POST /cameras with duplicate name should return 409"""
        camera_data = {
            "name": "Duplicate Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "is_enabled": False
        }

        # Create first camera
        response1 = client.post("/api/v1/cameras", json=camera_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/v1/cameras", json=camera_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_create_camera_invalid_rtsp_url(self):
        """POST /cameras with invalid RTSP URL should return 422"""
        camera_data = {
            "name": "Invalid Camera",
            "type": "rtsp",
            "rtsp_url": "http://example.com/stream",  # Should be rtsp://
            "is_enabled": False
        }

        response = client.post("/api/v1/cameras", json=camera_data)
        assert response.status_code == 422

    def test_create_camera_missing_rtsp_url(self):
        """POST /cameras for RTSP without URL should return 422"""
        camera_data = {
            "name": "Missing URL Camera",
            "type": "rtsp",
            "is_enabled": False
        }

        response = client.post("/api/v1/cameras", json=camera_data)
        assert response.status_code == 422

    def test_create_camera_missing_device_index(self):
        """POST /cameras for USB without device_index should return 422"""
        camera_data = {
            "name": "Missing Index Camera",
            "type": "usb",
            "is_enabled": False
        }

        response = client.post("/api/v1/cameras", json=camera_data)
        assert response.status_code == 422

    def test_list_cameras_empty(self):
        """GET /cameras should return empty list when no cameras"""
        response = client.get("/api/v1/cameras")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_cameras(self):
        """GET /cameras should return all cameras"""
        # Create test cameras
        camera1_data = {
            "name": "Camera 1",
            "type": "rtsp",
            "rtsp_url": "rtsp://example1.com/stream",
            "is_enabled": False
        }
        camera2_data = {
            "name": "Camera 2",
            "type": "usb",
            "device_index": 0,
            "is_enabled": False
        }

        client.post("/api/v1/cameras", json=camera1_data)
        client.post("/api/v1/cameras", json=camera2_data)

        # List cameras
        response = client.get("/api/v1/cameras")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Camera 1"
        assert data[1]["name"] == "Camera 2"

    def test_list_cameras_filter_by_enabled(self):
        """GET /cameras with is_enabled filter should work"""
        # Create cameras with different enabled status
        client.post("/api/v1/cameras", json={
            "name": "Enabled Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "is_enabled": True
        })
        client.post("/api/v1/cameras", json={
            "name": "Disabled Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example2.com/stream",
            "is_enabled": False
        })

        # Filter by enabled=True
        response = client.get("/api/v1/cameras?is_enabled=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Enabled Camera"

    def test_get_camera_by_id(self):
        """GET /cameras/{id} should return camera details"""
        # Create camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Test Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Get camera
        response = client.get(f"/api/v1/cameras/{camera_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == camera_id
        assert data["name"] == "Test Camera"

    def test_get_camera_not_found(self):
        """GET /cameras/{id} for non-existent camera should return 404"""
        response = client.get("/api/v1/cameras/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_camera(self):
        """PUT /cameras/{id} should update camera"""
        # Create camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Original Name",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "frame_rate": 5,
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Update camera
        update_data = {
            "name": "Updated Name",
            "frame_rate": 10
        }
        response = client.put(f"/api/v1/cameras/{camera_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["frame_rate"] == 10

    def test_update_camera_not_found(self):
        """PUT /cameras/{id} for non-existent camera should return 404"""
        response = client.put("/api/v1/cameras/non-existent-id", json={"name": "Test"})

        assert response.status_code == 404

    def test_delete_camera(self):
        """DELETE /cameras/{id} should delete camera"""
        # Create camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Camera to Delete",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Delete camera
        response = client.delete(f"/api/v1/cameras/{camera_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_response = client.get(f"/api/v1/cameras/{camera_id}")
        assert get_response.status_code == 404

    def test_delete_camera_not_found(self):
        """DELETE /cameras/{id} for non-existent camera should return 404"""
        response = client.delete("/api/v1/cameras/non-existent-id")

        assert response.status_code == 404

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_camera_connection_success(self, mock_videocapture):
        """POST /cameras/{id}/test should test connection and return thumbnail"""
        # Create camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Test Connection Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "username": "admin",
            "password": "password",
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock successful connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True

        # Create fake frame (numpy array)
        import numpy as np
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)

        mock_videocapture.return_value = mock_cap

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successful" in data["message"].lower()
        assert data["thumbnail"] is not None
        assert data["thumbnail"].startswith("data:image/jpeg;base64,")

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_camera_connection_failure(self, mock_videocapture):
        """POST /cameras/{id}/test should handle connection failure"""
        # Create camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Failed Connection Camera",
            "type": "rtsp",
            "rtsp_url": "rtsp://example.com/stream",
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock failed connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower() or "check" in data["message"].lower()

    def test_test_camera_connection_not_found(self):
        """POST /cameras/{id}/test for non-existent camera should return 404"""
        response = client.post("/api/v1/cameras/non-existent-id/test")

        assert response.status_code == 404

    # USB-Specific Test Connection Tests (Story F1.3)

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_usb_camera_connection_success(self, mock_videocapture):
        """POST /cameras/{id}/test should work for USB cameras"""
        # Create USB camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Test USB Camera",
            "type": "usb",
            "device_index": 0,
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock successful USB connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True

        import numpy as np
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)

        mock_videocapture.return_value = mock_cap

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "usb camera connected successfully" in data["message"].lower()
        assert "device 0" in data["message"].lower()
        assert data["thumbnail"] is not None

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_usb_camera_not_found(self, mock_videocapture):
        """POST /cameras/{id}/test should return device not found for USB cameras"""
        # Create USB camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Missing USB Camera",
            "type": "usb",
            "device_index": 99,  # Unlikely to exist
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock device not found
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "usb camera not found" in data["message"].lower()
        assert "device index 99" in data["message"].lower()

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_usb_camera_permission_denied(self, mock_videocapture):
        """POST /cameras/{id}/test should handle permission errors for USB cameras"""
        # Create USB camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Permission Denied USB Camera",
            "type": "usb",
            "device_index": 0,
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock permission denied error
        mock_videocapture.side_effect = Exception("Permission denied")

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "permission denied" in data["message"].lower()
        assert "video" in data["message"].lower()  # Should mention video group

    @patch('app.api.v1.cameras.cv2.VideoCapture')
    def test_test_usb_camera_already_in_use(self, mock_videocapture):
        """POST /cameras/{id}/test should handle device busy errors for USB cameras"""
        # Create USB camera
        create_response = client.post("/api/v1/cameras", json={
            "name": "Busy USB Camera",
            "type": "usb",
            "device_index": 0,
            "is_enabled": False
        })
        camera_id = create_response.json()["id"]

        # Mock device busy error
        mock_videocapture.side_effect = Exception("Device is busy or in use")

        # Test connection
        response = client.post(f"/api/v1/cameras/{camera_id}/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "in use" in data["message"].lower()
        assert "another application" in data["message"].lower()
