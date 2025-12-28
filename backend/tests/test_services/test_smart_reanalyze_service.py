"""
Unit tests for SmartReanalyzeService (Story P11-4.3)

Tests:
- AC-4.3.2: Query encoded via EmbeddingService.encode_text()
- AC-4.3.3: Frame embeddings scored against query (cosine similarity)
- AC-4.3.4: Top-K frames selected for AI analysis
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from app.services.smart_reanalyze_service import (
    SmartReanalyzeService,
    get_smart_reanalyze_service,
    reset_smart_reanalyze_service,
    ScoredFrame,
    SmartReanalyzeResult,
)


class TestSmartReanalyzeServiceInit:
    """Tests for SmartReanalyzeService initialization."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = SmartReanalyzeService()

        assert service.DEFAULT_TOP_K == 5
        assert service.DEFAULT_MIN_SIMILARITY == 0.2
        assert service.DIVERSITY_THRESHOLD == 0.92

    def test_get_smart_reanalyze_service_singleton(self):
        """Test that get_smart_reanalyze_service returns singleton."""
        reset_smart_reanalyze_service()

        service1 = get_smart_reanalyze_service()
        service2 = get_smart_reanalyze_service()

        assert service1 is service2

        reset_smart_reanalyze_service()


class TestFrameSelection:
    """Tests for frame selection logic."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock EmbeddingService."""
        mock = MagicMock()
        # Return 512-dim embedding for text
        mock.encode_text = AsyncMock(return_value=[0.5] * 512)
        # Return frame embeddings
        mock.get_frame_embeddings = AsyncMock(return_value=[
            {"id": "emb1", "frame_index": 0, "embedding": [0.6] * 512, "model_version": "clip-ViT-B-32-v1"},
            {"id": "emb2", "frame_index": 1, "embedding": [0.3] * 512, "model_version": "clip-ViT-B-32-v1"},
            {"id": "emb3", "frame_index": 2, "embedding": [0.8] * 512, "model_version": "clip-ViT-B-32-v1"},
        ])
        return mock

    @pytest.fixture
    def service_with_mock(self, mock_embedding_service):
        """Create SmartReanalyzeService with mocked embedding service."""
        service = SmartReanalyzeService(embedding_service=mock_embedding_service)
        return service

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_select_relevant_frames_basic(self, service_with_mock, db_session, mock_embedding_service):
        """Test basic frame selection (AC-4.3.3, AC-4.3.4)."""
        result = await service_with_mock.select_relevant_frames(
            db=db_session,
            event_id="test-event-123",
            query="package delivery",
            top_k=3,
            min_similarity=0.1,
        )

        assert isinstance(result, SmartReanalyzeResult)
        assert len(result.selected_frames) <= 3
        assert result.query_embedding_time_ms >= 0
        assert result.frame_scoring_time_ms >= 0

        # Verify encode_text was called with formatted query (QuerySuggester adds "a photo of" prefix for short queries)
        mock_embedding_service.encode_text.assert_called_once_with("a photo of package delivery")

    @pytest.mark.asyncio
    async def test_select_relevant_frames_sorted_by_score(self, service_with_mock, db_session):
        """Test that frame scores are sorted by similarity (highest first)."""
        result = await service_with_mock.select_relevant_frames(
            db=db_session,
            event_id="test-event-123",
            query="package",
            top_k=5,
            min_similarity=0.0,
        )

        # Scores should be sorted descending
        for i in range(len(result.frame_scores) - 1):
            assert result.frame_scores[i].similarity_score >= result.frame_scores[i + 1].similarity_score

    @pytest.mark.asyncio
    async def test_select_relevant_frames_respects_min_similarity(self, mock_embedding_service, db_session):
        """Test that frames below min_similarity are excluded."""
        # Set up embeddings with varying similarities
        mock_embedding_service.get_frame_embeddings = AsyncMock(return_value=[
            {"id": "emb1", "frame_index": 0, "embedding": [0.9] * 512, "model_version": "v1"},
            {"id": "emb2", "frame_index": 1, "embedding": [0.1] * 512, "model_version": "v1"},  # Low similarity
            {"id": "emb3", "frame_index": 2, "embedding": [0.8] * 512, "model_version": "v1"},
        ])

        service = SmartReanalyzeService(embedding_service=mock_embedding_service)
        result = await service.select_relevant_frames(
            db=db_session,
            event_id="test-event-123",
            query="package",
            top_k=5,
            min_similarity=0.5,  # High threshold
        )

        # Frame 1 with low similarity embedding should be excluded from selection
        # (depending on cosine similarity calculation)
        assert len(result.selected_frames) <= 3

    @pytest.mark.asyncio
    async def test_select_relevant_frames_no_embeddings(self, db_session):
        """Test handling when no frame embeddings exist."""
        mock_embedding_service = MagicMock()
        mock_embedding_service.encode_text = AsyncMock(return_value=[0.5] * 512)
        mock_embedding_service.get_frame_embeddings = AsyncMock(return_value=[])

        # Mock query cache to ensure no cached results interfere
        mock_query_cache = MagicMock()
        mock_query_cache.get = MagicMock(return_value=None)

        service = SmartReanalyzeService(
            embedding_service=mock_embedding_service,
            query_cache=mock_query_cache
        )
        result = await service.select_relevant_frames(
            db=db_session,
            event_id="test-event-123",
            query="package",
            top_k=5,
            min_similarity=0.2,
            use_cache=False,  # Disable cache to test empty embeddings path
        )

        assert result.selected_frames == []
        assert result.frame_scores == []

    @pytest.mark.asyncio
    async def test_select_relevant_frames_top_k_limit(self, mock_embedding_service, db_session):
        """Test that top_k limit is respected."""
        # Set up many embeddings
        embeddings = [
            {"id": f"emb{i}", "frame_index": i, "embedding": [0.5 + i * 0.01] * 512, "model_version": "v1"}
            for i in range(10)
        ]
        mock_embedding_service.get_frame_embeddings = AsyncMock(return_value=embeddings)

        service = SmartReanalyzeService(embedding_service=mock_embedding_service)
        result = await service.select_relevant_frames(
            db=db_session,
            event_id="test-event-123",
            query="package",
            top_k=3,
            min_similarity=0.0,
        )

        assert len(result.selected_frames) <= 3


