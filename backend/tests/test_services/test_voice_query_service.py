"""
Unit tests for Voice Query Service (Story P4-6.3)

Tests cover:
- Time expression parsing
- Camera name matching
- Response generation
- Edge cases and ambiguous queries
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from app.services.voice_query_service import (
    VoiceQueryService,
    TimeRange,
    ParsedQuery,
    QueryResult,
    get_voice_query_service,
)


@dataclass
class MockCamera:
    """Mock camera for testing."""
    id: str
    name: str
    is_enabled: bool = True


@dataclass
class MockEvent:
    """Mock event for testing."""
    id: str
    camera_id: str
    timestamp: datetime
    description: str
    objects_detected: str  # JSON string


class TestTimeExpressionParsing:
    """Tests for time expression parsing (AC2)"""

    @pytest.fixture
    def service(self):
        return VoiceQueryService()

    def test_parse_today(self, service):
        """Parse 'today' to since midnight."""
        result = service._parse_time_expression("what happened today")
        assert result.description == "today"
        assert result.start.hour == 0
        assert result.start.minute == 0

    def test_parse_yesterday(self, service):
        """Parse 'yesterday' to previous day."""
        result = service._parse_time_expression("any activity yesterday")
        assert result.description == "yesterday"
        # Should be previous day
        now = datetime.now(timezone.utc)
        expected_date = (now - timedelta(days=1)).date()
        assert result.start.date() == expected_date

    def test_parse_this_morning(self, service):
        """Parse 'this morning' to 6 AM - 12 PM."""
        result = service._parse_time_expression("what happened this morning")
        assert result.description == "this morning"
        assert result.start.hour == 6

    def test_parse_this_afternoon(self, service):
        """Parse 'this afternoon' to 12 PM - 6 PM."""
        result = service._parse_time_expression("any activity this afternoon")
        assert result.description == "this afternoon"
        assert result.start.hour == 12

    def test_parse_this_evening(self, service):
        """Parse 'this evening' to 6 PM - 10 PM."""
        result = service._parse_time_expression("what's happening this evening")
        assert result.description == "this evening"
        assert result.start.hour == 18

    def test_parse_tonight(self, service):
        """Parse 'tonight' to 6 PM - midnight."""
        result = service._parse_time_expression("anything tonight")
        assert result.description == "tonight"
        assert result.start.hour == 18

    def test_parse_last_hour(self, service):
        """Parse 'last hour' to past 60 minutes."""
        result = service._parse_time_expression("what happened in the last hour")
        assert result.description == "the last hour"
        now = datetime.now(timezone.utc)
        assert (now - result.start).total_seconds() < 3700  # ~1 hour with buffer

    def test_parse_last_n_hours(self, service):
        """Parse 'last 3 hours' to past N hours."""
        result = service._parse_time_expression("activity in the last 3 hours")
        assert "3 hours" in result.description
        now = datetime.now(timezone.utc)
        diff = now - result.start
        assert 2.9 < diff.total_seconds() / 3600 < 3.1  # ~3 hours

    def test_parse_last_n_minutes(self, service):
        """Parse 'last 30 minutes' to past N minutes."""
        result = service._parse_time_expression("what happened in the last 30 minutes")
        assert "30 minute" in result.description
        now = datetime.now(timezone.utc)
        diff = now - result.start
        assert 29 < diff.total_seconds() / 60 < 31  # ~30 minutes

    def test_parse_recently(self, service):
        """Parse 'recently' to last hour."""
        result = service._parse_time_expression("any activity recently")
        assert result.description == "the last hour"

    def test_parse_default_no_time(self, service):
        """Default to last hour when no time specified."""
        result = service._parse_time_expression("what's at the front door")
        assert result.description == "the last hour"


class TestCameraNameMatching:
    """Tests for camera name matching (AC3)"""

    @pytest.fixture
    def service(self):
        return VoiceQueryService()

    @pytest.fixture
    def cameras(self):
        return [
            MockCamera(id="cam-1", name="Front Door Camera"),
            MockCamera(id="cam-2", name="Back Yard Camera"),
            MockCamera(id="cam-3", name="Garage Camera"),
            MockCamera(id="cam-4", name="Side Entrance"),
        ]

    def test_exact_name_match(self, service, cameras):
        """Match exact camera name."""
        camera_id, camera_name = service._match_camera_name(
            "what's at the front door camera", cameras
        )
        assert camera_id == "cam-1"
        assert camera_name == "Front Door Camera"

    def test_partial_name_match(self, service, cameras):
        """Match partial camera name."""
        camera_id, camera_name = service._match_camera_name(
            "anything at the back yard", cameras
        )
        assert camera_id == "cam-2"
        assert camera_name == "Back Yard Camera"

    def test_synonym_match_front(self, service, cameras):
        """Match using synonym 'front door'."""
        camera_id, camera_name = service._match_camera_name(
            "activity at the front entrance", cameras
        )
        assert camera_id == "cam-1"

    def test_synonym_match_garage(self, service, cameras):
        """Match using synonym 'driveway'."""
        camera_id, camera_name = service._match_camera_name(
            "anyone in the driveway", cameras
        )
        assert camera_id == "cam-3"

    def test_all_cameras_no_filter(self, service, cameras):
        """'all cameras' returns no filter."""
        camera_id, camera_name = service._match_camera_name(
            "what's happening on all cameras", cameras
        )
        assert camera_id is None
        assert camera_name is None

    def test_no_match_returns_none(self, service, cameras):
        """Unknown camera returns None."""
        camera_id, camera_name = service._match_camera_name(
            "what's at the kitchen", cameras
        )
        assert camera_id is None
        assert camera_name is None

    def test_case_insensitive(self, service, cameras):
        """Camera matching is case insensitive."""
        camera_id, camera_name = service._match_camera_name(
            "FRONT DOOR activity", cameras
        )
        assert camera_id == "cam-1"


class TestResponseGeneration:
    """Tests for response generation (AC4)"""

    @pytest.fixture
    def service(self):
        return VoiceQueryService()

    def test_no_events_response(self, service):
        """Generate response for no events."""
        response = service._generate_no_events_response("today", "front door")
        assert "No activity" in response
        assert "front door" in response
        assert "today" in response

    def test_no_events_all_cameras(self, service):
        """Generate response for no events on all cameras."""
        response = service._generate_no_events_response("today", "all cameras")
        assert "No activity" in response
        assert "all cameras" not in response  # Should be simpler

    def test_single_event_response(self, service):
        """Generate response for single event."""
        event = MockEvent(
            id="evt-1",
            camera_id="cam-1",
            timestamp=datetime.now(timezone.utc),
            description="A person was seen at the door",
            objects_detected='["person"]',
        )
        response = service._generate_single_event_response(event, "today", "front door")
        assert "1 event" in response
        assert "person" in response.lower()

    def test_multiple_events_response(self, service):
        """Generate response for multiple events."""
        result = QueryResult(
            events=[],  # Not used directly
            count=5,
            cameras_involved=["Front Door", "Back Yard"],
            objects_detected={"person": 3, "vehicle": 2},
        )
        response = service._generate_multiple_events_response(
            result, "today", "all cameras"
        )
        assert "5 events" in response
        assert "person" in response.lower()
        assert "vehicle" in response.lower()


class TestAmbiguousQueries:
    """Tests for ambiguous query handling (AC5)"""

    @pytest.fixture
    def service(self):
        return VoiceQueryService()

    def test_ambiguous_interesting(self, service):
        """Handle 'anything interesting' query."""
        response = service.handle_ambiguous_query("anything interesting happening?")
        assert "Try asking" in response or "recent activity" in response

    def test_help_query(self, service):
        """Handle help-style queries."""
        response = service.handle_ambiguous_query("what can you tell me")
        assert "ask me" in response.lower() or "try asking" in response.lower()


class TestFullQueryFlow:
    """Integration tests for full query flow"""

    @pytest.fixture
    def service(self):
        return VoiceQueryService()

    @pytest.fixture
    def cameras(self):
        return [
            MockCamera(id="cam-1", name="Front Door Camera"),
            MockCamera(id="cam-2", name="Back Yard Camera"),
        ]

    def test_parse_query_extracts_all_parts(self, service, cameras):
        """Parse query extracts time and camera."""
        parsed = service.parse_query(
            "What happened at the front door today?", cameras
        )
        assert parsed.time_range.description == "today"
        assert parsed.camera_filter == "cam-1"
        assert parsed.camera_name == "Front Door Camera"

    def test_parse_query_default_time(self, service, cameras):
        """Query without time defaults to last hour."""
        parsed = service.parse_query("What's at the back yard?", cameras)
        assert parsed.time_range.description == "the last hour"
        assert parsed.camera_filter == "cam-2"

    def test_generate_full_response(self, service):
        """Generate complete response from parsed query and result."""
        parsed = ParsedQuery(
            original_query="What happened today?",
            time_range=TimeRange(
                start=datetime.now(timezone.utc) - timedelta(hours=12),
                end=datetime.now(timezone.utc),
                description="today",
            ),
            camera_filter=None,
            camera_name=None,
        )
        result = QueryResult(
            events=[],
            count=3,
            cameras_involved=["Front Door"],
            objects_detected={"person": 2, "package": 1},
        )
        response = service.generate_response(parsed, result)
        assert "3 events" in response
        assert "today" in response


class TestServiceSingleton:
    """Test service singleton pattern"""

    def test_get_voice_query_service_returns_same_instance(self):
        """get_voice_query_service returns singleton."""
        service1 = get_voice_query_service()
        service2 = get_voice_query_service()
        assert service1 is service2

    def test_service_instance_type(self):
        """Service instance is VoiceQueryService."""
        service = get_voice_query_service()
        assert isinstance(service, VoiceQueryService)
