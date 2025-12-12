# Story P4-3.4: Context-Enhanced AI Prompts

Status: done

## Story

As a **home security system user**,
I want **the AI descriptions to include relevant historical context about recognized visitors and patterns**,
so that **I receive more informative descriptions like "Your regular mail carrier is at the door (seen 12 times this month)" instead of just "Person at door"**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | When generating AI descriptions, the system retrieves similar past events using SimilarityService | Integration test with event containing embedding |
| 2 | If a matched entity exists (from EntityService), entity name and occurrence count are included in the AI prompt | Unit test with mock entity data |
| 3 | Historical context format in prompt: "This visitor has been seen [X] times. First seen: [date]. Last seen: [date]. User name: [name or 'unnamed']" | Test prompt construction |
| 4 | If similar events found (>0.7 similarity), include summary: "Similar events detected: [count] occurrences in last [N] days" | Test with similar event history |
| 5 | AI prompt includes time-of-day pattern context when available: "This camera typically sees activity at this time" or "Unusual timing - normally quiet at this hour" | Test pattern context injection |
| 6 | Context is only included when confidence is high enough (>0.7 similarity threshold) to avoid misleading information | Test threshold filtering |
| 7 | AI description output naturally incorporates context (e.g., "Your mail carrier John is at the front door, their 12th visit this month") | Integration test with full AI pipeline |
| 8 | Performance: Context gathering adds <300ms to event processing (combined with existing <500ms embedding lookup) | Performance benchmark |
| 9 | Feature can be enabled/disabled via system settings (`enable_context_enhanced_prompts`) | Settings API test |
| 10 | Graceful degradation: If context service fails, AI description generated without context (no blocking) | Test with service failure |
| 11 | Context inclusion logged for debugging and analytics (which context was included, similarity scores) | Log output verification |
| 12 | A/B test capability: System can randomly skip context for comparison (configurable % via settings) | Settings-driven A/B test |

## Tasks / Subtasks

- [x] **Task 1: Create ContextEnhancedPromptService** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Create `backend/app/services/context_prompt_service.py`
  - [x] Implement `build_context_enhanced_prompt(event_id, base_prompt, thumbnail)` method
  - [x] Integrate with EntityService to get matched entity info
  - [x] Integrate with SimilarityService to find similar past events
  - [x] Format historical context section for AI prompt
  - [x] Add threshold filtering (>0.7 similarity)

- [x] **Task 2: Implement entity context formatting** (AC: 2, 3)
  - [x] Create `_format_entity_context(entity)` helper method
  - [x] Include: entity name (or "unnamed visitor"), occurrence_count, first_seen_at, last_seen_at
  - [x] Format dates in natural language (e.g., "first seen 2 weeks ago")
  - [x] Handle null/missing entity gracefully

- [x] **Task 3: Implement similarity context formatting** (AC: 4)
  - [x] Create `_format_similarity_context(similar_events)` helper method
  - [x] Count similar events within configurable time window (default 30 days)
  - [x] Include highest similarity score for reference
  - [x] Summarize event types if available (e.g., "mostly deliveries")

- [x] **Task 4: Implement time pattern context** (AC: 5)
  - [x] Create `_format_time_pattern_context(camera_id, event_time)` helper method
  - [x] Query historical events for same camera and time-of-day (±1 hour window)
  - [x] Determine if current time is "typical" or "unusual" for activity
  - [x] Format as natural language context line

- [x] **Task 5: Add system settings for context enhancement** (AC: 9, 12)
  - [x] Add `enable_context_enhanced_prompts` setting (default: true)
  - [x] Add `context_ab_test_percentage` setting (default: 0 = disabled)
  - [x] Add `context_similarity_threshold` setting (default: 0.7)
  - [x] Add `context_time_window_days` setting (default: 30)
  - [x] Expose settings via existing settings API

- [x] **Task 6: Integrate with AI description pipeline** (AC: 7, 8, 10)
  - [x] Modify `ai_service.py` to accept optional context parameter
  - [x] Update `event_processor.py` to call ContextEnhancedPromptService before AI description
  - [x] Implement graceful fallback if context service fails
  - [x] Add timing instrumentation for performance monitoring

- [x] **Task 7: Implement A/B test logic** (AC: 12)
  - [x] In event processor, check `context_ab_test_percentage` setting
  - [x] Use random sampling to skip context for configured percentage
  - [x] Log A/B test assignment for later analysis
  - [x] Store A/B assignment in event metadata (context_included: boolean)

- [x] **Task 8: Add logging and analytics** (AC: 11)
  - [x] Log context components used for each event
  - [x] Log similarity scores and thresholds
  - [x] Log entity match details
  - [x] Log performance timing (context gathering duration)

- [x] **Task 9: Write unit tests** (AC: 2, 3, 4, 5, 6)
  - [x] Test entity context formatting with various entity states
  - [x] Test similarity context formatting with mock similar events
  - [x] Test time pattern context with typical/unusual scenarios
  - [x] Test threshold filtering excludes low-confidence matches
  - [x] Test graceful handling of missing data