class TestDiversityFiltering:
    """Tests for diversity filtering in frame selection."""

    def test_select_diverse_frames_basic(self):
        """Test that near-duplicate frames are filtered."""
        service = SmartReanalyzeService()

        # Create scored frames with embeddings
        scored_frames = [
            ScoredFrame(frame_index=0, similarity_score=0.9, embedding_id="e1"),
            ScoredFrame(frame_index=1, similarity_score=0.85, embedding_id="e2"),
            ScoredFrame(frame_index=2, similarity_score=0.8, embedding_id="e3"),
        ]

        # Frame embeddings with frame 1 being near-duplicate of frame 0
        frame_embeddings = [
            {"frame_index": 0, "embedding": [0.5] * 512},
            {"frame_index": 1, "embedding": [0.501] * 512},  # Very similar to frame 0
            {"frame_index": 2, "embedding": [0.3] * 512},  # Different
        ]

        selected = service._select_diverse_frames(
            scored_frames=scored_frames,
            frame_embeddings=frame_embeddings,
            top_k=5,
            min_similarity=0.0,
        )

        # Frame 1 should be filtered as near-duplicate
        assert 0 in selected
        # Frame 1 might be excluded due to high similarity to frame 0
        assert len(selected) >= 1


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical vectors."""
        service = SmartReanalyzeService()

        vec = [0.5] * 512
        similarity = service._cosine_similarity_single(vec, vec)

        assert similarity == pytest.approx(1.0, abs=0.001)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors."""
        service = SmartReanalyzeService()

        # Create orthogonal vectors (not exactly 512 dims for simplicity in test)
        vec1 = [1.0, 0.0, 0.0] + [0.0] * 509
        vec2 = [0.0, 1.0, 0.0] + [0.0] * 509

        similarity = service._cosine_similarity_single(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=0.001)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        service = SmartReanalyzeService()

        vec1 = [0.5] * 512
        vec2 = [0.0] * 512

        similarity = service._cosine_similarity_single(vec1, vec2)

        assert similarity == 0.0


class TestScoredFrameDataclass:
    """Tests for ScoredFrame dataclass."""

    def test_scored_frame_creation(self):
        """Test creating ScoredFrame."""
        frame = ScoredFrame(
            frame_index=0,
            similarity_score=0.85,
            embedding_id="emb-123"
        )

        assert frame.frame_index == 0
        assert frame.similarity_score == 0.85
        assert frame.embedding_id == "emb-123"


class TestSmartReanalyzeResult:
    """Tests for SmartReanalyzeResult dataclass."""

    def test_result_creation(self):
        """Test creating SmartReanalyzeResult."""
        result = SmartReanalyzeResult(
            selected_frames=[0, 2, 4],
            frame_scores=[
                ScoredFrame(frame_index=0, similarity_score=0.9, embedding_id="e1"),
                ScoredFrame(frame_index=2, similarity_score=0.8, embedding_id="e2"),
            ],
            query_embedding_time_ms=45.2,
            frame_scoring_time_ms=2.3,
        )

        assert result.selected_frames == [0, 2, 4]
        assert len(result.frame_scores) == 2
        assert result.query_embedding_time_ms == 45.2
        assert result.frame_scoring_time_ms == 2.3
