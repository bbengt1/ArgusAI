"""
API tests for Pattern Detection endpoints (Story P4-3.5)

Tests:
- AC10: GET /api/v1/context/patterns/{camera_id} returns pattern data
- AC11: Response includes all required fields
- AC14: Insufficient data flag for new cameras
"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.context import router
from app.services.pattern_service import PatternData, reset_pattern_service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_pattern_service():
    """Create mock PatternService."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_camera():
    """Create a mock camera."""
    camera = MagicMock()
    camera.id = "test-camera-123"
    camera.name = "Test Camera"
    return camera


@pytest.fixture
def app_factory():
    """Factory to create FastAPI test app with configurable mocks."""
    def _create_app(mock_db, mock_pattern_service, camera_exists=True):
        reset_pattern_service()

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1")

        def override_get_db():
            if camera_exists:
                mock_camera = MagicMock()
                mock_camera.id = "test-camera-123"
                mock_camera.name = "Test Camera"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_camera
            else:
                mock_db.query.return_value.filter.return_value.first.return_value = None
            yield mock_db

        def override_get_pattern_service():
            return mock_pattern_service

        from app.core.database import get_db
        from app.services.pattern_service import get_pattern_service

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.dependency_overrides[get_pattern_service] = override_get_pattern_service

        return test_app

    yield _create_app
    reset_pattern_service()


@pytest.fixture
def app(app_factory, mock_db, mock_pattern_service, mock_camera):
    """Create FastAPI test app with camera exists by default."""
    return app_factory(mock_db, mock_pattern_service, camera_exists=True)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetCameraPatterns:
    """Tests for GET /api/v1/context/patterns/{camera_id} endpoint."""

    def test_get_patterns_success(self, client, mock_pattern_service):
        """AC10, AC11: Test successful pattern retrieval with all required fields."""
        # Mock pattern data
        pattern_data = PatternData(
            camera_id="test-camera-123",
            hourly_distribution={str(h).zfill(2): h * 2 for h in range(24)},
            daily_distribution={str(d): d * 10 for d in range(7)},
            peak_hours=["09", "14", "17"],
            quiet_hours=["02", "03", "04", "05"],
            average_events_per_day=8.5,
            last_calculated_at=datetime(2025, 12, 11, 10, 0, tzinfo=timezone.utc),
            calculation_window_days=30,
            insufficient_data=False,
        )

        async def mock_get_patterns(*args, **kwargs):
            return pattern_data

        mock_pattern_service.get_patterns = mock_get_patterns

        response = client.get("/api/v1/context/patterns/test-camera-123")

        assert response.status_code == 200
        data = response.json()

        # AC11: Verify all required fields are present
        assert "camera_id" in data
        assert "hourly_distribution" in data
        assert "daily_distribution" in data
        assert "peak_hours" in data
        assert "quiet_hours" in data
        assert "average_events_per_day" in data
        assert "last_calculated_at" in data
        assert "calculation_window_days" in data
        assert "insufficient_data" in data

        # Verify values
        assert data["camera_id"] == "test-camera-123"
        assert len(data["hourly_distribution"]) == 24
        assert len(data["daily_distribution"]) == 7
        assert data["peak_hours"] == ["09", "14", "17"]
        assert data["quiet_hours"] == ["02", "03", "04", "05"]
        assert data["average_events_per_day"] == 8.5
        assert data["calculation_window_days"] == 30
        assert data["insufficient_data"] is False

    def test_get_patterns_camera_not_found(self, app_factory, mock_db, mock_pattern_service):
        """Test 404 when camera doesn't exist."""
        # Create app with camera_exists=False
        app = app_factory(mock_db, mock_pattern_service, camera_exists=False)
        client = TestClient(app)

        response = client.get("/api/v1/context/patterns/nonexistent-camera")

        assert response.status_code == 404
        assert "Camera not found" in response.json()["detail"]

    def test_get_patterns_insufficient_data(self, client, mock_pattern_service):
        """AC14: Test response when camera has insufficient history."""
        async def mock_get_patterns(*args, **kwargs):
            return None

        mock_pattern_service.get_patterns = mock_get_patterns

        response = client.get("/api/v1/context/patterns/test-camera-123")

        assert response.status_code == 404
        assert "No activity patterns available" in response.json()["detail"]


class TestRecalculateCameraPatterns:
    """Tests for POST /api/v1/context/patterns/{camera_id}/recalculate endpoint."""

    def test_recalculate_success(self, client, mock_pattern_service):
        """AC15: Test successful pattern recalculation."""
        mock_pattern = MagicMock()
        mock_pattern.id = "pattern-123"

        async def mock_recalculate(*args, **kwargs):
            return mock_pattern

        mock_pattern_service.recalculate_patterns = mock_recalculate

        response = client.post("/api/v1/context/patterns/test-camera-123/recalculate?window_days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["camera_id"] == "test-camera-123"
        assert data["success"] is True
        assert "30-day window" in data["message"]
        assert data["insufficient_data"] is False

    def test_recalculate_insufficient_data(self, client, mock_pattern_service):
        """Test recalculation with insufficient data."""
        async def mock_recalculate(*args, **kwargs):
            return None

        mock_pattern_service.recalculate_patterns = mock_recalculate

        response = client.post("/api/v1/context/patterns/test-camera-123/recalculate")

        assert response.status_code == 200
        data = response.json()
        assert data["camera_id"] == "test-camera-123"
        assert data["success"] is False
        assert data["insufficient_data"] is True

    def test_recalculate_camera_not_found(self, app_factory, mock_db, mock_pattern_service):
        """Test 404 when camera doesn't exist."""
        # Create app with camera_exists=False
        app = app_factory(mock_db, mock_pattern_service, camera_exists=False)
        client = TestClient(app)

        response = client.post("/api/v1/context/patterns/nonexistent-camera/recalculate")

        assert response.status_code == 404

    def test_recalculate_invalid_window_days_too_small(self, client, mock_pattern_service):
        """Test validation rejects window_days less than 7."""
        response = client.post("/api/v1/context/patterns/test-camera-123/recalculate?window_days=3")
        assert response.status_code == 422

    def test_recalculate_invalid_window_days_too_large(self, client, mock_pattern_service):
        """Test validation rejects window_days greater than 365."""
        response = client.post("/api/v1/context/patterns/test-camera-123/recalculate?window_days=500")
        assert response.status_code == 422


class TestBatchRecalculatePatterns:
    """Tests for POST /api/v1/context/patterns/batch endpoint."""

    def test_batch_recalculate_success(self, client, mock_pattern_service):
        """AC9: Test batch pattern recalculation."""
        async def mock_recalculate_all(*args, **kwargs):
            return {
                "total_cameras": 5,
                "patterns_calculated": 3,
                "patterns_skipped": 2,
                "elapsed_ms": 150.5,
            }

        mock_pattern_service.recalculate_all_patterns = mock_recalculate_all

        response = client.post("/api/v1/context/patterns/batch?window_days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total_cameras"] == 5
        assert data["patterns_calculated"] == 3
        assert data["patterns_skipped"] == 2
        assert data["elapsed_ms"] == 150.5

    def test_batch_recalculate_invalid_window_days_too_small(self, client, mock_pattern_service):
        """Test validation rejects window_days less than 7."""
        response = client.post("/api/v1/context/patterns/batch?window_days=5")
        assert response.status_code == 422

    def test_batch_recalculate_invalid_window_days_too_large(self, client, mock_pattern_service):
        """Test validation rejects window_days greater than 365."""
        response = client.post("/api/v1/context/patterns/batch?window_days=400")
        assert response.status_code == 422
