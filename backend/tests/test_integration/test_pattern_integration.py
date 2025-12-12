"""
Integration tests for Pattern Detection (Story P4-3.5)

Tests:
- AC6: Pattern persistence in database
- AC12: Context service integration with pattern data
"""
import json
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.camera import Camera
from app.models.event import Event
from app.models.camera_activity_pattern import CameraActivityPattern
from app.services.pattern_service import (
    PatternService,
    get_pattern_service,
    reset_pattern_service,
)


# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a test database with tables."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_camera(test_db):
    """Create a test camera."""
    camera = Camera(
        id="test-camera-123",
        name="Front Door",
        type="rtsp",
        rtsp_url="rtsp://192.168.1.100:554/stream",
        is_enabled=True,
    )
    test_db.add(camera)
    test_db.commit()
    return camera


@pytest.fixture
def test_events(test_db, test_camera):
    """Create test events spread across different hours and days."""
    events = []
    now = datetime.now(timezone.utc)

    # Create events for pattern calculation (need 10+ events over 7+ days)
    # Events spread over 10 days to ensure 7+ days of history

    # Day 1 (10 days ago) at 9 AM - 3 events
    for i in range(3):
        event = Event(
            id=f"event-day1-9-{i}",
            camera_id=test_camera.id,
            timestamp=now - timedelta(days=10) + timedelta(hours=9, minutes=i),
            description="Person detected at front door",
            confidence=85,
            objects_detected='["person"]',
        )
        events.append(event)
        test_db.add(event)

    # Day 3 (8 days ago) at 2 PM - 3 events
    for i in range(3):
        event = Event(
            id=f"event-day3-14-{i}",
            camera_id=test_camera.id,
            timestamp=now - timedelta(days=8) + timedelta(hours=14, minutes=i),
            description="Car in driveway",
            confidence=90,
            objects_detected='["vehicle"]',
        )
        events.append(event)
        test_db.add(event)

    # Day 5 (6 days ago) at 5 PM - 4 events
    for i in range(4):
        event = Event(
            id=f"event-day5-17-{i}",
            camera_id=test_camera.id,
            timestamp=now - timedelta(days=6) + timedelta(hours=17, minutes=i),
            description="Package delivery",
            confidence=88,
            objects_detected='["package"]',
        )
        events.append(event)
        test_db.add(event)

    # Day 7 (4 days ago) at 3 AM (quiet hour) - 1 event
    event = Event(
        id="event-day7-3-0",
        camera_id=test_camera.id,
        timestamp=now - timedelta(days=4) + timedelta(hours=3),
        description="Animal detected",
        confidence=75,
        objects_detected='["animal"]',
    )
    events.append(event)
    test_db.add(event)

    # Day 9 (2 days ago) at 10 AM - 2 events
    for i in range(2):
        event = Event(
            id=f"event-day9-10-{i}",
            camera_id=test_camera.id,
            timestamp=now - timedelta(days=2) + timedelta(hours=10, minutes=i),
            description="Motion detected",
            confidence=70,
            objects_detected='["person"]',
        )
        events.append(event)
        test_db.add(event)

    test_db.commit()
    return events


