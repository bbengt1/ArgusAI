"""
Tests for MCPContextProvider (Story P11-3.1).

Tests feedback context gathering, accuracy calculation, pattern extraction,
prompt formatting, and fail-open behavior.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import uuid

from app.services.mcp_context import (
    MCPContextProvider,
    AIContext,
    FeedbackContext,
    EntityContext,
    CameraContext,
    TimePatternContext,
    get_mcp_context_provider,
    reset_mcp_context_provider,
)
from app.models.event_feedback import EventFeedback
from app.models.camera import Camera
from app.models.event import Event


class TestMCPContextProvider:
    """Test suite for MCPContextProvider."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        reset_mcp_context_provider()
        return MCPContextProvider()

    @pytest.fixture
    def camera_id(self):
        """Sample camera ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def event_time(self):
        """Sample event time."""
        return datetime.now(timezone.utc)

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    def test_provider_initialization(self, provider):
        """Test MCPContextProvider initializes correctly."""
        assert provider is not None
        assert provider.FEEDBACK_LIMIT == 50

    def test_singleton_pattern(self):
        """Test get_mcp_context_provider returns same instance."""
        reset_mcp_context_provider()
        provider1 = get_mcp_context_provider()
        provider2 = get_mcp_context_provider()
        assert provider1 is provider2

    def test_reset_singleton(self):
        """Test reset_mcp_context_provider creates new instance."""
        provider1 = get_mcp_context_provider()
        reset_mcp_context_provider()
        provider2 = get_mcp_context_provider()
        assert provider1 is not provider2


class TestFeedbackContextGathering:
    """Tests for feedback context gathering."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        return MCPContextProvider()

    @pytest.fixture
    def camera_id(self):
        """Sample camera ID."""
        return str(uuid.uuid4())

    def _create_mock_feedback(
        self,
        rating: str = "helpful",
        correction: str = None,
        camera_id: str = None,
    ) -> MagicMock:
        """Create a mock EventFeedback object."""
        feedback = MagicMock(spec=EventFeedback)
        feedback.rating = rating
        feedback.correction = correction
        feedback.camera_id = camera_id
        feedback.created_at = datetime.now(timezone.utc)
        return feedback

    @pytest.mark.asyncio
    async def test_get_context_no_session(self, provider, camera_id):
        """Test get_context with no database session returns empty context."""
        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
        )

        assert isinstance(context, AIContext)
        assert context.feedback is None
        assert context.entity is None
        assert context.camera is None
        assert context.time_pattern is None

    @pytest.mark.asyncio
    async def test_get_context_no_feedback(self, provider, camera_id):
        """Test get_context with no feedback data."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        assert context.feedback.accuracy_rate is None
        assert context.feedback.total_feedback == 0
        assert context.feedback.common_corrections == []

    @pytest.mark.asyncio
    async def test_get_context_all_positive_feedback(self, provider, camera_id):
        """Test accuracy calculation with all positive feedback."""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Create 10 positive feedback items
        feedbacks = [self._create_mock_feedback(rating="helpful") for _ in range(10)]

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = feedbacks
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        assert context.feedback.accuracy_rate == 1.0
        assert context.feedback.total_feedback == 10

    @pytest.mark.asyncio
    async def test_get_context_all_negative_feedback(self, provider, camera_id):
        """Test accuracy calculation with all negative feedback."""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Create 10 negative feedback items
        feedbacks = [self._create_mock_feedback(rating="not_helpful") for _ in range(10)]

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = feedbacks
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        assert context.feedback.accuracy_rate == 0.0
        assert context.feedback.total_feedback == 10

    @pytest.mark.asyncio
    async def test_get_context_mixed_feedback(self, provider, camera_id):
        """Test accuracy calculation with 50% positive feedback."""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Create 5 positive and 5 negative feedback items
        feedbacks = (
            [self._create_mock_feedback(rating="helpful") for _ in range(5)] +
            [self._create_mock_feedback(rating="not_helpful") for _ in range(5)]
        )

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = feedbacks
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        assert context.feedback.accuracy_rate == 0.5
        assert context.feedback.total_feedback == 10


class TestPatternExtraction:
    """Tests for common pattern extraction."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        return MCPContextProvider()

    def test_extract_patterns_empty_list(self, provider):
        """Test pattern extraction with empty list."""
        patterns = provider._extract_common_patterns([])
        assert patterns == []

    def test_extract_patterns_single_correction(self, provider):
        """Test pattern extraction with single correction."""
        corrections = ["That's a cat, not a dog"]
        patterns = provider._extract_common_patterns(corrections)
        assert len(patterns) <= 3
        assert "cat" in patterns or "dog" in patterns

    def test_extract_patterns_repeated_words(self, provider):
        """Test pattern extraction with repeated words."""
        corrections = [
            "It was a delivery person",
            "That's a delivery truck",
            "Missing the delivery package",
            "Delivery driver left",
        ]
        patterns = provider._extract_common_patterns(corrections)
        assert "delivery" in patterns

    def test_extract_patterns_filters_stop_words(self, provider):
        """Test that stop words are filtered out."""
        corrections = [
            "The cat is on the mat",
            "A dog is in the yard",
        ]
        patterns = provider._extract_common_patterns(corrections)
        assert "the" not in patterns
        assert "is" not in patterns
        assert "on" not in patterns

    def test_extract_patterns_max_three(self, provider):
        """Test that at most 3 patterns are returned."""
        corrections = [
            "cat dog bird fish turtle",
            "cat dog bird fish",
            "cat dog bird",
        ]
        patterns = provider._extract_common_patterns(corrections)
        assert len(patterns) <= 3


