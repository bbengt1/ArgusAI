"""
Unit tests for PatternService (Story P4-3.5: Pattern Detection)

Tests coverage:
- AC1: Hourly activity distribution calculation
- AC2: Daily activity distribution calculation
- AC3: Peak hour identification
- AC4: Average events per day calculation
- AC5: Quiet hour identification
- AC7: get_patterns() returns activity patterns
- AC8: is_typical_timing() returns timing analysis
"""
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
import statistics

from app.services.pattern_service import (
    PatternService,
    PatternData,
    TimingAnalysisResult,
    get_pattern_service,
    reset_pattern_service,
)
from app.models.camera_activity_pattern import CameraActivityPattern
from app.models.event import Event
from app.models.camera import Camera


class TestPatternServiceCalculations:
    """Test pattern calculation methods."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    def test_calculate_hourly_distribution_basic(self):
        """AC1: Test hourly distribution calculation with events spread across hours."""
        # Create mock events at specific hours
        events = []
        for hour in [9, 9, 9, 14, 14, 17, 17, 17, 17]:
            event = MagicMock(spec=Event)
            event.timestamp = datetime(2025, 12, 10, hour, 30, tzinfo=timezone.utc)
            events.append(event)

        result = self.service._calculate_hourly_distribution(events)

        # Verify structure
        assert len(result) == 24  # All hours represented
        assert all(h.zfill(2) in result for h in [str(i) for i in range(24)])

        # Verify counts
        assert result["09"] == 3
        assert result["14"] == 2
        assert result["17"] == 4
        assert result["00"] == 0
        assert result["23"] == 0

    def test_calculate_hourly_distribution_empty(self):
        """AC1: Test hourly distribution with no events."""
        result = self.service._calculate_hourly_distribution([])

        assert len(result) == 24
        assert all(count == 0 for count in result.values())

    def test_calculate_daily_distribution_basic(self):
        """AC2: Test daily distribution calculation across days of week."""
        # Create events: 3 on Monday (0), 5 on Wednesday (2), 2 on Saturday (5)
        events = []

        # Monday events (2025-12-08 is a Monday)
        for _ in range(3):
            event = MagicMock(spec=Event)
            event.timestamp = datetime(2025, 12, 8, 10, 0, tzinfo=timezone.utc)
            events.append(event)

        # Wednesday events (2025-12-10 is a Wednesday)
        for _ in range(5):
            event = MagicMock(spec=Event)
            event.timestamp = datetime(2025, 12, 10, 14, 0, tzinfo=timezone.utc)
            events.append(event)

        # Saturday events (2025-12-13 is a Saturday)
        for _ in range(2):
            event = MagicMock(spec=Event)
            event.timestamp = datetime(2025, 12, 13, 9, 0, tzinfo=timezone.utc)
            events.append(event)

        result = self.service._calculate_daily_distribution(events)

        # Verify structure
        assert len(result) == 7  # All days represented
        assert all(str(d) in result for d in range(7))

        # Verify counts
        assert result["0"] == 3  # Monday
        assert result["2"] == 5  # Wednesday
        assert result["5"] == 2  # Saturday
        assert result["1"] == 0  # Tuesday
        assert result["6"] == 0  # Sunday

    def test_calculate_peak_hours_basic(self):
        """AC3: Test peak hour identification - above mean + 0.5*std_dev."""
        # Create distribution with clear peaks at hours 9, 14, 17
        hourly = {str(h).zfill(2): 0 for h in range(24)}
        hourly["09"] = 20  # Peak
        hourly["14"] = 25  # Peak
        hourly["17"] = 30  # Peak (highest)
        hourly["10"] = 5   # Below average
        hourly["12"] = 3   # Below average

        result = self.service._calculate_peak_hours(hourly)

        # Calculate expected threshold
        counts = list(hourly.values())
        mean = statistics.mean(counts)
        std_dev = statistics.stdev(counts)
        threshold = mean + (0.5 * std_dev)

        # Peak hours should have count > threshold
        assert "09" in result
        assert "14" in result
        assert "17" in result
        assert "10" not in result
        assert "12" not in result

    def test_calculate_peak_hours_empty(self):
        """AC3: Test peak hour identification with no events."""
        hourly = {str(h).zfill(2): 0 for h in range(24)}
        result = self.service._calculate_peak_hours(hourly)
        assert result == []

    def test_calculate_peak_hours_uniform(self):
        """AC3: Test peak hours with uniform distribution."""
        hourly = {str(h).zfill(2): 10 for h in range(24)}
        result = self.service._calculate_peak_hours(hourly)
        assert result == []  # No peaks when all values are the same

    def test_calculate_quiet_hours_basic(self):
        """AC5: Test quiet hour identification - below 10% of max."""
        hourly = {str(h).zfill(2): 0 for h in range(24)}
        # Peak activity at certain hours
        hourly["09"] = 100
        hourly["14"] = 80
        hourly["17"] = 60
        # Low activity hours
        hourly["02"] = 5   # 5% of max - quiet
        hourly["03"] = 8   # 8% of max - quiet
        hourly["04"] = 10  # 10% of max - borderline, just above threshold
        hourly["05"] = 15  # 15% of max - not quiet

        result = self.service._calculate_quiet_hours(hourly)

        # Threshold is 10% of max (100) = 10
        # Hours with < 10 events are quiet
        assert "02" in result
        assert "03" in result
        assert "04" not in result  # >= 10%
        assert "05" not in result  # > 10%
        assert "00" in result      # 0 events

    def test_calculate_quiet_hours_all_zero(self):
        """AC5: Test quiet hours when all events are zero."""
        hourly = {str(h).zfill(2): 0 for h in range(24)}
        result = self.service._calculate_quiet_hours(hourly)
        # All hours are quiet when max is 0
        assert len(result) == 24


class TestPatternServiceGetPatterns:
    """Test get_patterns method."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    @pytest.mark.asyncio
    async def test_get_patterns_returns_data(self):
        """AC7: Test get_patterns returns activity patterns."""
        # Setup mock database session
        db = MagicMock()

        # Create mock pattern record
        mock_pattern = MagicMock(spec=CameraActivityPattern)
        mock_pattern.camera_id = "test-camera-123"
        mock_pattern.hourly_distribution = json.dumps({"09": 10, "14": 15})
        mock_pattern.daily_distribution = json.dumps({"0": 20, "1": 25})
        mock_pattern.peak_hours = json.dumps(["09", "14"])
        mock_pattern.quiet_hours = json.dumps(["02", "03", "04"])
        mock_pattern.average_events_per_day = 8.5
        mock_pattern.last_calculated_at = datetime(2025, 12, 11, 10, 0, tzinfo=timezone.utc)
        mock_pattern.calculation_window_days = 30

        # Mock query
        db.query.return_value.filter_by.return_value.first.return_value = mock_pattern

        result = await self.service.get_patterns(db, "test-camera-123")

        assert result is not None
        assert isinstance(result, PatternData)
        assert result.camera_id == "test-camera-123"
        assert result.hourly_distribution == {"09": 10, "14": 15}
        assert result.daily_distribution == {"0": 20, "1": 25}
        assert result.peak_hours == ["09", "14"]
        assert result.quiet_hours == ["02", "03", "04"]
        assert result.average_events_per_day == 8.5
        assert result.insufficient_data is False

    @pytest.mark.asyncio
    async def test_get_patterns_returns_none_when_not_found(self):
        """AC7: Test get_patterns returns None when no patterns exist."""
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None

        result = await self.service.get_patterns(db, "nonexistent-camera")

        assert result is None


