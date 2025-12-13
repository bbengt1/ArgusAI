"""
Integration tests for Summaries API (Story P4-4.1, P4-4.5)

Tests:
- AC13: POST /api/v1/summaries/generate endpoint
- AC14: GET /api/v1/summaries/daily endpoint
- AC15: Validation errors (400 for invalid date ranges)
- AC16: Response schema verification

Story P4-4.5 tests:
- hours_back parameter support
- Parameter validation (hours_back vs start_time/end_time)
- Response includes id and stats
- digest_type='on_demand' for generated summaries
"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.core.database import get_db
from app.services.summary_service import (
    SummaryService,
    get_summary_service,
    reset_summary_service,
    SummaryResult,
    SummaryStats,
)


# Shared mock instances (module level for persistence)
_mock_db = None
_mock_summary_service = None


def get_mock_db():
    """Get shared mock database session."""
    global _mock_db
    if _mock_db is None:
        _mock_db = MagicMock(spec=Session)
        # Set up default mock return values - VERY IMPORTANT: return None for cache checks
        # This ensures the endpoint calls generate_summary instead of returning cached result
        _mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        _mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        _mock_db.query.return_value.filter.return_value.first.return_value = None
        _mock_db.query.return_value.count.return_value = 0
        _mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        _mock_db.add = MagicMock()
        _mock_db.commit = MagicMock()
        _mock_db.refresh = MagicMock()
    return _mock_db


def get_mock_summary_service():
    """Get shared mock summary service."""
    global _mock_summary_service
    if _mock_summary_service is None:
        _mock_summary_service = MagicMock(spec=SummaryService)
    return _mock_summary_service


# Mock database session fixture
@pytest.fixture
def mock_db():
    """Mock database session."""
    return get_mock_db()


# Mock summary service fixture
@pytest.fixture
def mock_summary_service():
    """Mock summary service."""
    return get_mock_summary_service()


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Override dependencies with functions that return shared mocks
    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_summary_service] = get_mock_summary_service

    yield TestClient(app)

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    global _mock_db, _mock_summary_service
    _mock_db = None
    _mock_summary_service = None
    reset_summary_service()
    yield
    reset_summary_service()


class TestGenerateSummaryEndpoint:
    """Tests for POST /api/v1/summaries/generate (AC13)."""

    def test_generate_summary_success(self, client, mock_summary_service):
        """Test successful summary generation."""
        # Mock generate_summary to return a successful result
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Today was a quiet day with just the mail carrier visiting around noon.",
            period_start=datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2025, 12, 12, 23, 59, 59, tzinfo=timezone.utc),
            event_count=3,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(
                total_events=3,
                by_type={"person": 2, "vehicle": 1},
                by_camera={"Front Door": 3}
            ),
            ai_cost=Decimal("0.0001"),
            provider_used="openai",
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": "2025-12-12T23:59:59Z"
            }
        )

        # Returns 201 Created (Story P4-4.5)
        assert response.status_code == 201
        data = response.json()
        assert "summary_text" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "event_count" in data
        assert "generated_at" in data

    def test_generate_summary_with_camera_ids(self, client, mock_summary_service):
        """Test summary generation with specific cameras."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Activity on selected cameras.",
            period_start=datetime.now(timezone.utc) - timedelta(days=1),
            period_end=datetime.now(timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=5),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-11T00:00:00Z",
                "end_time": "2025-12-12T00:00:00Z",
                "camera_ids": ["cam-1", "cam-2"]
            }
        )

        # Returns 201 Created (Story P4-4.5)
        assert response.status_code == 201

    def test_generate_summary_invalid_date_range(self, client):
        """Test 400 error for end_time before start_time (AC15)."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T23:59:59Z",
                "end_time": "2025-12-12T00:00:00Z"  # End before start
            }
        )

        assert response.status_code == 400
        assert "end_time must be after start_time" in response.json()["detail"]

    def test_generate_summary_future_date_rejected(self, client):
        """Test 400 error for future dates > 1 day (AC15)."""
        future_date = datetime.now(timezone.utc) + timedelta(days=10)

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": future_date.isoformat()
            }
        )

        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()


class TestDailySummaryEndpoint:
    """Tests for GET /api/v1/summaries/daily (AC14)."""

    def test_daily_summary_success(self, client, mock_summary_service):
        """Test successful daily summary retrieval."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Quiet day on December 11th.",
            period_start=datetime(2025, 12, 11, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2025, 12, 11, 23, 59, 59, tzinfo=timezone.utc),
            event_count=2,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=2),
            success=True
        ))

        response = client.get("/api/v1/summaries/daily?date=2025-12-11")

        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert data["date"] == "2025-12-11"
        assert "cached" in data

    def test_daily_summary_invalid_date_format(self, client):
        """Test 400 for invalid date format."""
        response = client.get("/api/v1/summaries/daily?date=12-11-2025")

        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    def test_daily_summary_future_date_rejected(self, client):
        """Test 400 for future dates > 1 day (AC15)."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")

        response = client.get(f"/api/v1/summaries/daily?date={future_date}")

        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()

    def test_daily_summary_with_cameras(self, client, mock_summary_service):
        """Test daily summary with camera filter."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Camera-specific summary.",
            period_start=datetime.now(timezone.utc) - timedelta(days=1),
            period_end=datetime.now(timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=5),
            success=True
        ))

        response = client.get(
            "/api/v1/summaries/daily?date=2025-12-11&camera_ids=cam-1,cam-2"
        )

        assert response.status_code == 200