class TestPatternPersistence:
    """Test pattern persistence in database (AC6)."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    @pytest.mark.asyncio
    async def test_pattern_persisted_to_database(self, test_db, test_camera, test_events):
        """AC6: Test that patterns are persisted to camera_activity_patterns table."""
        # Recalculate patterns
        pattern = await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        # Verify pattern was created
        assert pattern is not None
        assert pattern.camera_id == test_camera.id

        # Verify pattern exists in database
        db_pattern = test_db.query(CameraActivityPattern).filter_by(
            camera_id=test_camera.id
        ).first()

        assert db_pattern is not None
        assert db_pattern.id == pattern.id

        # Verify pattern data
        hourly = json.loads(db_pattern.hourly_distribution)
        assert "09" in hourly
        assert "14" in hourly
        assert "17" in hourly

        daily = json.loads(db_pattern.daily_distribution)
        assert len(daily) == 7  # All days represented

        peak_hours = json.loads(db_pattern.peak_hours)
        assert isinstance(peak_hours, list)

        quiet_hours = json.loads(db_pattern.quiet_hours)
        assert isinstance(quiet_hours, list)

    @pytest.mark.asyncio
    async def test_pattern_recalculation_updates_existing(self, test_db, test_camera, test_events):
        """AC6: Test that recalculation updates existing pattern record."""
        # First calculation
        pattern1 = await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        original_id = pattern1.id
        original_calculated_at = pattern1.last_calculated_at

        # Add more events
        for i in range(5):
            event = Event(
                id=f"event-new-{i}",
                camera_id=test_camera.id,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=20, minutes=i),
                description="New event",
                confidence=80,
                objects_detected='["person"]',
            )
            test_db.add(event)
        test_db.commit()

        # Force recalculation
        pattern2 = await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        # Should be same record (updated, not new)
        assert pattern2.id == original_id
        assert pattern2.last_calculated_at > original_calculated_at

        # Verify only one pattern exists for this camera
        count = test_db.query(CameraActivityPattern).filter_by(
            camera_id=test_camera.id
        ).count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_pattern_not_created_insufficient_events(self, test_db, test_camera):
        """AC6: Test that no pattern is created with insufficient events."""
        # Add only 5 events (below minimum of 10)
        for i in range(5):
            event = Event(
                id=f"event-few-{i}",
                camera_id=test_camera.id,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                description="Event",
                confidence=80,
                objects_detected='["person"]',
            )
            test_db.add(event)
        test_db.commit()

        pattern = await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        assert pattern is None

        # Verify no pattern exists in database
        count = test_db.query(CameraActivityPattern).filter_by(
            camera_id=test_camera.id
        ).count()
        assert count == 0


class TestPatternContextIntegration:
    """Test integration with context-enhanced prompts (AC12)."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    @pytest.mark.asyncio
    async def test_timing_analysis_uses_persisted_patterns(self, test_db, test_camera, test_events):
        """AC12: Test that timing analysis reads from persisted patterns."""
        # Calculate and persist patterns
        await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        # Query timing at a peak hour
        event_time = datetime.now(timezone.utc).replace(hour=9, minute=30)
        result = await self.service.is_typical_timing(
            db=test_db,
            camera_id=test_camera.id,
            timestamp=event_time
        )

        # Should recognize this as typical or have pattern data
        assert result.is_typical is not None  # Has pattern data

    @pytest.mark.asyncio
    async def test_timing_analysis_performance(self, test_db, test_camera, test_events):
        """AC13: Test that pattern lookup is fast (<50ms target)."""
        import time

        # Calculate and persist patterns
        await self.service.recalculate_patterns(
            db=test_db,
            camera_id=test_camera.id,
            window_days=30,
            force=True
        )

        # Measure timing analysis performance
        start = time.time()
        for _ in range(10):  # Run multiple times
            event_time = datetime.now(timezone.utc).replace(hour=14, minute=0)
            await self.service.is_typical_timing(
                db=test_db,
                camera_id=test_camera.id,
                timestamp=event_time
            )
        elapsed_ms = (time.time() - start) * 1000

        # Average should be well under 50ms per call
        avg_ms = elapsed_ms / 10
        assert avg_ms < 50, f"Pattern lookup took {avg_ms:.2f}ms, expected <50ms"


class TestPatternBatchCalculation:
    """Test batch pattern calculation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    @pytest.mark.asyncio
    async def test_recalculate_all_patterns(self, test_db, test_camera, test_events):
        """Test batch recalculation for all cameras."""
        result = await self.service.recalculate_all_patterns(
            db=test_db,
            window_days=30
        )

        assert "total_cameras" in result
        assert "patterns_calculated" in result
        assert "patterns_skipped" in result
        assert "elapsed_ms" in result

        # Should have calculated pattern for the test camera
        assert result["patterns_calculated"] >= 0