class TestPatternServiceTimingAnalysis:
    """Test is_typical_timing method."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    @pytest.mark.asyncio
    async def test_is_typical_timing_quiet_hour(self):
        """AC8: Test timing analysis identifies quiet hours as unusual."""
        db = MagicMock()

        # Mock pattern with quiet hours including 03
        mock_pattern = MagicMock(spec=CameraActivityPattern)
        mock_pattern.camera_id = "test-camera"
        mock_pattern.hourly_distribution = json.dumps({str(h).zfill(2): 10 for h in range(24)})
        mock_pattern.daily_distribution = json.dumps({str(d): 50 for d in range(7)})
        mock_pattern.peak_hours = json.dumps(["09", "14", "17"])
        mock_pattern.quiet_hours = json.dumps(["02", "03", "04", "05"])
        mock_pattern.average_events_per_day = 8.5
        mock_pattern.last_calculated_at = datetime.now(timezone.utc)
        mock_pattern.calculation_window_days = 30

        db.query.return_value.filter_by.return_value.first.return_value = mock_pattern

        # Test at 3 AM (quiet hour)
        event_time = datetime(2025, 12, 11, 3, 30, tzinfo=timezone.utc)
        result = await self.service.is_typical_timing(db, "test-camera", event_time)

        assert isinstance(result, TimingAnalysisResult)
        assert result.is_typical is False
        assert result.confidence == 0.8
        assert "03:30" in result.reason or "normally quiet" in result.reason

    @pytest.mark.asyncio
    async def test_is_typical_timing_peak_hour(self):
        """AC8: Test timing analysis identifies peak hours as typical."""
        db = MagicMock()

        # Mock pattern with peak hours including 14
        mock_pattern = MagicMock(spec=CameraActivityPattern)
        mock_pattern.camera_id = "test-camera"
        mock_pattern.hourly_distribution = json.dumps({str(h).zfill(2): 10 for h in range(24)})
        mock_pattern.daily_distribution = json.dumps({str(d): 50 for d in range(7)})
        mock_pattern.peak_hours = json.dumps(["09", "14", "17"])
        mock_pattern.quiet_hours = json.dumps(["02", "03", "04", "05"])
        mock_pattern.average_events_per_day = 8.5
        mock_pattern.last_calculated_at = datetime.now(timezone.utc)
        mock_pattern.calculation_window_days = 30

        db.query.return_value.filter_by.return_value.first.return_value = mock_pattern

        # Test at 2 PM (peak hour)
        event_time = datetime(2025, 12, 11, 14, 30, tzinfo=timezone.utc)
        result = await self.service.is_typical_timing(db, "test-camera", event_time)

        assert result.is_typical is True
        assert result.confidence == 0.9
        assert "Typical activity time" in result.reason

    @pytest.mark.asyncio
    async def test_is_typical_timing_normal_period(self):
        """AC8: Test timing analysis for normal (non-peak, non-quiet) hours."""
        db = MagicMock()

        # Mock pattern
        mock_pattern = MagicMock(spec=CameraActivityPattern)
        mock_pattern.camera_id = "test-camera"
        mock_pattern.hourly_distribution = json.dumps({str(h).zfill(2): 10 for h in range(24)})
        mock_pattern.daily_distribution = json.dumps({str(d): 50 for d in range(7)})
        mock_pattern.peak_hours = json.dumps(["09", "14", "17"])
        mock_pattern.quiet_hours = json.dumps(["02", "03", "04", "05"])
        mock_pattern.average_events_per_day = 8.5
        mock_pattern.last_calculated_at = datetime.now(timezone.utc)
        mock_pattern.calculation_window_days = 30

        db.query.return_value.filter_by.return_value.first.return_value = mock_pattern

        # Test at 11 AM (normal hour - not peak, not quiet)
        event_time = datetime(2025, 12, 11, 11, 30, tzinfo=timezone.utc)
        result = await self.service.is_typical_timing(db, "test-camera", event_time)

        assert result.is_typical is True
        assert result.confidence == 0.5
        assert "Normal activity period" in result.reason

    @pytest.mark.asyncio
    async def test_is_typical_timing_insufficient_data(self):
        """AC8: Test timing analysis returns None when no patterns exist."""
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None

        event_time = datetime(2025, 12, 11, 10, 0, tzinfo=timezone.utc)
        result = await self.service.is_typical_timing(db, "test-camera", event_time)

        assert result.is_typical is None
        assert result.confidence == 0.0
        assert "Insufficient history" in result.reason

    @pytest.mark.asyncio
    async def test_is_typical_timing_low_activity_day(self):
        """AC8: Test timing analysis identifies low-activity days."""
        db = MagicMock()

        # Mock pattern with very low Sunday (day 6) activity
        daily = {str(d): 100 for d in range(7)}
        daily["6"] = 10  # Sunday has much lower activity

        mock_pattern = MagicMock(spec=CameraActivityPattern)
        mock_pattern.camera_id = "test-camera"
        mock_pattern.hourly_distribution = json.dumps({str(h).zfill(2): 10 for h in range(24)})
        mock_pattern.daily_distribution = json.dumps(daily)
        mock_pattern.peak_hours = json.dumps([])  # No peak hours
        mock_pattern.quiet_hours = json.dumps([])  # No quiet hours
        mock_pattern.average_events_per_day = 8.5
        mock_pattern.last_calculated_at = datetime.now(timezone.utc)
        mock_pattern.calculation_window_days = 30

        db.query.return_value.filter_by.return_value.first.return_value = mock_pattern

        # Test on a Sunday (2025-12-14 is Sunday)
        event_time = datetime(2025, 12, 14, 10, 0, tzinfo=timezone.utc)
        result = await self.service.is_typical_timing(db, "test-camera", event_time)

        assert result.is_typical is False
        assert result.confidence == 0.6
        assert "Sunday" in result.reason


class TestPatternServiceSingleton:
    """Test singleton pattern."""

    def test_get_pattern_service_returns_same_instance(self):
        """Test that get_pattern_service returns singleton."""
        reset_pattern_service()

        service1 = get_pattern_service()
        service2 = get_pattern_service()

        assert service1 is service2

    def test_reset_pattern_service(self):
        """Test that reset_pattern_service creates new instance."""
        service1 = get_pattern_service()
        reset_pattern_service()
        service2 = get_pattern_service()

        assert service1 is not service2


class TestPatternServiceEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pattern_service()
        self.service = PatternService()

    def test_calculate_hourly_distribution_single_event(self):
        """Test hourly distribution with single event."""
        event = MagicMock(spec=Event)
        event.timestamp = datetime(2025, 12, 10, 12, 0, tzinfo=timezone.utc)

        result = self.service._calculate_hourly_distribution([event])

        assert result["12"] == 1
        assert sum(result.values()) == 1

    def test_calculate_peak_hours_single_peak(self):
        """Test peak hours with only one hour having activity."""
        hourly = {str(h).zfill(2): 0 for h in range(24)}
        hourly["12"] = 100  # Only noon has activity

        result = self.service._calculate_peak_hours(hourly)

        # Single hour with all activity is a peak
        assert "12" in result

    @pytest.mark.asyncio
    async def test_recalculate_patterns_camera_not_found(self):
        """Test recalculation returns None for non-existent camera."""
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None

        result = await self.service.recalculate_patterns(db, "nonexistent-camera")

        assert result is None
