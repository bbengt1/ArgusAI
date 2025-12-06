# Story P3-2.5: Track Token Usage for Multi-Image Requests

Status: done

## Story

As a **system administrator**,
I want **accurate token tracking for multi-image requests**,
So that **cost estimates remain accurate and I can monitor AI usage effectively**.

## Acceptance Criteria

1. **AC1:** Given a multi-image AI request completes, when usage is tracked, then AIUsage record includes total tokens (input + output) and token count reflects all images sent
2. **AC2:** Given OpenAI vision request with 5 images, when response is received, then `usage.prompt_tokens` and `usage.completion_tokens` are recorded and stored in ai_usage table with `analysis_mode="multi_frame"`
3. **AC3:** Given provider doesn't return token counts (some Gemini responses), when usage is tracked, then estimate tokens based on image count and response length and flag estimate with `is_estimated: true`
4. **AC4:** Given cost tracking is enabled, when multi-image request completes, then estimated cost is calculated using provider's per-token rates and cost is stored with the AIUsage record

## Tasks / Subtasks

- [x] **Task 1: Add analysis_mode field to AIUsage model** (AC: 2)
  - [x] 1.1 Add `analysis_mode` column to AIUsage model (String, nullable, values: "single_image", "multi_frame")
  - [x] 1.2 Add `is_estimated` column to track estimated vs actual token counts (Boolean, default False)
  - [x] 1.3 Create Alembic migration for new columns
  - [x] 1.4 Apply migration and verify schema update

- [x] **Task 2: Update AIService to track multi-image tokens** (AC: 1, 2)
  - [x] 2.1 Modify `_track_usage()` method to accept `analysis_mode` parameter
  - [x] 2.2 Update all provider `generate_multi_image_description()` methods to pass analysis_mode="multi_frame"
  - [x] 2.3 Ensure single-image calls pass analysis_mode="single_image"
  - [x] 2.4 Verify token counts from OpenAI/Claude/Grok responses are captured correctly

- [x] **Task 3: Implement token estimation for providers without counts** (AC: 3)
  - [x] 3.1 Add token estimation constants:
    - OpenAI: ~85 tokens/image (low-res), ~765 tokens/image (high-res)
    - Claude: ~1,334 tokens/image
    - Gemini: ~258 tokens/image (estimate)
  - [x] 3.2 Implement `_estimate_image_tokens()` method in AIService
  - [x] 3.3 Apply estimation when provider response lacks token counts (particularly Gemini)
  - [x] 3.4 Set `is_estimated=True` when using estimates

- [x] **Task 4: Implement cost calculation for multi-image** (AC: 4)
  - [x] 4.1 Define cost rates per provider (from architecture.md CostTracker):
    - OpenAI GPT-4o-mini: $0.00015/1K input, $0.00060/1K output
    - Claude 3 Haiku: $0.00025/1K input, $0.00125/1K output
    - Gemini Flash: $0.000075/1K input, $0.0003/1K output
    - Grok: $0.00005/1K input, $0.00010/1K output (estimate)
  - [x] 4.2 Update `_calculate_cost()` method to use provider-specific rates
  - [x] 4.3 Ensure cost is stored with AIUsage record

- [x] **Task 5: Write unit tests** (AC: All)
  - [x] 5.1 Test AIUsage model includes new fields (analysis_mode, is_estimated)
  - [x] 5.2 Test multi-image tracking sets analysis_mode="multi_frame"
  - [x] 5.3 Test single-image tracking sets analysis_mode="single_image"
  - [x] 5.4 Test token estimation when provider returns no counts
  - [x] 5.5 Test is_estimated flag is set correctly
  - [x] 5.6 Test cost calculation for each provider
  - [x] 5.7 Test usage stats aggregation includes new fields

## Dev Notes

### Architecture References

