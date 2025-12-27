# Epic Technical Specification: Query-Adaptive Optimization

Date: 2025-12-26
Author: Brent
Epic ID: P12-4
Status: Draft

---

## Overview

Epic P12-4 enhances the Phase 11 query-adaptive frame selection with batch embedding processing, diversity filtering, and improved re-analysis UX. This builds upon the CLIP-based text-to-frame matching foundation to provide more efficient and accurate frame selection for targeted event re-analysis.

**PRD Reference:** docs/PRD-phase12.md (FRs 29-38)
**Architecture:** docs/architecture/phase-12-additions.md
**Foundation:** Phase 11 Story P11-4.1-4.3 (EmbeddingService, FrameEmbedding, smart-reanalyze)

## Objectives and Scope

**In Scope:**
- Implement batch embedding generation (40% overhead reduction)
- Add diversity filtering to prevent near-duplicate frame selection
- Integrate quality scoring with relevance in frame ranking
- Implement query result caching with TTL
- Add query suggestions based on event type
- Enhance re-analyze modal with relevance scores display
- Auto-format single-word queries

**Out of Scope:**
- CLIP model training/fine-tuning
- Frame embedding storage redesign (use P11 infrastructure)
- Multi-modal query input (voice, image)

## System Architecture Alignment

**Components Affected:**
- `backend/app/services/query_adaptive/batch_embedder.py` - New service
- `backend/app/services/query_adaptive/diversity_filter.py` - New service
- `backend/app/services/query_adaptive/query_cache.py` - New service
- `backend/app/services/embedding_service.py` - Extend for batch
- `backend/app/api/v1/events.py` - Enhance smart-reanalyze endpoint
- `frontend/components/events/ReanalyzeModal.tsx` - Enhanced UI

**Architecture Constraints:**
- Batch processing must be 40% faster than sequential
- Diversity filtering adds <10ms overhead
- Query cache TTL: 5 minutes
- Must maintain backward compatibility with P11 endpoints

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs |
|--------|----------------|--------|---------|
| BatchEmbedder | Batch frame embedding | List[frames] | List[embeddings] |
| DiversityFilter | Filter near-duplicates | embeddings, scores | selected indices |
| QueryCache | Cache query results | event_id, query | cached frames |
| QuerySuggester | Generate query hints | event type | suggested queries |
| EmbeddingService | CLIP encoding | frames/text | embeddings |

### Data Models and Contracts

**Query Result Cache:**

```python
# backend/app/services/query_adaptive/query_cache.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class CachedQueryResult:
    event_id: str
    query: str
    frame_indices: List[int]
    relevance_scores: List[float]
    cached_at: datetime
    ttl_seconds: int = 300  # 5 minutes

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.cached_at + timedelta(seconds=self.ttl_seconds)

class QueryCache:
    """In-memory cache for query results with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, CachedQueryResult] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, event_id: str, query: str) -> Optional[CachedQueryResult]:
        """Get cached result if not expired."""
        key = self._make_key(event_id, query)
        result = self._cache.get(key)
        if result and not result.is_expired:
            return result
        elif result:
            del self._cache[key]
        return None

    def set(self, event_id: str, query: str, frame_indices: List[int], scores: List[float]):
        """Cache query result."""
        key = self._make_key(event_id, query)
        self._cache[key] = CachedQueryResult(
            event_id=event_id,
            query=query,
            frame_indices=frame_indices,
            relevance_scores=scores,
            cached_at=datetime.utcnow(),
            ttl_seconds=self.ttl_seconds,
        )

    def _make_key(self, event_id: str, query: str) -> str:
        return f"{event_id}:{query.lower().strip()}"
```

**Enhanced Response Schema:**

```python
# backend/app/schemas/events.py

class FrameWithScore(BaseModel):
    frame_index: int
    relevance_score: float  # 0-100
    quality_score: float    # 0-100
    combined_score: float   # 0-100
    thumbnail_url: str
    timestamp_offset_ms: int

class SmartReanalyzeResponse(BaseModel):
    event_id: str
    query: str
    formatted_query: str  # After auto-formatting
    selected_frames: List[FrameWithScore]
    total_frames_analyzed: int
    selection_time_ms: float
    cached: bool
    suggested_queries: List[str]
```

### APIs and Interfaces

```yaml
POST /api/v1/events/{event_id}/smart-reanalyze:
  summary: Query-adaptive frame selection for re-analysis
  requestBody:
    content:
      application/json:
        schema:
          type: object
          required: [query]
          properties:
            query:
              type: string
              description: Natural language query
            top_k:
              type: integer
              default: 5
              description: Number of frames to select
            use_cache:
              type: boolean
              default: true
            comparison_mode:
              type: boolean
              default: false
              description: Include uniform selection for A/B comparison
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/SmartReanalyzeResponse'

GET /api/v1/events/{event_id}/query-suggestions:
  summary: Get suggested queries for event
  responses:
    200:
      content:
        application/json:
          schema:
            type: object
            properties:
              suggestions:
                type: array
                items:
                  type: string
```

### Workflows and Sequencing

**Batch Embedding Flow:**