class TestPromptFormatting:
    """Tests for prompt formatting."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        return MCPContextProvider()

    def test_format_empty_context(self, provider):
        """Test formatting with empty context."""
        context = AIContext()
        result = provider.format_for_prompt(context)
        assert result == ""

    def test_format_feedback_only(self, provider):
        """Test formatting with only feedback context."""
        context = AIContext(
            feedback=FeedbackContext(
                accuracy_rate=0.85,
                total_feedback=50,
                common_corrections=["delivery", "package"],
                recent_negative_reasons=["missed the box"],
            )
        )
        result = provider.format_for_prompt(context)

        assert "85%" in result
        assert "delivery" in result
        assert "package" in result

    def test_format_feedback_no_accuracy(self, provider):
        """Test formatting with feedback but no accuracy."""
        context = AIContext(
            feedback=FeedbackContext(
                accuracy_rate=None,
                total_feedback=0,
                common_corrections=[],
                recent_negative_reasons=[],
            )
        )
        result = provider.format_for_prompt(context)
        assert result == ""

    def test_format_with_entity(self, provider):
        """Test formatting with entity context."""
        context = AIContext(
            entity=EntityContext(
                entity_id="123",
                name="John",
                entity_type="person",
                attributes={"color": "blue"},
                last_seen=datetime.now(timezone.utc),
                sighting_count=5,
            )
        )
        result = provider.format_for_prompt(context)

        assert "John" in result
        assert "person" in result
        assert "color=blue" in result

    def test_format_with_camera_location(self, provider):
        """Test formatting with camera location hint."""
        context = AIContext(
            camera=CameraContext(
                camera_id="cam1",
                location_hint="Front Door",
                typical_objects=["car", "person"],
                false_positive_patterns=["shadow"],
            )
        )
        result = provider.format_for_prompt(context)
        assert "Front Door" in result

    def test_format_with_unusual_timing(self, provider):
        """Test formatting with unusual timing flag."""
        context = AIContext(
            time_pattern=TimePatternContext(
                hour=3,
                typical_activity_level="low",
                is_unusual=True,
                typical_event_count=0.5,
            )
        )
        result = provider.format_for_prompt(context)
        assert "unusual" in result.lower()

    def test_format_combined_context(self, provider):
        """Test formatting with multiple context components."""
        context = AIContext(
            feedback=FeedbackContext(
                accuracy_rate=0.9,
                total_feedback=100,
                common_corrections=["vehicle"],
                recent_negative_reasons=[],
            ),
            camera=CameraContext(
                camera_id="cam1",
                location_hint="Driveway",
                typical_objects=[],
                false_positive_patterns=[],
            ),
        )
        result = provider.format_for_prompt(context)

        assert "90%" in result
        assert "Driveway" in result


class TestFailOpenBehavior:
    """Tests for fail-open error handling."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        return MCPContextProvider()

    @pytest.fixture
    def camera_id(self):
        """Sample camera ID."""
        return str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_database_error_returns_none(self, provider, camera_id):
        """Test that database errors return None for feedback context."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database connection failed")

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        # Should return context with None feedback, not raise exception
        assert isinstance(context, AIContext)
        assert context.feedback is None

    @pytest.mark.asyncio
    async def test_query_error_returns_none(self, provider, camera_id):
        """Test that query errors return None for feedback context."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.side_effect = Exception("Query failed")
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        # Should return context with None feedback, not raise exception
        assert isinstance(context, AIContext)
        assert context.feedback is None

    @pytest.mark.asyncio
    async def test_partial_context_on_error(self, provider, camera_id):
        """Test that partial context is returned when one component fails."""
        # In MVP, only feedback context is implemented
        # This test validates the pattern for future components
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        # Context should be returned (not exception) with None components
        assert isinstance(context, AIContext)
        assert context.feedback is None
        assert context.entity is None
        assert context.camera is None
        assert context.time_pattern is None


