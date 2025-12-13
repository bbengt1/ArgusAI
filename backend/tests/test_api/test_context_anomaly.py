"""
API Tests for anomaly scoring endpoints (Story P4-7.2)

Tests cover:
- GET /api/v1/context/anomaly/score/{event_id} - Score existing event
- POST /api/v1/context/anomaly/score - Ad-hoc scoring
- Error handling (404, 500)
"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.context import router
from app.services.anomaly_scoring_service import AnomalyScoreResult, reset_anomaly_scoring_service
from app.services.pattern_service import PatternData, reset_pattern_service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_anomaly_service():
    """Create mock AnomalyScoringService."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_pattern_service():
    """Create mock PatternService."""
    service = MagicMock()
    return service


@pytest.fixture
def app_factory():
    """Factory to create FastAPI test app with configurable mocks."""
    def _create_app(
        mock_db,
        mock_anomaly_service,
        mock_pattern_service,
        event_exists=True,
        camera_exists=True,
    ):
        reset_anomaly_scoring_service()
        reset_pattern_service()

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1")

        def override_get_db():
            # Configure mock for event queries
            if event_exists:
                mock_event = MagicMock()
                mock_event.id = "event-test-1"
                mock_event.camera_id = "cam-test-1"
                mock_event.timestamp = datetime.now(timezone.utc)
                mock_event.objects_detected = json.dumps(["person"])
                mock_db.query.return_value.filter.return_value.first.return_value = mock_event
            elif camera_exists:
                mock_camera = MagicMock()
                mock_camera.id = "cam-test-1"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_camera
            else:
                mock_db.query.return_value.filter.return_value.first.return_value = None
            yield mock_db

        def override_get_anomaly_service():
            return mock_anomaly_service

        def override_get_pattern_service():
            return mock_pattern_service

        from app.core.database import get_db
        from app.services.anomaly_scoring_service import get_anomaly_scoring_service
        from app.services.pattern_service import get_pattern_service

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.dependency_overrides[get_anomaly_scoring_service] = override_get_anomaly_service
        test_app.dependency_overrides[get_pattern_service] = override_get_pattern_service

        return test_app

    yield _create_app
    reset_anomaly_scoring_service()
    reset_pattern_service()


class TestScoreEventEndpoint:
    """Tests for GET /api/v1/context/anomaly/score/{event_id}."""

    def test_score_event_success(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should score existing event and return detailed breakdown."""
        # Configure mock
        mock_anomaly_service.score_event = AsyncMock(return_value=AnomalyScoreResult(
            total=0.35,
            timing_score=0.2,
            day_score=0.1,
            object_score=0.5,
            severity="medium",
            has_baseline=True,
        ))

        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=True
        )
        client = TestClient(app)

        response = client.get("/api/v1/context/anomaly/score/event-test-1")

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "event-test-1"
        assert data["total_score"] == 0.35
        assert data["timing_score"] == 0.2
        assert data["day_score"] == 0.1
        assert data["object_score"] == 0.5
        assert data["severity"] == "medium"
        assert data["has_baseline"] is True

    def test_score_event_not_found(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should return 404 for non-existent event."""
        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=False, camera_exists=False
        )
        client = TestClient(app)

        response = client.get("/api/v1/context/anomaly/score/nonexistent-event")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_score_event_scoring_failure(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should return 500 if scoring fails."""
        # Configure mock to return None (failure)
        mock_anomaly_service.score_event = AsyncMock(return_value=None)

        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=True
        )
        client = TestClient(app)

        response = client.get("/api/v1/context/anomaly/score/event-test-1")

        assert response.status_code == 500
        assert "Failed to calculate" in response.json()["detail"]


class TestCalculateAnomalyScoreEndpoint:
    """Tests for POST /api/v1/context/anomaly/score."""

    def test_calculate_score_success(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should calculate score for ad-hoc data."""
        # Configure mocks
        mock_pattern_service.get_patterns = AsyncMock(return_value=PatternData(
            camera_id="cam-test-1",
            hourly_distribution={"12": 10},
            daily_distribution={"0": 20},
            peak_hours=["12"],
            quiet_hours=["03"],
            average_events_per_day=10.0,
            last_calculated_at=datetime.now(timezone.utc),
            calculation_window_days=30,
            insufficient_data=False,
            object_type_distribution={"person": 100},
            dominant_object_type="person",
        ))

        mock_anomaly_service.calculate_anomaly_score = AsyncMock(
            return_value=AnomalyScoreResult(
                total=0.15,
                timing_score=0.1,
                day_score=0.05,
                object_score=0.2,
                severity="low",
                has_baseline=True,
            )
        )

        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=False, camera_exists=True
        )
        client = TestClient(app)

        response = client.post(
            "/api/v1/context/anomaly/score",
            json={
                "camera_id": "cam-test-1",
                "timestamp": "2024-01-15T12:00:00Z",
                "objects_detected": ["person"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] is None  # No event for ad-hoc
        assert data["total_score"] == 0.15
        assert data["severity"] == "low"
        assert data["has_baseline"] is True

    def test_calculate_score_camera_not_found(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should return 404 for non-existent camera."""
        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=False, camera_exists=False
        )
        client = TestClient(app)

        response = client.post(
            "/api/v1/context/anomaly/score",
            json={
                "camera_id": "nonexistent-camera",
                "timestamp": "2024-01-15T12:00:00Z",
                "objects_detected": ["person"],
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_calculate_score_no_baseline(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should return neutral score when no baseline exists."""
        # Configure mocks - no patterns available
        mock_pattern_service.get_patterns = AsyncMock(return_value=None)
        mock_anomaly_service.calculate_anomaly_score = AsyncMock(
            return_value=AnomalyScoreResult(
                total=0.0,
                timing_score=0.0,
                day_score=0.0,
                object_score=0.0,
                severity="low",
                has_baseline=False,
            )
        )

        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=False, camera_exists=True
        )
        client = TestClient(app)

        response = client.post(
            "/api/v1/context/anomaly/score",
            json={
                "camera_id": "cam-test-1",
                "timestamp": "2024-01-15T12:00:00Z",
                "objects_detected": ["person"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_score"] == 0.0
        assert data["has_baseline"] is False

    def test_calculate_score_validation_error(self, app_factory, mock_db, mock_anomaly_service, mock_pattern_service):
        """Should return 422 for invalid request body."""
        app = app_factory(
            mock_db, mock_anomaly_service, mock_pattern_service,
            event_exists=False, camera_exists=True
        )
        client = TestClient(app)

        response = client.post(
            "/api/v1/context/anomaly/score",
            json={
                # Missing required camera_id and timestamp
                "objects_detected": ["person"],
            },
        )

        assert response.status_code == 422
