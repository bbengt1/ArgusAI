"""
Unit tests for EntityService (Story P4-3.3: Recurring Visitor Detection)

Tests:
- AC1: System clusters similar event embeddings to identify recurring entities
- AC2: RecognizedEntity model stores required fields
- AC3: EntityEvent junction table links entities to events
- AC4: match_or_create_entity returns existing entity or creates new one
- AC5: When match found above threshold, entity is updated
- AC6: When no match above threshold, new entity is created
- AC13: Performance: Entity matching completes in <200ms with 1000 entities
- AC14: Graceful handling when embedding service unavailable
"""
import json
import pytest
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np

from app.services.entity_service import (
    EntityService,
    get_entity_service,
    reset_entity_service,
    EntityMatchResult,
)


class TestEntityMatchResult:
    """Tests for EntityMatchResult dataclass."""

    def test_create_match_result_for_new_entity(self):
        """Test creating match result for a new entity."""
        now = datetime.now(timezone.utc)
        result = EntityMatchResult(
            entity_id="test-entity-id",
            entity_type="person",
            name=None,
            first_seen_at=now,
            last_seen_at=now,
            occurrence_count=1,
            similarity_score=1.0,
            is_new=True,
        )

        assert result.entity_id == "test-entity-id"
        assert result.entity_type == "person"
        assert result.name is None
        assert result.occurrence_count == 1
        assert result.similarity_score == 1.0
        assert result.is_new is True

    def test_create_match_result_for_existing_entity(self):
        """Test creating match result for an existing entity."""
        first_seen = datetime.now(timezone.utc) - timedelta(days=7)
        last_seen = datetime.now(timezone.utc)
        result = EntityMatchResult(
            entity_id="existing-entity-id",
            entity_type="vehicle",
            name="Mail Truck",
            first_seen_at=first_seen,
            last_seen_at=last_seen,
            occurrence_count=15,
            similarity_score=0.87,
            is_new=False,
        )

        assert result.entity_id == "existing-entity-id"
        assert result.entity_type == "vehicle"
        assert result.name == "Mail Truck"
        assert result.occurrence_count == 15
        assert result.similarity_score == 0.87
        assert result.is_new is False


class TestEntityServiceInit:
    """Tests for EntityService initialization."""

    def test_init_with_default_similarity_service(self):
        """Test initialization with default similarity service."""
        service = EntityService()
        assert service._similarity_service is not None
        assert service._entity_cache == {}
        assert service._cache_loaded is False

    def test_init_with_custom_similarity_service(self):
        """Test initialization with custom similarity service."""
        mock_similarity_service = MagicMock()
        service = EntityService(similarity_service=mock_similarity_service)
        assert service._similarity_service == mock_similarity_service

    def test_default_threshold_value(self):
        """Test that default threshold is 0.75."""
        assert EntityService.DEFAULT_THRESHOLD == 0.75


class TestEntityServiceSingleton:
    """Tests for EntityService singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_entity_service()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_entity_service()

    def test_get_entity_service_returns_singleton(self):
        """Test that get_entity_service returns same instance."""
        service1 = get_entity_service()
        service2 = get_entity_service()
        assert service1 is service2

    def test_reset_entity_service_clears_singleton(self):
        """Test that reset_entity_service clears the singleton."""
        service1 = get_entity_service()
        reset_entity_service()
        service2 = get_entity_service()
        assert service1 is not service2


class TestEntityServiceCaching:
    """Tests for EntityService embedding cache."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_entity_service()
        self.service = EntityService()

    def teardown_method(self):
        """Clean up after tests."""
        reset_entity_service()

    def test_cache_initially_empty(self):
        """Test that cache is empty on initialization."""
        assert self.service._entity_cache == {}
        assert self.service._cache_loaded is False

    def test_invalidate_cache_clears_cache(self):
        """Test that _invalidate_cache clears the cache."""
        # Populate cache manually
        self.service._entity_cache = {"entity1": [0.1, 0.2, 0.3]}
        self.service._cache_loaded = True

        self.service._invalidate_cache()

        assert self.service._entity_cache == {}
        assert self.service._cache_loaded is False