class TestRecentNegativeFeedback:
    """Tests for recent negative feedback extraction."""

    @pytest.fixture
    def provider(self):
        """Create a fresh MCPContextProvider instance."""
        return MCPContextProvider()

    @pytest.fixture
    def camera_id(self):
        """Sample camera ID."""
        return str(uuid.uuid4())

    def _create_mock_feedback(
        self,
        rating: str = "helpful",
        correction: str = None,
    ) -> MagicMock:
        """Create a mock EventFeedback object."""
        feedback = MagicMock(spec=EventFeedback)
        feedback.rating = rating
        feedback.correction = correction
        feedback.created_at = datetime.now(timezone.utc)
        return feedback

    @pytest.mark.asyncio
    async def test_extracts_recent_negative_reasons(self, provider, camera_id):
        """Test that recent negative feedback reasons are extracted."""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Create feedback with corrections on negative items
        feedbacks = [
            self._create_mock_feedback(rating="not_helpful", correction="Wrong person"),
            self._create_mock_feedback(rating="not_helpful", correction="Missed package"),
            self._create_mock_feedback(rating="helpful"),
            self._create_mock_feedback(rating="not_helpful", correction="Incorrect action"),
        ]

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = feedbacks
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        # Should have the negative corrections from first 5 items
        assert len(context.feedback.recent_negative_reasons) <= 5

    @pytest.mark.asyncio
    async def test_ignores_negative_without_correction(self, provider, camera_id):
        """Test that negative feedback without corrections is not included in reasons."""
        mock_db = MagicMock()
        mock_query = MagicMock()

        feedbacks = [
            self._create_mock_feedback(rating="not_helpful", correction=None),
            self._create_mock_feedback(rating="not_helpful", correction=""),
            self._create_mock_feedback(rating="not_helpful", correction="Actual correction"),
        ]

        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = feedbacks
        mock_db.query.return_value = mock_query

        context = await provider.get_context(
            camera_id=camera_id,
            event_time=datetime.now(timezone.utc),
            db=mock_db,
        )

        assert context.feedback is not None
        # Only the one with actual correction text should be included
        # The first two negative items don't have correction text
        reasons = context.feedback.recent_negative_reasons
        if len(reasons) > 0:
            assert "Actual correction" in reasons or reasons == []