- **AIUsage Model**: `backend/app/models/ai_usage.py` - Current schema lacks analysis_mode
- **AIService Usage Tracking**: `backend/app/services/ai_service.py` - `_track_usage()` method around line 1960
- **Cost Rates**: Reference architecture.md CostTracker section for per-token pricing
- [Source: docs/architecture.md#CostTracker]
- [Source: docs/epics-phase3.md#Story-P3-2.5]

### Project Structure Notes

- Modify existing model: `backend/app/models/ai_usage.py`
- Modify existing service: `backend/app/services/ai_service.py`
- Add Alembic migration: `backend/alembic/versions/xxx_add_analysis_mode_to_ai_usage.py`
- Add tests to: `backend/tests/test_services/test_ai_service.py`

### Implementation Guidance

1. **AIUsage Model Changes:**
   ```python
   # Add to AIUsage model
   analysis_mode = Column(String(20), nullable=True, index=True)  # "single_image", "multi_frame"
   is_estimated = Column(Boolean, nullable=False, default=False)  # True if tokens are estimated
   ```

2. **Token Estimation Constants:**
   ```python
   # Approximate tokens per image by provider
   TOKENS_PER_IMAGE = {
       "openai": {"low_res": 85, "high_res": 765},
       "claude": 1334,
       "gemini": 258,
       "grok": 85  # OpenAI-compatible, same as OpenAI
   }
   ```

3. **Cost Rates (USD per 1K tokens):**
   ```python
   COST_RATES = {
       "openai": {"input": 0.00015, "output": 0.00060},
       "claude": {"input": 0.00025, "output": 0.00125},
       "gemini": {"input": 0.000075, "output": 0.0003},
       "grok": {"input": 0.00005, "output": 0.00010}
   }
   ```

### Learnings from Previous Story

**From Story p3-2-4-create-multi-frame-prompts-optimized-for-sequences (Status: done)**

- **Multi-Image Infrastructure Ready**: `describe_images()` method and all provider implementations complete
- **AIResult Includes Tokens**: Each provider returns `AIResult.tokens_used` - use this for tracking
- **Existing Usage Tracking**: `_track_usage()` at line 1960 already logs to ai_usage table
- **Provider Pattern**: All 4 providers (OpenAI, Grok, Claude, Gemini) inherit from AIProviderBase
- **Test Patterns**: Use existing TestMultiImage* classes for test patterns
- **Files Modified in P3-2.4**:
  - `ai_service.py` - Added MULTI_FRAME_SYSTEM_PROMPT, enhanced prompts
  - `system.py` - Added multi_frame_description_prompt field
- **Pre-existing Issue**: `datetime.utcnow()` deprecation warning (lines 1358, 1970)

**Files to REUSE (not recreate):**
- `backend/app/models/ai_usage.py` - Extend existing model
- `backend/app/services/ai_service.py` - Modify `_track_usage()` method
- `backend/tests/test_services/test_ai_service.py` - Add tests to existing file

**Key Methods to Modify:**
- `_track_usage()` (lines ~1960-1985) - Add analysis_mode and is_estimated parameters
- `_calculate_cost()` or add new method for provider-specific rates

[Source: docs/sprint-artifacts/p3-2-4-create-multi-frame-prompts-optimized-for-sequences.md#Dev-Agent-Record]

### Testing Standards

- Add tests to existing `backend/tests/test_services/test_ai_service.py`
- Create new `TestMultiImageUsageTracking` class or extend existing
- Test database model changes with SQLAlchemy test session
- Mock provider responses to verify token extraction
- Test estimation logic for providers without token counts

### References

- [Source: docs/architecture.md#CostTracker]
- [Source: docs/epics-phase3.md#Story-P3-2.5]
- [Source: docs/sprint-artifacts/p3-2-4-create-multi-frame-prompts-optimized-for-sequences.md]
- OpenAI token counting: https://platform.openai.com/docs/guides/vision

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-2-5-track-token-usage-for-multi-image-requests.context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- None required

### Completion Notes List

1. Added `analysis_mode` and `is_estimated` columns to AIUsage model in `backend/app/models/ai_usage.py`
2. Created Alembic migration `9312c504c570_add_analysis_mode_and_is_estimated_to_.py`
3. Added `TOKENS_PER_IMAGE` constants for token estimation per provider (OpenAI, Grok, Claude, Gemini)
4. Added `COST_RATES` constants for cost calculation per provider
5. Implemented `_estimate_image_tokens()` method to estimate tokens when providers don't return counts
6. Implemented `_calculate_cost()` method for provider-specific cost calculation
7. Updated `_track_usage()` method to accept `analysis_mode` and `is_estimated` parameters
8. Updated single-image tracking to pass `analysis_mode="single_image"`
9. Updated multi-image tracking to pass `analysis_mode="multi_frame"` with estimation logic
10. Added 13 new tests (TestTokenEstimation: 6, TestCostCalculation: 4, TestAnalysisModeTracking: 3)
11. All 74 AI service tests pass

### File List

**Modified:**
- `backend/app/models/ai_usage.py` - Added analysis_mode and is_estimated columns
- `backend/app/services/ai_service.py` - Added token estimation, cost calculation, and usage tracking enhancements
- `backend/tests/test_services/test_ai_service.py` - Added 13 new tests for multi-image token tracking

**Added:**
- `backend/alembic/versions/9312c504c570_add_analysis_mode_and_is_estimated_to_.py` - Migration for new columns

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-06 | 1.0 | Story drafted from epics-phase3.md |
| 2025-12-06 | 1.1 | Implementation complete - all tasks done, 74 tests passing |
| 2025-12-06 | 1.2 | Senior Developer Review notes appended - APPROVED |

---

## Senior Developer Review (AI)

### Reviewer
Brent

### Date
2025-12-06

### Outcome
**APPROVE** - All acceptance criteria implemented and verified. All tasks marked complete are verified as done.

### Summary
Story P3-2.5 implements comprehensive multi-image token usage tracking for AI requests. The implementation adds `analysis_mode` and `is_estimated` columns to the AIUsage model, implements token estimation for providers that don't return counts (particularly Gemini), and adds provider-specific cost calculation. All 4 acceptance criteria are fully implemented with 13 new tests covering the functionality.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- Note: `datetime.utcnow()` deprecation warning at `ai_service.py:2100` - pre-existing issue noted in story dev notes, not a blocker

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Multi-image AI request tracks total tokens | IMPLEMENTED | `ai_service.py:1770-1775` |
| AC2 | OpenAI 5-image request stores analysis_mode="multi_frame" | IMPLEMENTED | `ai_service.py:1775` |
| AC3 | Token estimation for providers without counts | IMPLEMENTED | `ai_service.py:1188-1229` |
| AC4 | Cost calculation with provider rates | IMPLEMENTED | `ai_service.py:1231-1270` |

**Summary: 4 of 4 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| 1.1 Add analysis_mode column | Complete | VERIFIED | `ai_usage.py:30` |
| 1.2 Add is_estimated column | Complete | VERIFIED | `ai_usage.py:31` |
| 1.3 Create Alembic migration | Complete | VERIFIED | `9312c504c570_add_analysis_mode_and_is_estimated_to_.py` |
| 1.4 Apply migration | Complete | VERIFIED | Migration applied |
| 2.1 Modify _track_usage() | Complete | VERIFIED | `ai_service.py:2077-2082` |
| 2.2 Multi-image passes multi_frame | Complete | VERIFIED | `ai_service.py:1775` |
| 2.3 Single-image passes single_image | Complete | VERIFIED | `ai_service.py:1535` |
| 2.4 Token counts captured | Complete | VERIFIED | Tests pass |
| 3.1 Token estimation constants | Complete | VERIFIED | `ai_service.py:66-71` |
| 3.2 _estimate_image_tokens() | Complete | VERIFIED | `ai_service.py:1188-1229` |
| 3.3 Apply estimation for Gemini | Complete | VERIFIED | `ai_service.py:1758-1774` |
| 3.4 Set is_estimated=True | Complete | VERIFIED | `ai_service.py:1775` |
| 4.1 Cost rates per provider | Complete | VERIFIED | `ai_service.py:75-80` |
| 4.2 _calculate_cost() method | Complete | VERIFIED | `ai_service.py:1231-1270` |
| 4.3 Cost stored with AIUsage | Complete | VERIFIED | `ai_service.py:2105` |
| 5.1-5.7 Unit tests | Complete | VERIFIED | 13 tests pass |

**Summary: 17 of 17 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

**Tests Added:**
- `TestTokenEstimation` (6 tests) - Tests token estimation for all providers
- `TestCostCalculation` (4 tests) - Tests cost calculation for all providers
- `TestAnalysisModeTracking` (3 tests) - Tests analysis_mode and is_estimated tracking

**Coverage:**
- AC1: Covered by `test_multi_image_tracking_sets_analysis_mode`
- AC2: Covered by `test_multi_image_tracking_sets_analysis_mode`, `test_single_image_tracking_sets_analysis_mode`
- AC3: Covered by all `TestTokenEstimation` tests + `test_multi_image_estimation_when_no_tokens_returned`
- AC4: Covered by all `TestCostCalculation` tests

**Test Results:** 13/13 tests pass, 74/74 AI service tests pass overall

### Architectural Alignment

- ✓ Follows existing AIService patterns
- ✓ Uses SQLAlchemy model with Alembic migration
- ✓ Cost rates match architecture.md CostTracker section
- ✓ Token estimates based on provider documentation

### Security Notes

No security concerns identified. Changes are limited to internal tracking and do not expose new attack surfaces.

### Best-Practices and References

- Token estimation constants based on provider documentation
- Cost rates from architecture.md CostTracker section
- OpenAI vision token counting: https://platform.openai.com/docs/guides/vision

### Action Items

**Advisory Notes:**
- Note: Consider addressing `datetime.utcnow()` deprecation in a future cleanup story (not blocking)