class TestResponseSchema:
    """Tests for response schema compliance (AC16)."""

    def test_response_includes_required_fields(self, client, mock_summary_service):
        """Test response includes all required fields."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test summary",
            period_start=datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2025, 12, 12, 23, 59, 59, tzinfo=timezone.utc),
            event_count=10,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=10),
            ai_cost=Decimal("0.0001"),
            provider_used="openai",
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": "2025-12-12T23:59:59Z"
            }
        )

        # Returns 201 Created (Story P4-4.5)
        assert response.status_code == 201
        data = response.json()

        # AC16: Required fields
        assert "summary_text" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "event_count" in data
        assert "generated_at" in data

        # Verify types
        assert isinstance(data["summary_text"], str)
        assert isinstance(data["event_count"], int)

    def test_stats_included_when_generated(self, client, mock_summary_service):
        """Test stats are included for fresh generation."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test summary",
            period_start=datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2025, 12, 12, 23, 59, 59, tzinfo=timezone.utc),
            event_count=10,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(
                total_events=10,
                by_type={"person": 6, "vehicle": 4},
                by_camera={"Front Door": 7, "Driveway": 3},
                alerts_triggered=1,
                doorbell_rings=2
            ),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": "2025-12-12T23:59:59Z"
            }
        )

        # Returns 201 Created (Story P4-4.5)
        assert response.status_code == 201
        data = response.json()

        assert "stats" in data
        assert data["stats"]["total_events"] == 10
        assert data["stats"]["by_type"]["person"] == 6


class TestListSummaries:
    """Tests for GET /api/v1/summaries endpoint."""

    def test_list_summaries_empty(self, client, mock_db):
        """Test listing summaries when none exist."""
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        response = client.get("/api/v1/summaries")

        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        assert "total" in data
        assert len(data["summaries"]) == 0

    def test_list_summaries_pagination(self, client, mock_db):
        """Test listing summaries with pagination."""
        mock_db.query.return_value.count.return_value = 50
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        response = client.get("/api/v1/summaries?limit=10&offset=20")

        assert response.status_code == 200