class TestMatchOrCreateEntity:
    """Tests for match_or_create_entity method (AC1, AC4, AC5, AC6)."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_entity_service()
        self.service = EntityService()

    def teardown_method(self):
        """Clean up after tests."""
        reset_entity_service()

    @pytest.mark.asyncio
    async def test_creates_new_entity_when_cache_empty(self):
        """AC6: When no existing entities, creates new entity."""
        # Create mock database session
        mock_db = MagicMock()

        # Mock query for entity cache loading (return empty)
        mock_query = MagicMock()
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # Mock event timestamp query
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query.filter.return_value.first.return_value = mock_event

        # Generate test embedding
        embedding = [0.1] * 512

        result = await self.service.match_or_create_entity(
            db=mock_db,
            event_id="test-event-1",
            embedding=embedding,
            entity_type="person",
        )

        assert result.is_new is True
        assert result.entity_type == "person"
        assert result.occurrence_count == 1
        assert result.similarity_score == 1.0
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_matches_existing_entity_above_threshold(self):
        """AC5: When match found above threshold, returns existing entity."""
        mock_db = MagicMock()

        # Create existing entity embedding (very similar to test embedding)
        existing_embedding = [0.1] * 512

        # Mock entity in cache
        mock_entity = MagicMock()
        mock_entity.id = "existing-entity-id"
        mock_entity.reference_embedding = json.dumps(existing_embedding)

        # Set up cache loading
        mock_query = MagicMock()
        mock_query.all.return_value = [mock_entity]
        mock_db.query.return_value = mock_query

        # Mock event timestamp query
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query.filter.return_value.first.return_value = mock_event

        # Test with identical embedding (similarity = 1.0)
        test_embedding = [0.1] * 512

        # Pre-load cache to avoid database query
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Mock the entity update
        mock_existing = MagicMock()
        mock_existing.id = "existing-entity-id"
        mock_existing.entity_type = "person"
        mock_existing.name = "Test Person"
        mock_existing.first_seen_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_existing.last_seen_at = datetime.now(timezone.utc)
        mock_existing.occurrence_count = 5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        result = await self.service.match_or_create_entity(
            db=mock_db,
            event_id="test-event-2",
            embedding=test_embedding,
            entity_type="person",
            threshold=0.75,
        )

        # Should match existing entity
        assert result.is_new is False
        assert result.entity_id == "existing-entity-id"
        assert result.similarity_score >= 0.75

    @pytest.mark.asyncio
    async def test_creates_new_entity_below_threshold(self):
        """AC6: When no match above threshold, creates new entity."""
        mock_db = MagicMock()

        # Create existing entity with very different embedding
        existing_embedding = [0.9, 0.1, 0.0] + [0.0] * 509

        # Pre-load cache
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Test with very different embedding
        test_embedding = [0.0, 0.0, 0.9] + [0.1] * 509

        # Mock event timestamp query
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        mock_db.query.return_value = mock_query

        result = await self.service.match_or_create_entity(
            db=mock_db,
            event_id="test-event-3",
            embedding=test_embedding,
            entity_type="vehicle",
            threshold=0.75,
        )

        assert result.is_new is True
        assert result.entity_type == "vehicle"
        assert result.occurrence_count == 1

    @pytest.mark.asyncio
    async def test_configurable_threshold(self):
        """Test that threshold parameter is respected."""
        mock_db = MagicMock()

        # Create existing entity
        existing_embedding = [1.0, 0.0] + [0.0] * 510

        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Test embedding with moderate similarity (~0.7)
        test_embedding = [0.7, 0.7] + [0.0] * 510

        # Mock event timestamp
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        mock_db.query.return_value = mock_query

        # With high threshold (0.9), should create new entity
        result_high = await self.service.match_or_create_entity(
            db=mock_db,
            event_id="test-event-4",
            embedding=test_embedding,
            entity_type="person",
            threshold=0.9,
        )
        assert result_high.is_new is True


class TestEntityCRUD:
    """Tests for entity CRUD operations (AC7, AC8, AC9, AC10)."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_entity_service()
        self.service = EntityService()

    def teardown_method(self):
        """Clean up after tests."""
        reset_entity_service()

    @pytest.mark.asyncio
    async def test_get_all_entities_returns_paginated_list(self):
        """AC7: GET /api/v1/entities returns list of entities with stats."""
        mock_db = MagicMock()

        # Create mock entities
        mock_entity1 = MagicMock()
        mock_entity1.id = "entity-1"
        mock_entity1.entity_type = "person"
        mock_entity1.name = "Test Person"
        mock_entity1.first_seen_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_entity1.last_seen_at = datetime.now(timezone.utc)
        mock_entity1.occurrence_count = 10

        mock_entity2 = MagicMock()
        mock_entity2.id = "entity-2"
        mock_entity2.entity_type = "vehicle"
        mock_entity2.name = None
        mock_entity2.first_seen_at = datetime.now(timezone.utc) - timedelta(days=3)
        mock_entity2.last_seen_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_entity2.occurrence_count = 5

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_entity1, mock_entity2
        ]
        mock_db.query.return_value = mock_query

        entities, total = await self.service.get_all_entities(
            db=mock_db,
            limit=50,
            offset=0,
        )

        assert total == 2
        assert len(entities) == 2
        assert entities[0]["id"] == "entity-1"
        assert entities[0]["entity_type"] == "person"
        assert entities[1]["id"] == "entity-2"

    @pytest.mark.asyncio
    async def test_get_all_entities_filters_by_type(self):
        """Test filtering entities by type."""
        mock_db = MagicMock()

        mock_entity = MagicMock()
        mock_entity.id = "entity-1"
        mock_entity.entity_type = "person"
        mock_entity.name = None
        mock_entity.first_seen_at = datetime.now(timezone.utc)
        mock_entity.last_seen_at = datetime.now(timezone.utc)
        mock_entity.occurrence_count = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_entity]
        mock_db.query.return_value = mock_query

        entities, total = await self.service.get_all_entities(
            db=mock_db,
            limit=50,
            offset=0,
            entity_type="person",
        )

        assert total == 1
        # Verify filter was called
        mock_query.filter.assert_called()

    @pytest.mark.asyncio
    async def test_get_entity_returns_with_recent_events(self):
        """AC8: GET /api/v1/entities/{id} returns entity with events."""
        mock_db = MagicMock()

        # Mock entity
        mock_entity = MagicMock()
        mock_entity.id = "entity-1"
        mock_entity.entity_type = "person"
        mock_entity.name = "Mail Carrier"
        mock_entity.first_seen_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_entity.last_seen_at = datetime.now(timezone.utc)
        mock_entity.occurrence_count = 5
        mock_entity.created_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_entity.updated_at = datetime.now(timezone.utc)

        # Mock event
        mock_event = MagicMock()
        mock_event.id = "event-1"
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_event.description = "Person at door"
        mock_event.thumbnail_path = "/path/to/thumb.jpg"
        mock_event.camera_id = "camera-1"
        mock_event.similarity_score = 0.92

        # Set up query mocks
        mock_query1 = MagicMock()
        mock_query1.filter.return_value.first.return_value = mock_entity

        mock_query2 = MagicMock()
        mock_query2.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_event
        ]

        mock_db.query.side_effect = [mock_query1, mock_query2]

        entity = await self.service.get_entity(
            db=mock_db,
            entity_id="entity-1",
            include_events=True,
            event_limit=10,
        )

        assert entity is not None
        assert entity["id"] == "entity-1"
        assert entity["name"] == "Mail Carrier"
        assert "recent_events" in entity
        assert len(entity["recent_events"]) == 1

    @pytest.mark.asyncio
    async def test_get_entity_returns_none_for_not_found(self):
        """Test that get_entity returns None when not found."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        entity = await self.service.get_entity(
            db=mock_db,
            entity_id="nonexistent-id",
        )

        assert entity is None

    @pytest.mark.asyncio
    async def test_update_entity_name(self):
        """AC9: PUT /api/v1/entities/{id} allows naming entity."""
        mock_db = MagicMock()

        mock_entity = MagicMock()
        mock_entity.id = "entity-1"
        mock_entity.entity_type = "person"
        mock_entity.name = None
        mock_entity.first_seen_at = datetime.now(timezone.utc)
        mock_entity.last_seen_at = datetime.now(timezone.utc)
        mock_entity.occurrence_count = 5

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_entity
        mock_db.query.return_value = mock_query

        result = await self.service.update_entity(
            db=mock_db,
            entity_id="entity-1",
            name="Mail Carrier",
        )

        assert result is not None
        assert mock_entity.name == "Mail Carrier"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_entity_returns_none_for_not_found(self):
        """Test that update_entity returns None when not found."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = await self.service.update_entity(
            db=mock_db,
            entity_id="nonexistent-id",
            name="Test",
        )

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_entity_removes_entity_and_clears_cache(self):
        """AC10: DELETE /api/v1/entities/{id} removes entity."""
        mock_db = MagicMock()

        mock_entity = MagicMock()
        mock_entity.id = "entity-1"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_entity
        mock_db.query.return_value = mock_query

        # Add entity to cache
        self.service._entity_cache = {"entity-1": [0.1] * 512}

        result = await self.service.delete_entity(
            db=mock_db,
            entity_id="entity-1",
        )

        assert result is True
        mock_db.delete.assert_called_with(mock_entity)
        mock_db.commit.assert_called()
        assert "entity-1" not in self.service._entity_cache

    @pytest.mark.asyncio
    async def test_delete_entity_returns_false_for_not_found(self):
        """Test that delete_entity returns False when not found."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = await self.service.delete_entity(
            db=mock_db,
            entity_id="nonexistent-id",
        )

        assert result is False
        mock_db.delete.assert_not_called()


class TestGetEntityForEvent:
    """Tests for get_entity_for_event method (AC12)."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_entity_service()
        self.service = EntityService()

    def teardown_method(self):
        """Clean up after tests."""
        reset_entity_service()

    @pytest.mark.asyncio
    async def test_returns_entity_summary_for_linked_event(self):
        """AC12: Event response includes matched_entity data."""
        mock_db = MagicMock()

        # Mock result from join query
        mock_result = MagicMock()
        mock_result.id = "entity-1"
        mock_result.entity_type = "person"
        mock_result.name = "Mail Carrier"
        mock_result.first_seen_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_result.occurrence_count = 10
        mock_result.similarity_score = 0.92

        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        entity = await self.service.get_entity_for_event(
            db=mock_db,
            event_id="event-1",
        )

        assert entity is not None
        assert entity["id"] == "entity-1"
        assert entity["name"] == "Mail Carrier"
        assert entity["occurrence_count"] == 10
        assert entity["similarity_score"] == 0.92

    @pytest.mark.asyncio
    async def test_returns_none_for_unlinked_event(self):
        """Test that get_entity_for_event returns None for unlinked events."""
        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        entity = await self.service.get_entity_for_event(
            db=mock_db,
            event_id="unlinked-event",
        )

        assert entity is None