```
Event Video Frames (N frames)
        │
        ▼
┌───────────────────────────────────────┐
│         BatchEmbedder.embed_batch()   │
│                                       │
│   ┌─────────────────────────────────┐ │
│   │ Batch 1 (8 frames)              │ │
│   │ ─► Preprocess all               │ │
│   │ ─► Stack into tensor            │ │
│   │ ─► Single CLIP forward pass     │ │
│   │ ─► Split embeddings             │ │
│   └─────────────────────────────────┘ │
│                                       │
│   ┌─────────────────────────────────┐ │
│   │ Batch 2 (8 frames)              │ │
│   │ ─► Same process                 │ │
│   └─────────────────────────────────┘ │
│                                       │
│   ... repeat for all batches          │
│                                       │
│   Result: ~40% faster than sequential │
└───────────────────────────────────────┘
        │
        ▼
    List[embeddings]
```

**Complete Selection Flow:**

```
Query: "Is this a delivery person?"
        │
        ▼
┌─────────────────────────────────────┐
│    1. Format Query                  │
│    ─► "a photo of a delivery person"│
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    2. Check Cache                   │
│    ─► Cache hit? Return cached      │
│    ─► Cache miss? Continue          │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    3. Encode Query                  │
│    ─► CLIP text encoder             │
│    ─► Query embedding (512-dim)     │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    4. Load Frame Embeddings         │
│    ─► From FrameEmbedding table     │
│    ─► Or generate via BatchEmbedder │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    5. Calculate Relevance Scores    │
│    ─► Cosine similarity             │
│    ─► Scale to 0-100                │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    6. Get Quality Scores            │
│    ─► From stored frame metadata    │
│    ─► Blur, exposure scores         │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    7. Combined Scoring              │
│    combined = relevance*0.7 +       │
│               quality*0.3           │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    8. Diversity Filter              │
│    ─► Sort by combined score        │
│    ─► Greedy selection with         │
│       similarity threshold (0.92)   │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    9. Cache Result                  │
│    ─► Store with 5-min TTL          │
└─────────────────────────────────────┘
        │
        ▼
    Selected Frames with Scores
```

**Service Implementation:**

```python
# backend/app/services/query_adaptive/batch_embedder.py

class BatchEmbedder:
    """Batch processing for frame embeddings with 40%+ overhead reduction."""

    BATCH_SIZE = 8  # Optimal for CLIP

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def embed_frames_batch(
        self,
        frames: List[np.ndarray],
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple frames in batches.

        ~40% faster than sequential processing.
        """
        embeddings = []
        start_time = time.time()

        for i in range(0, len(frames), self.BATCH_SIZE):
            batch = frames[i:i + self.BATCH_SIZE]
            batch_embeddings = await self._process_batch(batch)
            embeddings.extend(batch_embeddings)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Batch embedded {len(frames)} frames in {duration_ms:.1f}ms",
            extra={"frame_count": len(frames), "duration_ms": duration_ms}
        )

        return embeddings

    async def _process_batch(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Process a batch of frames through CLIP."""
        import torch

        # Preprocess all frames
        preprocessed = [self.embedding_service.preprocess(f) for f in frames]

        # Stack into batch tensor
        batch_tensor = torch.stack(preprocessed)

        # Single forward pass for batch
        with torch.no_grad():
            embeddings = self.embedding_service.model.encode_image(batch_tensor)

        return [e.cpu().numpy() for e in embeddings]
```

```python
# backend/app/services/query_adaptive/diversity_filter.py

class DiversityFilter:
    """Prevents selection of near-duplicate frames."""

    SIMILARITY_THRESHOLD = 0.92

    def filter_diverse_frames(
        self,
        embeddings: List[np.ndarray],
        scores: List[float],
        top_k: int = 5,
    ) -> List[int]:
        """
        Select top-k frames while maintaining diversity.

        Uses greedy selection: pick highest score, then filter similar.
        """
        if len(embeddings) <= top_k:
            return list(range(len(embeddings)))

        # Sort by score descending
        scored_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        selected = []
        selected_embeddings = []

        for idx in scored_indices:
            if len(selected) >= top_k:
                break

            # Check similarity to already selected
            is_diverse = True
            for sel_emb in selected_embeddings:
                similarity = self._cosine_similarity(embeddings[idx], sel_emb)
                if similarity > self.SIMILARITY_THRESHOLD:
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(idx)
                selected_embeddings.append(embeddings[idx])

        return selected

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

```python
# backend/app/services/query_adaptive/query_suggester.py

