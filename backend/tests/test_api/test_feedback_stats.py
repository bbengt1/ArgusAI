"""
Tests for Feedback Statistics API endpoints (Story P4-5.2)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timezone, timedelta

from main import app
from app.core.database import Base, get_db
# Import all models to ensure they are registered with Base.metadata
from app.models import *  # noqa: F401, F403
from app.models.event import Event
from app.models.event_feedback import EventFeedback
from app.models.camera import Camera


# Test database setup
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override dependency to use test database"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create and tear down test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with dependency override"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(test_db):
    """Get database session for test setup"""
    return TestingSessionLocal()


@pytest.fixture
def test_camera(db_session) -> Camera:
    """Create a test camera"""
    camera = Camera(
        id=str(uuid.uuid4()),
        name="Test Camera 1",
        type="rtsp",
        rtsp_url="rtsp://test:test@localhost:554/stream1",
        is_enabled=True,
        source_type="rtsp"
    )
    db_session.add(camera)
    db_session.commit()
    db_session.refresh(camera)
    return camera


@pytest.fixture
def test_camera_2(db_session) -> Camera:
    """Create a second test camera"""
    camera = Camera(
        id=str(uuid.uuid4()),
        name="Test Camera 2",
        type="rtsp",
        rtsp_url="rtsp://test:test@localhost:554/stream2",
        is_enabled=True,
        source_type="rtsp"
    )
    db_session.add(camera)
    db_session.commit()
    db_session.refresh(camera)
    return camera


def create_event(db_session, camera: Camera, timestamp: datetime = None) -> Event:
    """Helper to create an event for testing"""
    event = Event(
        id=str(uuid.uuid4()),
        camera_id=camera.id,
        timestamp=timestamp or datetime.now(timezone.utc),
        description="Test event description",
        confidence=85,
        objects_detected='["person"]',
        alert_triggered=False,
        source_type="rtsp"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def create_feedback(db_session, event: Event, rating: str, correction: str = None) -> EventFeedback:
    """Helper to create feedback for testing"""
    feedback = EventFeedback(
        event_id=event.id,
        camera_id=event.camera_id,  # Story P4-5.2: Include camera_id
        rating=rating,
        correction=correction
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    return feedback


class TestFeedbackStatsEndpoint:
    """Test suite for GET /api/v1/feedback/stats endpoint"""

    def test_get_stats_empty(self, client):
        """Test stats with no feedback data (AC1)"""
        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present (AC1, AC2)
        assert data["total_count"] == 0
        assert data["helpful_count"] == 0
        assert data["not_helpful_count"] == 0
        assert data["accuracy_rate"] == 0.0
        assert data["feedback_by_camera"] == {}
        assert data["daily_trend"] == []
        assert data["top_corrections"] == []

    def test_get_stats_with_feedback(self, client, db_session, test_camera: Camera):
        """Test stats with feedback data (AC1, AC2, AC3)"""
        # Create events and feedback
        for i in range(10):
            event = create_event(db_session, test_camera)
            rating = "helpful" if i < 8 else "not_helpful"  # 80% helpful
            create_feedback(db_session, event, rating)

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 10
        assert data["helpful_count"] == 8
        assert data["not_helpful_count"] == 2
        assert data["accuracy_rate"] == 80.0  # AC3: 8/10 * 100 = 80%

    def test_get_stats_accuracy_calculation(self, client, db_session, test_camera: Camera):
        """Test accuracy rate calculation (AC3)"""
        # Create 5 helpful and 5 not_helpful = 50% accuracy
        for i in range(10):
            event = create_event(db_session, test_camera)
            rating = "helpful" if i < 5 else "not_helpful"
            create_feedback(db_session, event, rating)

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["accuracy_rate"] == 50.0

    def test_get_stats_filter_by_camera(self, client, db_session, test_camera: Camera, test_camera_2: Camera):
        """Test camera_id filter (AC4)"""
        # Create events for both cameras
        event1 = create_event(db_session, test_camera)
        event2 = create_event(db_session, test_camera_2)

        create_feedback(db_session, event1, "helpful")
        create_feedback(db_session, event2, "not_helpful")

        # Filter by camera 1
        response = client.get(f"/api/v1/feedback/stats?camera_id={test_camera.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 1
        assert data["helpful_count"] == 1
        assert data["not_helpful_count"] == 0
        assert data["accuracy_rate"] == 100.0

    def test_get_stats_filter_by_date_range(self, client, db_session, test_camera: Camera):
        """Test date range filters (AC5)"""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        # Create events at different times
        event_now = create_event(db_session, test_camera, now)
        event_yesterday = create_event(db_session, test_camera, yesterday)
        event_week_ago = create_event(db_session, test_camera, week_ago)

        create_feedback(db_session, event_now, "helpful")
        create_feedback(db_session, event_yesterday, "not_helpful")
        create_feedback(db_session, event_week_ago, "helpful")

        # Filter to yesterday only
        start_date = yesterday.strftime("%Y-%m-%d")
        end_date = yesterday.strftime("%Y-%m-%d")

        response = client.get(f"/api/v1/feedback/stats?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 1
        assert data["not_helpful_count"] == 1

    def test_get_stats_per_camera_breakdown(self, client, db_session, test_camera: Camera, test_camera_2: Camera):
        """Test per-camera breakdown (AC8)"""
        # Camera 1: 3 helpful, 1 not_helpful = 75%
        for i in range(4):
            event = create_event(db_session, test_camera)
            rating = "helpful" if i < 3 else "not_helpful"
            create_feedback(db_session, event, rating)

        # Camera 2: 1 helpful, 1 not_helpful = 50%
        for i in range(2):
            event = create_event(db_session, test_camera_2)
            rating = "helpful" if i < 1 else "not_helpful"
            create_feedback(db_session, event, rating)

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert test_camera.id in data["feedback_by_camera"]
        assert test_camera_2.id in data["feedback_by_camera"]

        cam1_stats = data["feedback_by_camera"][test_camera.id]
        assert cam1_stats["camera_id"] == test_camera.id
        assert cam1_stats["camera_name"] == "Test Camera 1"
        assert cam1_stats["helpful_count"] == 3
        assert cam1_stats["not_helpful_count"] == 1
        assert cam1_stats["accuracy_rate"] == 75.0

        cam2_stats = data["feedback_by_camera"][test_camera_2.id]
        assert cam2_stats["accuracy_rate"] == 50.0

    def test_get_stats_daily_trend(self, client, db_session, test_camera: Camera):
        """Test daily trend data (AC9)"""
        now = datetime.now(timezone.utc)

        # Create feedback for today
        for i in range(3):
            event = create_event(db_session, test_camera, now)
            rating = "helpful" if i < 2 else "not_helpful"
            create_feedback(db_session, event, rating)

        # Create feedback for yesterday
        yesterday = now - timedelta(days=1)
        for i in range(2):
            event = create_event(db_session, test_camera, yesterday)
            rating = "helpful"
            create_feedback(db_session, event, rating)

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert len(data["daily_trend"]) >= 2

        # Check that dates are included in trend
        dates = [item["date"] for item in data["daily_trend"]]
        assert now.strftime("%Y-%m-%d") in dates or yesterday.strftime("%Y-%m-%d") in dates

    def test_get_stats_top_corrections(self, client, db_session, test_camera: Camera):
        """Test top corrections aggregation (AC10)"""
        # Create multiple events with same correction
        correction_1 = "This was a delivery driver"
        correction_2 = "Wrong person detected"

        for i in range(5):
            event = create_event(db_session, test_camera)
            create_feedback(db_session, event, "not_helpful", correction_1)

        for i in range(3):
            event = create_event(db_session, test_camera)
            create_feedback(db_session, event, "not_helpful", correction_2)

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert len(data["top_corrections"]) >= 2

        # First correction should be most common
        assert data["top_corrections"][0]["correction_text"] == correction_1
        assert data["top_corrections"][0]["count"] == 5

        assert data["top_corrections"][1]["correction_text"] == correction_2
        assert data["top_corrections"][1]["count"] == 3

    def test_camera_id_auto_populated_on_create(self, client, db_session, test_camera: Camera):
        """Test camera_id is auto-populated when creating feedback (AC6, AC7)"""
        event = create_event(db_session, test_camera)

        # Create feedback via API
        response = client.post(
            f"/api/v1/events/{event.id}/feedback",
            json={"rating": "helpful"}
        )
        assert response.status_code == 201
        data = response.json()

        # Verify camera_id was populated
        assert data["camera_id"] == test_camera.id

    def test_stats_with_combined_filters(self, client, db_session, test_camera: Camera, test_camera_2: Camera):
        """Test combined camera_id and date range filters"""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        # Camera 1, today: helpful
        event1 = create_event(db_session, test_camera, now)
        create_feedback(db_session, event1, "helpful")

        # Camera 1, yesterday: not_helpful
        event2 = create_event(db_session, test_camera, yesterday)
        create_feedback(db_session, event2, "not_helpful")

        # Camera 2, today: helpful
        event3 = create_event(db_session, test_camera_2, now)
        create_feedback(db_session, event3, "helpful")

        # Filter: camera 1, today only
        today = now.strftime("%Y-%m-%d")
        response = client.get(
            f"/api/v1/feedback/stats?camera_id={test_camera.id}&start_date={today}&end_date={today}"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 1
        assert data["helpful_count"] == 1
        assert data["accuracy_rate"] == 100.0

    def test_stats_response_structure(self, client):
        """Test response contains all required fields with correct types"""
        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert isinstance(data["total_count"], int)
        assert isinstance(data["helpful_count"], int)
        assert isinstance(data["not_helpful_count"], int)
        assert isinstance(data["accuracy_rate"], (int, float))
        assert isinstance(data["feedback_by_camera"], dict)
        assert isinstance(data["daily_trend"], list)
        assert isinstance(data["top_corrections"], list)

    def test_top_corrections_limit(self, client, db_session, test_camera: Camera):
        """Test top corrections is limited to 10 entries"""
        # Create 15 different corrections
        for i in range(15):
            event = create_event(db_session, test_camera)
            create_feedback(db_session, event, "not_helpful", f"Correction {i}")

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        # Should be capped at 10
        assert len(data["top_corrections"]) <= 10

    def test_feedback_without_correction_excluded_from_top_corrections(self, client, db_session, test_camera: Camera):
        """Test that feedback without corrections doesn't appear in top_corrections"""
        # Create feedback without correction
        event1 = create_event(db_session, test_camera)
        create_feedback(db_session, event1, "not_helpful", None)

        # Create feedback with correction
        event2 = create_event(db_session, test_camera)
        create_feedback(db_session, event2, "not_helpful", "Has correction")

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        # Only one entry with correction
        assert len(data["top_corrections"]) == 1
        assert data["top_corrections"][0]["correction_text"] == "Has correction"

    def test_helpful_feedback_without_corrections(self, client, db_session, test_camera: Camera):
        """Test that helpful feedback (which typically has no correction) doesn't pollute top_corrections"""
        # Create helpful feedback (no correction needed)
        for i in range(5):
            event = create_event(db_session, test_camera)
            create_feedback(db_session, event, "helpful")

        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 5
        assert data["helpful_count"] == 5
        assert data["accuracy_rate"] == 100.0
        assert data["top_corrections"] == []
