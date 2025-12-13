"""
Tests for AlertEngine entity-based matching (Story P4-8.4)

Tests cover:
- Entity ID matching in alert rules
- Entity name pattern matching (fnmatch wildcards)
- Combined entity and other condition matching
"""
import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.services.alert_engine import AlertEngine
from app.models.alert_rule import AlertRule
from app.models.event import Event
from app.models.recognized_entity import RecognizedEntity


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def alert_engine(mock_db):
    """Create AlertEngine instance with mock db."""
    return AlertEngine(mock_db)


@pytest.fixture
def sample_event_with_entities():
    """Create a sample event with matched entity IDs."""
    event = MagicMock(spec=Event)
    event.id = "event-uuid"
    event.camera_id = "camera-uuid"
    event.timestamp = datetime.now(timezone.utc)
    event.description = "John Smith is at the door."
    event.confidence = 85
    event.objects_detected = json.dumps(["person"])
    event.anomaly_score = None
    event.matched_entity_ids = json.dumps(["entity-john-uuid", "entity-jane-uuid"])
    return event


@pytest.fixture
def sample_event_without_entities():
    """Create a sample event without matched entities."""
    event = MagicMock(spec=Event)
    event.id = "event-uuid"
    event.camera_id = "camera-uuid"
    event.timestamp = datetime.now(timezone.utc)
    event.description = "A person is at the door."
    event.confidence = 85
    event.objects_detected = json.dumps(["person"])
    event.anomaly_score = None
    event.matched_entity_ids = None
    return event


@pytest.fixture
def sample_entity_john():
    """Create mock entity for John."""
    entity = MagicMock(spec=RecognizedEntity)
    entity.id = "entity-john-uuid"
    entity.name = "John Smith"
    return entity


@pytest.fixture
def sample_entity_jane():
    """Create mock entity for Jane."""
    entity = MagicMock(spec=RecognizedEntity)
    entity.id = "entity-jane-uuid"
    entity.name = "Jane Doe"
    return entity


def create_rule_with_entity_ids(entity_ids):
    """Create a rule with entity_ids filter."""
    rule = MagicMock(spec=AlertRule)
    rule.id = "rule-uuid"
    rule.name = "Entity ID Rule"
    rule.is_enabled = True
    rule.conditions = "{}"
    rule.actions = json.dumps({"dashboard_notification": True})
    rule.entity_ids = json.dumps(entity_ids) if entity_ids else None
    rule.entity_names = None
    rule.cooldown_minutes = 0
    rule.last_triggered_at = None
    return rule


def create_rule_with_entity_names(entity_names):
    """Create a rule with entity_names filter."""
    rule = MagicMock(spec=AlertRule)
    rule.id = "rule-uuid"
    rule.name = "Entity Name Rule"
    rule.is_enabled = True
    rule.conditions = "{}"
    rule.actions = json.dumps({"dashboard_notification": True})
    rule.entity_ids = None
    rule.entity_names = json.dumps(entity_names) if entity_names else None
    rule.cooldown_minutes = 0
    rule.last_triggered_at = None
    return rule


# =============================================================================
# Entity ID Matching Tests
# =============================================================================


class TestEntityIdMatching:
    """Tests for _check_entity_ids method."""

    def test_no_filter_matches_any(self, alert_engine):
        """Test that no entity filter matches any entity."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=["entity-1"],
            rule_entity_ids=None
        )
        assert result is True

    def test_no_filter_matches_no_entities(self, alert_engine):
        """Test that no entity filter matches events without entities."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=None,
            rule_entity_ids=None
        )
        assert result is True

    def test_filter_matches_exact_entity(self, alert_engine):
        """Test that entity filter matches exact entity ID."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=["entity-john-uuid"],
            rule_entity_ids=["entity-john-uuid"]
        )
        assert result is True

    def test_filter_matches_one_of_multiple_entities(self, alert_engine):
        """Test OR logic - matches if any entity matches."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=["entity-john-uuid", "entity-jane-uuid"],
            rule_entity_ids=["entity-john-uuid"]
        )
        assert result is True

    def test_filter_no_match(self, alert_engine):
        """Test no match when entity ID not in filter."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=["entity-unknown-uuid"],
            rule_entity_ids=["entity-john-uuid"]
        )
        assert result is False

    def test_filter_with_no_event_entities_fails(self, alert_engine):
        """Test that filter with no event entities fails."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=None,
            rule_entity_ids=["entity-john-uuid"]
        )
        assert result is False

    def test_filter_with_empty_event_entities_fails(self, alert_engine):
        """Test that filter with empty event entities fails."""
        result = alert_engine._check_entity_ids(
            event_matched_entity_ids=[],
            rule_entity_ids=["entity-john-uuid"]
        )
        assert result is False


