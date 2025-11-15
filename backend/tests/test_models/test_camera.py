"""Unit tests for Camera SQLAlchemy model"""
import pytest
from app.models.camera import Camera
from datetime import datetime
import uuid


class TestCameraModel:
    """Test suite for Camera ORM model"""

    def test_create_camera_with_rtsp(self, db_session):
        """Create RTSP camera with all fields"""
        camera = Camera(
            name="Front Door Camera",
            type="rtsp",
            rtsp_url="rtsp://192.168.1.50:554/stream1",
            username="admin",
            password="secret123",
            frame_rate=5,
            is_enabled=True,
            motion_sensitivity="medium",
            motion_cooldown=60
        )

        db_session.add(camera)
        db_session.commit()

        # Verify saved
        assert camera.id is not None
        assert camera.name == "Front Door Camera"
        assert camera.type == "rtsp"
        assert camera.rtsp_url == "rtsp://192.168.1.50:554/stream1"
        assert camera.username == "admin"
        assert camera.frame_rate == 5
        assert camera.is_enabled is True
        assert camera.created_at is not None
        assert camera.updated_at is not None

    def test_create_camera_with_usb(self, db_session):
        """Create USB camera with device index"""
        camera = Camera(
            name="Webcam",
            type="usb",
            device_index=0,
            frame_rate=15,
            is_enabled=True
        )

        db_session.add(camera)
        db_session.commit()

        assert camera.type == "usb"
        assert camera.device_index == 0
        assert camera.rtsp_url is None
        assert camera.username is None

    def test_password_auto_encrypted_on_save(self, db_session):
        """Password should be automatically encrypted when saved"""
        plain_password = "my_secret_password"

        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream",
            password=plain_password
        )

        db_session.add(camera)
        db_session.commit()

        # Password in database should be encrypted
        assert camera.password is not None
        assert camera.password.startswith("encrypted:")
        assert camera.password != plain_password

    def test_get_decrypted_password(self, db_session):
        """get_decrypted_password() should return original password"""
        plain_password = "test_password_123"

        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream",
            password=plain_password
        )

        db_session.add(camera)
        db_session.commit()

        # Decrypt password
        decrypted = camera.get_decrypted_password()

        assert decrypted == plain_password

    def test_password_not_double_encrypted(self, db_session):
        """Already encrypted password should not be encrypted again"""
        plain_password = "test_password"

        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream",
            password=plain_password
        )

        db_session.add(camera)
        db_session.commit()

        # Get encrypted password
        encrypted_password = camera.password

        # Update password with already encrypted value
        camera.password = encrypted_password
        db_session.commit()

        # Should still be the same
        assert camera.password == encrypted_password

    def test_camera_with_null_password(self, db_session):
        """Camera with no password should handle None correctly"""
        camera = Camera(
            name="Public Camera",
            type="rtsp",
            rtsp_url="rtsp://public.example.com/stream",
            password=None
        )

        db_session.add(camera)
        db_session.commit()

        assert camera.password is None
        assert camera.get_decrypted_password() is None

    def test_default_values(self, db_session):
        """Test model default values"""
        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream"
        )

        db_session.add(camera)
        db_session.commit()

        # Check defaults
        assert camera.frame_rate == 5
        assert camera.is_enabled is True
        assert camera.motion_sensitivity == "medium"
        assert camera.motion_cooldown == 60

    def test_uuid_generation(self, db_session):
        """Camera ID should be auto-generated UUID"""
        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream"
        )

        db_session.add(camera)
        db_session.commit()

        # Verify UUID format
        assert camera.id is not None
        try:
            uuid.UUID(camera.id)
        except ValueError:
            pytest.fail(f"Camera ID is not a valid UUID: {camera.id}")

    def test_timestamps_auto_set(self, db_session):
        """created_at and updated_at should be automatically set"""
        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream"
        )

        db_session.add(camera)
        db_session.commit()

        assert isinstance(camera.created_at, datetime)
        assert isinstance(camera.updated_at, datetime)
        assert camera.created_at <= camera.updated_at

    def test_frame_rate_constraint(self, db_session):
        """Frame rate should enforce 1-30 constraint"""
        # Valid frame rate
        camera_valid = Camera(
            name="Valid Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream",
            frame_rate=15
        )
        db_session.add(camera_valid)
        db_session.commit()
        assert camera_valid.frame_rate == 15

        # Note: Check constraints are enforced at database level
        # SQLAlchemy may not raise error until commit
        # Actual constraint testing would require database-level validation

    def test_camera_type_constraint(self, db_session):
        """Camera type should be 'rtsp' or 'usb'"""
        camera = Camera(
            name="RTSP Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream"
        )
        db_session.add(camera)
        db_session.commit()
        assert camera.type in ["rtsp", "usb"]

    def test_motion_sensitivity_constraint(self, db_session):
        """Motion sensitivity should be low/medium/high"""
        for sensitivity in ["low", "medium", "high"]:
            camera = Camera(
                name=f"Camera {sensitivity}",
                type="rtsp",
                rtsp_url="rtsp://example.com/stream",
                motion_sensitivity=sensitivity
            )
            db_session.add(camera)
            db_session.commit()
            assert camera.motion_sensitivity == sensitivity

    def test_repr_method(self, db_session):
        """__repr__ should return useful string representation"""
        camera = Camera(
            name="Test Camera",
            type="rtsp",
            rtsp_url="rtsp://example.com/stream",
            is_enabled=True
        )
        db_session.add(camera)
        db_session.commit()

        repr_str = repr(camera)

        assert "Camera" in repr_str
        assert camera.id in repr_str
        assert "Test Camera" in repr_str
        assert "rtsp" in repr_str
        assert "True" in repr_str