class TestPerformance:
    """Performance tests (AC13)."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_entity_service()
        self.service = EntityService()

    def teardown_method(self):
        """Clean up after tests."""
        reset_entity_service()

    @pytest.mark.asyncio
    async def test_match_1000_entities_under_200ms(self):
        """AC13: Entity matching completes in <200ms with 1000 entities."""
        # Generate 1000 random entity embeddings
        np.random.seed(42)
        entity_embeddings = {}
        for i in range(1000):
            entity_id = f"entity-{i}"
            entity_embeddings[entity_id] = np.random.randn(512).tolist()

        # Pre-load cache
        self.service._entity_cache = entity_embeddings
        self.service._cache_loaded = True

        # Mock database
        mock_db = MagicMock()
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        mock_db.query.return_value = mock_query

        # Generate test embedding
        test_embedding = np.random.randn(512).tolist()

        # Measure time
        start_time = time.time()
        result = await self.service.match_or_create_entity(
            db=mock_db,
            event_id="test-event",
            embedding=test_embedding,
            entity_type="person",
        )
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in under 200ms
        assert elapsed_ms < 200, f"Entity matching took {elapsed_ms:.2f}ms, expected <200ms"
        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Test that cached embeddings provide fast matching."""
        # Pre-load cache with 100 entities
        np.random.seed(42)
        for i in range(100):
            self.service._entity_cache[f"entity-{i}"] = np.random.randn(512).tolist()
        self.service._cache_loaded = True

        mock_db = MagicMock()
        mock_event = MagicMock()
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_event
        mock_db.query.return_value = mock_query

        # Run multiple matches
        times = []
        for _ in range(10):
            test_embedding = np.random.randn(512).tolist()
            start = time.time()
            await self.service.match_or_create_entity(
                db=mock_db,
                event_id=f"event-{_}",
                embedding=test_embedding,
                entity_type="person",
            )
            times.append((time.time() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 50, f"Average matching time {avg_time:.2f}ms, expected <50ms"


class TestMatchEntityOnly:
    """Tests for match_entity_only method (Story P4-3.4: Context-Enhanced AI Prompts)."""

    def setup_method(self):
        """Setup test service."""
        reset_entity_service()
        self.service = EntityService()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_entities_exist(self):
        """Test returns None when no entities in cache."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        self.service._entity_cache = {}
        self.service._cache_loaded = True

        result = await self.service.match_entity_only(
            db=mock_db,
            embedding=[0.1] * 512,
            threshold=0.75,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_match_when_above_threshold(self):
        """Test returns match when similarity above threshold."""
        mock_db = MagicMock()

        # Create existing entity embedding
        existing_embedding = [0.1] * 512

        # Pre-load cache
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Mock entity lookup
        mock_entity = MagicMock()
        mock_entity.id = "existing-entity-id"
        mock_entity.entity_type = "person"
        mock_entity.name = "Known Person"
        mock_entity.first_seen_at = datetime.now(timezone.utc) - timedelta(days=7)
        mock_entity.last_seen_at = datetime.now(timezone.utc)
        mock_entity.occurrence_count = 5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entity

        # Test with identical embedding
        result = await self.service.match_entity_only(
            db=mock_db,
            embedding=[0.1] * 512,
            threshold=0.75,
        )

        assert result is not None
        assert result.entity_id == "existing-entity-id"
        assert result.name == "Known Person"
        assert result.is_new is False
        assert result.similarity_score >= 0.75

    @pytest.mark.asyncio
    async def test_returns_none_when_below_threshold(self):
        """Test returns None when no match above threshold."""
        mock_db = MagicMock()

        # Create existing entity with very different embedding
        existing_embedding = [0.9, 0.1] + [0.0] * 510

        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Test with very different embedding
        result = await self.service.match_entity_only(
            db=mock_db,
            embedding=[0.0, 0.0, 0.9] + [0.1] * 509,
            threshold=0.75,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_does_not_modify_database(self):
        """Test that match_entity_only is read-only."""
        mock_db = MagicMock()

        existing_embedding = [0.1] * 512
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        mock_entity = MagicMock()
        mock_entity.id = "existing-entity-id"
        mock_entity.entity_type = "person"
        mock_entity.name = None
        mock_entity.first_seen_at = datetime.now(timezone.utc)
        mock_entity.last_seen_at = datetime.now(timezone.utc)
        mock_entity.occurrence_count = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entity

        result = await self.service.match_entity_only(
            db=mock_db,
            embedding=[0.1] * 512,
            threshold=0.75,
        )

        # Verify no add() or commit() calls
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_respects_custom_threshold(self):
        """Test that custom threshold is respected."""
        mock_db = MagicMock()

        # Create existing entity
        existing_embedding = [1.0, 0.0] + [0.0] * 510
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        # Test embedding with moderate similarity (~0.7)
        test_embedding = [0.7, 0.7] + [0.0] * 510

        # Should NOT match with high threshold
        result_high = await self.service.match_entity_only(
            db=mock_db,
            embedding=test_embedding,
            threshold=0.95,
        )
        assert result_high is None

    @pytest.mark.asyncio
    async def test_returns_entity_occurrence_count_unchanged(self):
        """Test that occurrence count reflects current state, not incremented."""
        mock_db = MagicMock()

        existing_embedding = [0.1] * 512
        self.service._entity_cache = {"existing-entity-id": existing_embedding}
        self.service._cache_loaded = True

        mock_entity = MagicMock()
        mock_entity.id = "existing-entity-id"
        mock_entity.entity_type = "person"
        mock_entity.name = "Test"
        mock_entity.first_seen_at = datetime.now(timezone.utc) - timedelta(days=5)
        mock_entity.last_seen_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_entity.occurrence_count = 10  # Current count

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entity

        result = await self.service.match_entity_only(
            db=mock_db,
            embedding=[0.1] * 512,
            threshold=0.75,
        )

        # Should return current count, not incremented
        assert result.occurrence_count == 10