class QuerySuggester:
    """Generate query suggestions based on event type."""

    SUGGESTIONS = {
        "person": [
            "Is this a delivery person?",
            "What are they carrying?",
            "Are they wearing a uniform?",
            "Is this someone I know?",
        ],
        "vehicle": [
            "What color is the vehicle?",
            "Is it parked or moving?",
            "What type of vehicle?",
            "Can you read the license plate?",
        ],
        "package": [
            "What company is the package from?",
            "How large is the package?",
            "Where was it placed?",
        ],
        "animal": [
            "What type of animal?",
            "Is it a pet or wildlife?",
        ],
    }

    def get_suggestions(
        self,
        smart_detection_type: Optional[str],
        objects_detected: List[str],
    ) -> List[str]:
        """Get relevant query suggestions."""
        suggestions = []

        # Primary suggestions from smart detection
        if smart_detection_type and smart_detection_type in self.SUGGESTIONS:
            suggestions.extend(self.SUGGESTIONS[smart_detection_type][:3])

        # Secondary from detected objects
        for obj in objects_detected:
            obj_lower = obj.lower()
            for key, sug_list in self.SUGGESTIONS.items():
                if key in obj_lower:
                    suggestions.extend(sug_list[:2])
                    break

        # Dedupe while preserving order
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique[:5]

    @staticmethod
    def format_query(query: str) -> str:
        """Auto-format single-word queries for better CLIP matching."""
        query = query.strip()

        # Single word or very short → wrap with template
        if len(query.split()) <= 2 and not query.startswith("a photo"):
            return f"a photo of {query}"

        return query
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Batch embedding | 40% faster | vs sequential baseline |
| Diversity filter | <10ms | Additional overhead |
| Cache hit | <5ms | Latency for cached results |
| Total selection | <500ms | End-to-end for 20 frames |

### Security

- Query strings sanitized before logging
- No PII in cache keys
- Cache cleared on event deletion

### Reliability/Availability

- Graceful fallback to sequential if batch fails
- Quality scores optional (skip if not available)
- Cache miss doesn't fail request

### Observability

- Log batch processing times
- Metric: `frame_selection_duration_seconds{cached}` histogram
- Metric: `diversity_filter_frames_removed_total` counter
- Alert on selection times >1s

## Dependencies and Integrations

**Backend Dependencies:**
```
numpy>=1.26.0       # Batch operations
torch>=2.0.0        # CLIP inference (existing)
transformers        # CLIP model (existing)
```

**Integration Points:**
- EmbeddingService (P11-4.1) - CLIP encoding
- FrameEmbedding model (P11-4.2) - Stored embeddings
- FrameExtractionService (P3) - Quality scores

## Acceptance Criteria (Authoritative)

1. **AC1:** Batch embedding processes 8 frames per batch with 40% overhead reduction
2. **AC2:** Diversity filter prevents frames with >92% similarity from both being selected
3. **AC3:** Combined score = (relevance * 0.7) + (quality * 0.3)
4. **AC4:** Query cache returns results in <5ms for cache hits
5. **AC5:** Cache entries expire after 5 minutes
6. **AC6:** Single-word queries auto-formatted with "a photo of {query}"
7. **AC7:** Query suggestions appear based on event smart_detection_type
8. **AC8:** Re-analyze modal shows relevance score (0-100) for each frame
9. **AC9:** A/B comparison mode shows uniform vs adaptive selection
10. **AC10:** Total selection time logged and <500ms for 20 frames

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| AC1 | Workflows | BatchEmbedder | Benchmark: batch vs sequential |
| AC2 | Workflows | DiversityFilter | Two 95% similar frames → 1 selected |
| AC3 | Workflows | Combined scoring | Unit test: weight calculation |
| AC4 | Data Models | QueryCache.get() | Cache hit timing test |
| AC5 | Data Models | CachedQueryResult.is_expired | 6-minute-old cache miss |
| AC6 | Workflows | QuerySuggester.format_query | "dog" → "a photo of dog" |
| AC7 | APIs | GET /query-suggestions | Suggestions for person event |
| AC8 | APIs | SmartReanalyzeResponse | Verify relevance_score field |
| AC9 | APIs | comparison_mode param | Both results returned |
| AC10 | Performance | Full endpoint | Response time benchmark |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1:** CLIP model memory usage with large batches
  - *Mitigation:* Batch size 8, monitor GPU/CPU memory
- **R2:** Diversity threshold may over-filter diverse frames
  - *Mitigation:* Make threshold configurable, default 0.92

**Assumptions:**
- **A1:** P11-4 EmbeddingService and FrameEmbedding are operational
- **A2:** Frame quality scores available from P3/P9 implementation
- **A3:** Event has stored frames available for embedding

**Open Questions:**
- **Q1:** Should cache be shared across users? (Suggested: Yes, event-level cache)
- **Q2:** Should we persist cache to Redis? (Suggested: In-memory for MVP)

## Test Strategy Summary

**Unit Tests:**
- `test_batch_embedder_performance` - 40% faster benchmark
- `test_diversity_filter_removes_duplicates` - Similarity threshold
- `test_query_cache_ttl` - Expiration logic
- `test_query_formatting` - Single word formatting
- `test_combined_scoring` - Weight calculation

**Integration Tests:**
- `test_smart_reanalyze_with_cache` - Full flow with caching
- `test_query_suggestions_for_event` - Suggestions endpoint

**Frontend Tests:**
- `ReanalyzeModal.test.tsx` - Score display, suggestions

**Performance Tests:**
- Batch vs sequential embedding comparison
- End-to-end selection time for 20 frames

---

**Created:** 2025-12-26
**Stories:** P12-4.1, P12-4.2, P12-4.3, P12-4.4, P12-4.5