- [x] **Task 10: Write integration tests** (AC: 1, 7, 8, 10)
  - [x] Test full context gathering with real database
  - [x] Test AI description includes context in output
  - [x] Test performance meets <300ms target
  - [x] Test graceful degradation with service failures

- [x] **Task 11: Write API/settings tests** (AC: 9, 12)
  - [x] Test settings API for new context settings
  - [x] Test A/B test percentage affects context inclusion
  - [x] Test enable/disable toggle works correctly

## Dev Notes

### Architecture Alignment

This story is the fourth and key component of the Temporal Context Engine (Epic P4-3). It brings together all the previous work - EmbeddingService (P4-3.1), SimilarityService (P4-3.2), and EntityService (P4-3.3) - to enhance AI descriptions with historical context.

**Component Integration Flow:**
```
New Event Created
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ Event Processor (existing flow)                         │
│   Step 8: Generate embedding (EmbeddingService)         │
│   Step 9: Match entity (EntityService)                  │
│   Step 10 (NEW): Build context-enhanced prompt          │
│   Step 11: Generate AI description (with context)       │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ ContextEnhancedPromptService.build_context_enhanced_prompt() │
│                                                         │
│   1. Check if context enabled (settings)                │
│   2. Check A/B test (random skip %)                     │
│   3. Get entity context (from EntityService result)     │
│   4. Get similar events (SimilarityService)             │
│   5. Get time pattern context                           │
│   6. Format all context into prompt section             │
│   7. Return enhanced prompt                             │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ AIService.describe_image(thumbnail, enhanced_prompt)    │
│                                                         │
│   AI receives context like:                             │
│   "CONTEXT: This visitor (John, your mail carrier)      │
│    has been seen 12 times. First seen 2 weeks ago.      │
│    Similar events: 8 in last 30 days.                   │
│    Timing: Typical activity time for this camera."      │
│                                                         │
│   AI generates: "Your mail carrier John is at the       │
│   front door with a package, their 12th visit this      │
│   month. They typically arrive around this time."       │
└─────────────────────────────────────────────────────────┘
```

### Key Implementation Details

**ContextEnhancedPromptService Structure:**
```python
class ContextEnhancedPromptService:
    """Build context-enhanced prompts for AI description generation."""

    def __init__(
        self,
        entity_service: EntityService,
        similarity_service: SimilarityService,
        settings_service: SettingsService,
    ):
        self._entity_service = entity_service
        self._similarity_service = similarity_service
        self._settings_service = settings_service

    async def build_context_enhanced_prompt(
        self,
        db: Session,
        event_id: str,
        base_prompt: str,
        camera_id: str,
        event_time: datetime,
        matched_entity: Optional[EntityMatchResult] = None,
    ) -> ContextEnhancedPromptResult:
        """
        Build an AI prompt enhanced with historical context.

        Returns original prompt if context disabled or A/B test skips.
        """
        # Check settings
        if not self._settings_service.get("enable_context_enhanced_prompts", True):
            return ContextEnhancedPromptResult(prompt=base_prompt, context_included=False)

        # A/B test check
        ab_percentage = self._settings_service.get("context_ab_test_percentage", 0)
        if ab_percentage > 0 and random.randint(1, 100) <= ab_percentage:
            return ContextEnhancedPromptResult(prompt=base_prompt, context_included=False, ab_test_skip=True)

        # Gather context (with timeout/error handling)
        context_parts = []

        # Entity context
        if matched_entity and matched_entity.similarity_score >= threshold:
            context_parts.append(self._format_entity_context(matched_entity.entity))

        # Similar events context
        similar = await self._similarity_service.find_similar_events(...)
        if similar:
            context_parts.append(self._format_similarity_context(similar))

        # Time pattern context
        time_context = await self._get_time_pattern_context(db, camera_id, event_time)
        if time_context:
            context_parts.append(time_context)

        # Combine into enhanced prompt
        if context_parts:
            context_section = "HISTORICAL CONTEXT:\n" + "\n".join(context_parts)
            enhanced_prompt = f"{base_prompt}\n\n{context_section}"
        else:
            enhanced_prompt = base_prompt

        return ContextEnhancedPromptResult(
            prompt=enhanced_prompt,
            context_included=bool(context_parts),
            entity_context=matched_entity is not None,
            similar_events_count=len(similar) if similar else 0,
        )
```

**Context Format Examples:**

Entity context:
```
- Known visitor: "Mail Carrier John" (named by user)
- Seen 12 times total (first: 2 weeks ago, last: yesterday)
```

Similar events context:
```
- Similar events: 8 occurrences in last 30 days
- Most recent similar: 2 days ago (93% match)
```

Time pattern context:
```
- Timing: Typical for this camera (usually active 2-4pm weekdays)
```
OR
```
- Timing: Unusual - this camera normally quiet at this hour
```