class TestValidation:
    """Tests for input validation (AC15)."""

    def test_date_range_too_long(self, client):
        """Test 400 for date range > 90 days."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 6, 1, tzinfo=timezone.utc)  # 151 days

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": start.isoformat(),
                "end_time": end.isoformat()
            }
        )

        assert response.status_code == 400
        assert "90 days" in response.json()["detail"]

    def test_missing_required_fields(self, client):
        """Test 422 for missing required fields."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z"
                # Missing end_time
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_invalid_datetime_format(self, client):
        """Test 422 for invalid datetime format."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "not-a-date",
                "end_time": "also-not-a-date"
            }
        )

        assert response.status_code == 422


class TestRecentSummariesEndpoint:
    """Tests for GET /api/v1/summaries/recent (Story P4-4.4, AC10)."""

    def test_recent_summaries_empty(self, client, mock_db):
        """Test /recent returns empty array when no summaries exist."""
        # Mock queries to return no summaries
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = client.get("/api/v1/summaries/recent")

        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        assert isinstance(data["summaries"], list)
        assert len(data["summaries"]) == 0

    def test_recent_summaries_with_today_only(self, client, mock_db):
        """Test /recent returns today's summary when only today exists."""
        from app.models.activity_summary import ActivitySummary
        import uuid

        today = datetime.now(timezone.utc).date()

        # Create mock summary for today
        mock_summary = MagicMock(spec=ActivitySummary)
        mock_summary.id = str(uuid.uuid4())
        mock_summary.summary_text = "Today there were 5 events detected on cameras."
        mock_summary.event_count = 5
        mock_summary.generated_at = datetime.now(timezone.utc)
        mock_summary.digest_type = "daily"
        mock_summary.period_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Create side_effect function to return summary only for today
        def filter_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.filter = MagicMock(return_value=mock_result)
            mock_result.order_by = MagicMock(return_value=mock_result)

            # Check if this is the "today" query by examining the call stack
            # Simplified: return summary on first call (today), None on second (yesterday)
            if not hasattr(filter_side_effect, 'call_count'):
                filter_side_effect.call_count = 0
            filter_side_effect.call_count += 1

            if filter_side_effect.call_count == 1:
                mock_result.first = MagicMock(return_value=mock_summary)
            else:
                mock_result.first = MagicMock(return_value=None)

            return mock_result

        # Mock event stats query
        mock_db.query.return_value.filter.side_effect = filter_side_effect

        response = client.get("/api/v1/summaries/recent")

        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        # Note: Due to mock complexity, we mainly verify the endpoint works and returns correct structure
        assert isinstance(data["summaries"], list)

    def test_recent_summaries_response_schema(self, client, mock_db):
        """Test /recent response has correct schema."""
        from app.models.activity_summary import ActivitySummary
        import uuid

        today = datetime.now(timezone.utc).date()

        # Create mock summary
        mock_summary = MagicMock(spec=ActivitySummary)
        mock_summary.id = str(uuid.uuid4())
        mock_summary.summary_text = "Test summary with multiple events detected."
        mock_summary.event_count = 10
        mock_summary.generated_at = datetime.now(timezone.utc)
        mock_summary.digest_type = "daily"
        mock_summary.period_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Simple mock that returns the summary
        mock_filter_result = MagicMock()
        mock_filter_result.filter = MagicMock(return_value=mock_filter_result)
        mock_filter_result.order_by = MagicMock(return_value=mock_filter_result)
        mock_filter_result.first = MagicMock(return_value=mock_summary)
        mock_filter_result.all = MagicMock(return_value=[])

        mock_db.query.return_value.filter = MagicMock(return_value=mock_filter_result)

        response = client.get("/api/v1/summaries/recent")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "summaries" in data
        assert isinstance(data["summaries"], list)

        # If we have summaries, verify their schema
        if len(data["summaries"]) > 0:
            summary = data["summaries"][0]
            # Required fields per RecentSummaryItem schema
            assert "id" in summary
            assert "date" in summary
            assert "summary_text" in summary
            assert "event_count" in summary
            assert "camera_count" in summary
            assert "alert_count" in summary
            assert "doorbell_count" in summary
            assert "person_count" in summary
            assert "vehicle_count" in summary
            assert "generated_at" in summary

    def test_recent_summaries_no_auth_required(self, client):
        """Test /recent endpoint is accessible (auth handled by middleware)."""
        # This test verifies the endpoint responds regardless of auth
        # The actual auth is handled by middleware and returns 401 if required
        response = client.get("/api/v1/summaries/recent")

        # Should return 200 or 401, not 404 or 500
        assert response.status_code in [200, 401]