# =============================================================================
# Entity Name Pattern Matching Tests
# =============================================================================


class TestEntityNameMatching:
    """Tests for _check_entity_names method with fnmatch patterns."""

    def test_no_filter_matches_any(self, alert_engine):
        """Test that no name filter matches any entity."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=None
        )
        assert result is True

    def test_no_filter_matches_no_names(self, alert_engine):
        """Test that no name filter matches events without names."""
        result = alert_engine._check_entity_names(
            event_entity_names=None,
            rule_entity_names=None
        )
        assert result is True

    def test_exact_name_match(self, alert_engine):
        """Test exact name match."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["John Smith"]
        )
        assert result is True

    def test_case_insensitive_match(self, alert_engine):
        """Test case-insensitive name matching."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["john smith"]
        )
        assert result is True

    def test_wildcard_prefix_match(self, alert_engine):
        """Test wildcard at start (e.g., '*Smith' matches 'John Smith')."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["*Smith"]
        )
        assert result is True

    def test_wildcard_suffix_match(self, alert_engine):
        """Test wildcard at end (e.g., 'John*' matches 'John Smith')."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["John*"]
        )
        assert result is True

    def test_wildcard_both_sides(self, alert_engine):
        """Test wildcards on both sides (e.g., '*oh*' matches 'John')."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["*oh*"]
        )
        assert result is True

    def test_single_char_wildcard(self, alert_engine):
        """Test single character wildcard (?)."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["J?hn Smith"]
        )
        assert result is True

    def test_character_class_match(self, alert_engine):
        """Test character class matching [abc]."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["[JK]ohn Smith"]
        )
        assert result is True

    def test_no_match_different_name(self, alert_engine):
        """Test no match for different name."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["Jane Doe"]
        )
        assert result is False

    def test_filter_with_no_event_names_fails(self, alert_engine):
        """Test that filter with no event names fails."""
        result = alert_engine._check_entity_names(
            event_entity_names=None,
            rule_entity_names=["John*"]
        )
        assert result is False

    def test_filter_with_empty_event_names_fails(self, alert_engine):
        """Test that filter with empty event names fails."""
        result = alert_engine._check_entity_names(
            event_entity_names=[],
            rule_entity_names=["John*"]
        )
        assert result is False

    def test_or_logic_multiple_patterns(self, alert_engine):
        """Test OR logic - matches if any pattern matches."""
        result = alert_engine._check_entity_names(
            event_entity_names=["John Smith"],
            rule_entity_names=["Jane*", "John*", "Bob*"]
        )
        assert result is True

    def test_mail_carrier_pattern(self, alert_engine):
        """Test common pattern: 'Mail Carrier' matches exactly."""
        result = alert_engine._check_entity_names(
            event_entity_names=["Mail Carrier"],
            rule_entity_names=["Mail Carrier"]
        )
        assert result is True

    def test_delivery_wildcard(self, alert_engine):
        """Test delivery patterns with wildcards."""
        result = alert_engine._check_entity_names(
            event_entity_names=["Amazon Delivery", "FedEx Delivery"],
            rule_entity_names=["*Delivery*"]
        )
        assert result is True


# =============================================================================
# Get Event Entity Info Tests
# =============================================================================


class TestGetEventEntityInfo:
    """Tests for _get_event_entity_info method."""

    def test_get_entity_ids_from_event(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test extracting entity IDs and names from event."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        entity_ids, entity_names = alert_engine._get_event_entity_info(
            sample_event_with_entities
        )

        assert entity_ids == ["entity-john-uuid", "entity-jane-uuid"]
        assert "John Smith" in entity_names
        assert "Jane Doe" in entity_names

    def test_no_entities_returns_empty(
        self, alert_engine, mock_db, sample_event_without_entities
    ):
        """Test event without entities returns empty lists."""
        entity_ids, entity_names = alert_engine._get_event_entity_info(
            sample_event_without_entities
        )

        assert entity_ids == []
        assert entity_names == []

    def test_invalid_json_returns_empty(self, alert_engine, mock_db):
        """Test invalid JSON in matched_entity_ids returns empty."""
        event = MagicMock(spec=Event)
        event.matched_entity_ids = "invalid json"

        entity_ids, entity_names = alert_engine._get_event_entity_info(event)

        assert entity_ids == []


# =============================================================================
# Full Rule Evaluation Tests
# =============================================================================


class TestRuleEvaluationWithEntities:
    """Tests for evaluate_rule with entity matching."""

    def test_rule_matches_with_entity_id(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule with entity_ids matches event."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = create_rule_with_entity_ids(["entity-john-uuid"])
        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is True
        assert details["conditions_checked"]["entity_ids"] is True

    def test_rule_fails_with_wrong_entity_id(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule with different entity_ids fails."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = create_rule_with_entity_ids(["entity-unknown-uuid"])
        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is False
        assert details["conditions_checked"]["entity_ids"] is False

    def test_rule_matches_with_entity_name_pattern(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule with entity_names pattern matches event."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = create_rule_with_entity_names(["John*"])
        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is True
        assert details["conditions_checked"]["entity_names"] is True

    def test_rule_fails_with_wrong_entity_name(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule with different entity_names pattern fails."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = create_rule_with_entity_names(["Bob*"])
        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is False
        assert details["conditions_checked"]["entity_names"] is False

    def test_rule_without_entity_filter_matches_any(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule without entity filters matches events with entities."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = create_rule_with_entity_ids(None)
        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is True
        assert details["conditions_checked"]["entity_ids"] is True
        assert details["conditions_checked"]["entity_names"] is True

    def test_rule_without_entity_filter_matches_event_without_entities(
        self, alert_engine, mock_db, sample_event_without_entities
    ):
        """Test rule without entity filters matches events without entities."""
        rule = create_rule_with_entity_ids(None)
        matched, details = alert_engine.evaluate_rule(rule, sample_event_without_entities)

        assert matched is True

    def test_rule_with_entity_filter_fails_event_without_entities(
        self, alert_engine, mock_db, sample_event_without_entities
    ):
        """Test rule with entity filter fails for events without entities."""
        rule = create_rule_with_entity_ids(["entity-john-uuid"])
        matched, details = alert_engine.evaluate_rule(rule, sample_event_without_entities)

        assert matched is False


# =============================================================================
# Combined Conditions Tests
# =============================================================================


class TestCombinedConditions:
    """Tests for entity matching combined with other conditions."""

    def test_entity_and_object_type_match(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test rule with both entity and object type conditions."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = MagicMock(spec=AlertRule)
        rule.id = "rule-uuid"
        rule.name = "Combined Rule"
        rule.is_enabled = True
        rule.conditions = json.dumps({"object_types": ["person"]})
        rule.actions = json.dumps({"dashboard_notification": True})
        rule.entity_ids = json.dumps(["entity-john-uuid"])
        rule.entity_names = None
        rule.cooldown_minutes = 0
        rule.last_triggered_at = None

        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is True
        assert details["conditions_checked"]["object_types"] is True
        assert details["conditions_checked"]["entity_ids"] is True

    def test_entity_passes_but_object_type_fails(
        self, alert_engine, mock_db, sample_event_with_entities,
        sample_entity_john, sample_entity_jane
    ):
        """Test that rule fails if entity matches but object type doesn't."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            sample_entity_john, sample_entity_jane
        ]

        rule = MagicMock(spec=AlertRule)
        rule.id = "rule-uuid"
        rule.name = "Combined Rule"
        rule.is_enabled = True
        rule.conditions = json.dumps({"object_types": ["vehicle"]})  # Event has "person"
        rule.actions = json.dumps({"dashboard_notification": True})
        rule.entity_ids = json.dumps(["entity-john-uuid"])
        rule.entity_names = None
        rule.cooldown_minutes = 0
        rule.last_triggered_at = None

        matched, details = alert_engine.evaluate_rule(rule, sample_event_with_entities)

        assert matched is False
        assert details["conditions_checked"]["object_types"] is False
        # Entity check shouldn't run if object type failed
        assert "entity_ids" not in details["conditions_checked"]