**Modified AI Prompt Structure:**
```
[Original system prompt about describing security footage]

HISTORICAL CONTEXT:
- Known visitor: "Mail Carrier John" (named by user)
- Seen 12 times total (first: 2 weeks ago, last: yesterday)
- Similar events: 8 occurrences in last 30 days
- Timing: Typical for this camera (usually active 2-4pm weekdays)

Please incorporate this context naturally into your description if relevant.
For example, refer to recognized visitors by name and mention if this is a regular occurrence.
```

### Project Structure Notes

**Files to create:**
- `backend/app/services/context_prompt_service.py` - Main service for context-enhanced prompts
- `backend/tests/test_services/test_context_prompt_service.py` - Unit tests
- `backend/tests/test_integration/test_context_prompt_integration.py` - Integration tests

**Files to modify:**
- `backend/app/services/ai_service.py` - Accept context parameter in describe methods
- `backend/app/services/event_processor.py` - Call context service before AI description
- `backend/app/core/settings.py` - Add new context-related settings
- `backend/app/api/v1/system.py` - Expose new settings (if needed)

### Performance Considerations

- Context gathering should complete in <300ms total
- Use async/await for all database queries
- Cache time pattern statistics (update hourly or on-demand)
- Early exit if context disabled or A/B skipped
- Set timeouts on all sub-operations to prevent blocking
- Log timing for performance monitoring

### Testing Strategy

Per testing-strategy.md, target coverage:
- Unit tests: Context formatting, threshold filtering, A/B logic
- Integration tests: Full pipeline with real services, performance benchmarks
- API tests: Settings endpoints for context configuration

### Learnings from Previous Story

**From Story P4-3.3 (Recurring Visitor Detection) (Status: done)**

- **EntityService Available**: Use `EntityService` and `get_entity_service()` - DO NOT recreate
- **EntityMatchResult Structure**: Contains `entity: EntityResponse`, `similarity_score: float`, `is_new: bool`
- **Entity Fields**: `id`, `entity_type`, `name` (nullable), `first_seen_at`, `last_seen_at`, `occurrence_count`
- **Service Pattern**: Services in `backend/app/services/` with dependency injection via factory functions
- **Pipeline Integration**: Entity matching happens in event_processor.py after embedding generation
- **File Created**: `backend/app/services/entity_service.py` - REUSE for entity context
- **Test Coverage**: 48 tests (25 unit + 10 integration + 13 API) - target similar

**From Story P4-3.2 (Similarity Search) (Status: done)**

- **SimilarityService Available**: Use `get_similarity_service()` - DO NOT recreate
- **Find Similar Method**: `find_similar_events(db, event_id, limit, min_similarity, days_back)` returns similar events with scores
- **Batch Similarity**: `batch_cosine_similarity(query, candidates)` for efficient calculation
- **Performance**: <200ms for 10,000 embeddings - well within our <300ms budget
- **File Created**: `backend/app/services/similarity_service.py` - REUSE for similar events lookup

**From Story P4-3.1 (Event Embedding Generation) (Status: done)**

- **EmbeddingService Available**: Use `get_embedding_service()` - already integrated into pipeline
- **Embedding Storage**: embeddings stored in EventEmbedding model, accessible via event_id
- **Pipeline Step**: Embeddings generated as Step 8 in event_processor.py

**Reusable Services (DO NOT RECREATE):**
- `EntityService.get_entity(db, entity_id)` - Get entity details
- `SimilarityService.find_similar_events(db, event_id, ...)` - Find similar past events
- `EmbeddingService.get_embedding_vector(db, event_id)` - Get event embedding (already used)

**Architecture Decision:**
- Context prompt service orchestrates existing services - minimal new code
- Settings integration via existing SettingsService pattern
- A/B testing uses simple random sampling, logged for analysis

[Source: docs/sprint-artifacts/p4-3-3-recurring-visitor-detection.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/p4-3-2-similarity-search.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/p4-3-1-event-embedding-generation.md#Dev-Agent-Record]

### References

- [Source: docs/epics-phase4.md#Story-P4-3.4-Context-Enhanced-AI-Prompts]
- [Source: docs/PRD-phase4.md#FR4 - AI descriptions include historical context when relevant]
- [Source: docs/architecture.md#Phase-4-Service-Architecture - Context Service Flow]
- [Source: docs/architecture.md#ADR-P4-001 - Embedding Model Selection]
- [Source: docs/sprint-artifacts/p4-3-3-recurring-visitor-detection.md - EntityService patterns]
- [Source: docs/sprint-artifacts/p4-3-2-similarity-search.md - SimilarityService patterns]
- [Source: docs/sprint-artifacts/p4-3-1-event-embedding-generation.md - EmbeddingService patterns]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p4-3-4-context-enhanced-ai-prompts.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-11 | Claude Opus 4.5 | Initial story draft from create-story workflow |