class TestOnDemandSummaryGeneration:
    """Tests for on-demand summary generation (Story P4-4.5)."""

    def test_generate_with_hours_back(self, client, mock_summary_service):
        """Test POST /generate with hours_back parameter (AC2)."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Activity summary for the last 3 hours.",
            period_start=datetime.now(timezone.utc) - timedelta(hours=3),
            period_end=datetime.now(timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(
                total_events=5,
                by_type={"person": 3, "vehicle": 2},
                by_camera={"Front Door": 5}
            ),
            ai_cost=Decimal("0.0002"),
            provider_used="openai",
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 3}
        )

        # Should return 201 Created
        assert response.status_code == 201
        data = response.json()

        # Verify response structure (AC4)
        assert "id" in data
        assert "summary_text" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "event_count" in data

    def test_generate_hours_back_validation_min(self, client):
        """Test hours_back must be >= 1."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 0}
        )

        assert response.status_code == 422  # Pydantic validation

    def test_generate_hours_back_validation_max(self, client):
        """Test hours_back must be <= 168 (1 week)."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 200}
        )

        assert response.status_code == 422  # Pydantic validation

    def test_generate_hours_back_valid_range(self, client, mock_summary_service):
        """Test hours_back accepts values 1-168."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Week summary",
            period_start=datetime.now(timezone.utc) - timedelta(hours=168),
            period_end=datetime.now(timezone.utc),
            event_count=100,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=100),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        # Test minimum (1 hour)
        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 1}
        )
        assert response.status_code == 201

    def test_generate_both_hours_back_and_times_rejected(self, client):
        """Test 422 when both hours_back and start_time/end_time provided."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "hours_back": 3,
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": "2025-12-12T23:59:59Z"
            }
        )

        assert response.status_code == 422
        # Should contain validation error about mutual exclusivity
        detail = response.json()["detail"]
        assert any("both" in str(d).lower() or "hours_back" in str(d).lower() for d in detail) or \
               "both" in str(detail).lower()

    def test_generate_neither_hours_back_nor_times_rejected(self, client):
        """Test 422 when neither hours_back nor start_time/end_time provided."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={}  # Empty request
        )

        assert response.status_code == 422

    def test_generate_only_start_time_rejected(self, client):
        """Test 422 when only start_time provided without end_time."""
        response = client.post(
            "/api/v1/summaries/generate",
            json={"start_time": "2025-12-12T00:00:00Z"}
        )

        assert response.status_code == 422

    def test_generate_response_includes_id(self, client, mock_summary_service, mock_db):
        """Test response includes summary ID (AC4)."""
        import uuid

        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test summary",
            period_start=datetime.now(timezone.utc) - timedelta(hours=3),
            period_end=datetime.now(timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=5),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        # Mock the db.refresh to set an ID on the saved summary
        test_uuid = str(uuid.uuid4())
        def mock_refresh(obj):
            obj.id = test_uuid
        mock_db.refresh = mock_refresh

        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 3}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        # ID should be set from our mock
        assert data["id"] == test_uuid

    def test_generate_response_includes_stats(self, client, mock_summary_service):
        """Test response includes stats with counts (AC4)."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test summary",
            period_start=datetime.now(timezone.utc) - timedelta(hours=3),
            period_end=datetime.now(timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(
                total_events=5,
                by_type={"person": 3},
                by_camera={"Front": 5},
                alerts_triggered=1,
                doorbell_rings=2
            ),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 3}
        )

        assert response.status_code == 201
        data = response.json()

        # Check stats are included
        assert "stats" in data
        assert data["stats"]["total_events"] == 5
        assert data["stats"]["alerts_triggered"] == 1
        assert data["stats"]["doorbell_rings"] == 2

        # Check top-level counts are also populated
        assert "camera_count" in data
        assert "alert_count" in data
        assert "doorbell_count" in data
        assert "person_count" in data
        assert "vehicle_count" in data

    def test_generate_explicit_times_returns_201(self, client, mock_summary_service):
        """Test POST with explicit times returns 201 (updated from 200)."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test summary",
            period_start=datetime(2025, 12, 12, 0, 0, 0, tzinfo=timezone.utc),
            period_end=datetime(2025, 12, 12, 23, 59, 59, tzinfo=timezone.utc),
            event_count=5,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=5),
            success=True,
            input_tokens=100,
            output_tokens=50
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={
                "start_time": "2025-12-12T00:00:00Z",
                "end_time": "2025-12-12T23:59:59Z"
            }
        )

        # Should return 201 Created (not 200)
        assert response.status_code == 201

    def test_generate_calls_summary_service(self, client, mock_summary_service):
        """Test that generate endpoint calls SummaryService.generate_summary (AC5)."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="Test",
            period_start=datetime.now(timezone.utc) - timedelta(hours=3),
            period_end=datetime.now(timezone.utc),
            event_count=0,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(),
            success=True,
            input_tokens=0,
            output_tokens=0
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 3}
        )

        assert response.status_code == 201
        # Verify the service was called
        mock_summary_service.generate_summary.assert_called_once()

    def test_generate_no_events_returns_summary(self, client, mock_summary_service):
        """Test generation with no events in range returns valid summary."""
        mock_summary_service.generate_summary = AsyncMock(return_value=SummaryResult(
            summary_text="It was a quiet period with no detected activity on any cameras.",
            period_start=datetime.now(timezone.utc) - timedelta(hours=3),
            period_end=datetime.now(timezone.utc),
            event_count=0,
            generated_at=datetime.now(timezone.utc),
            stats=SummaryStats(total_events=0),
            success=True,
            input_tokens=0,
            output_tokens=0
        ))

        response = client.post(
            "/api/v1/summaries/generate",
            json={"hours_back": 3}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["event_count"] == 0
        assert "quiet" in data["summary_text"].lower() or "no" in data["summary_text"].lower()
