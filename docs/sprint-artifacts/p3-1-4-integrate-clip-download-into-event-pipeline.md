# Story P3-1.4: Integrate Clip Download into Event Pipeline

Status: done

## Story

As a **system**,
I want **clip downloads to happen automatically for Protect events**,
so that **video is available when AI analysis needs it**.

## Acceptance Criteria

1. **AC1:** Given a Protect smart detection event is received, when the event is processed by EventProcessor, then ClipService.download_clip() is called before AI analysis and clip path is passed to AI service if download succeeds
2. **AC2:** Given clip download fails after retries, when fallback is triggered (FR5), then system uses existing thumbnail/snapshot for AI analysis and event is flagged with `fallback_reason: "clip_download_failed"` and processing continues without interruption (NFR8)
3. **AC3:** Given clip download succeeds, when AI analysis completes, then ClipService.cleanup_clip() is called and temporary file is removed
4. **AC4:** Given multiple events arrive simultaneously, when clips are being downloaded, then each event's clip download is independent and one failure doesn't block others (NFR8)

## Tasks / Subtasks

- [x] **Task 1: Add fallback_reason field to Event model** (AC: 2)
  - [x] 1.1 Add `fallback_reason: Optional[str]` field to Event model in `backend/app/models/event.py`
  - [x] 1.2 Create Alembic migration to add `fallback_reason` column to events table
  - [x] 1.3 Run `alembic upgrade head` to apply migration
  - [x] 1.4 Update EventResponse schema in `backend/app/schemas/event.py` to include `fallback_reason`

- [x] **Task 2: Extend event processing context** (AC: 1, 2)
  - [x] 2.1 Add `clip_path: Optional[Path]` to event processing context in EventProcessor
  - [x] 2.2 Add `fallback_reason: Optional[str]` to event processing context
  - [x] 2.3 Ensure context is passed through the processing pipeline

- [x] **Task 3: Integrate clip download into Protect event handler** (AC: 1, 2, 4)
  - [x] 3.1 Import `get_clip_service()` in event processor
  - [x] 3.2 After receiving Protect smart detection event, call `ClipService.download_clip()` with controller_id, camera_id, event timestamps, event_id
  - [x] 3.3 If download returns Path, set `clip_path` in context
  - [x] 3.4 If download returns None, set `fallback_reason = "clip_download_failed"` and use existing thumbnail
  - [x] 3.5 Ensure download is async and doesn't block other event processing

- [x] **Task 4: Pass clip path to AI service** (AC: 1)
  - [x] 4.1 Modify AI description generation call to accept optional `clip_path` parameter
  - [x] 4.2 If `clip_path` provided, AI service can use it (future stories will add multi-frame extraction)
  - [x] 4.3 For now, AI service continues using thumbnail if clip processing not yet implemented

- [x] **Task 5: Implement clip cleanup after AI analysis** (AC: 3)
  - [x] 5.1 After AI description is generated, check if `clip_path` was set
  - [x] 5.2 If clip exists, call `ClipService.cleanup_clip(event_id)` to remove temporary file
  - [x] 5.3 Log cleanup success/failure with event_id

- [x] **Task 6: Store fallback_reason in database** (AC: 2)
  - [x] 6.1 When creating Event record, include `fallback_reason` field if set
  - [x] 6.2 Verify fallback_reason is persisted and queryable

- [x] **Task 7: Write integration tests** (AC: All)
  - [x] 7.1 Test successful clip download → AI analysis → cleanup flow
  - [x] 7.2 Test clip download failure → fallback to thumbnail → event flagged
  - [x] 7.3 Test multiple concurrent events with independent clip downloads
  - [x] 7.4 Test event still creates successfully when clip unavailable
  - [x] 7.5 Test cleanup is called after processing completes

## Dev Notes

### Architecture References

- **FR5:** System handles clip download failures gracefully with fallback to snapshot [Source: docs/PRD-phase3.md#Video-Clip-Management]
- **NFR8:** System continues processing other events if one clip download fails [Source: docs/PRD-phase3.md#Reliability]
- **EventProcessor specification:** [Source: docs/architecture.md#Event-Processing-Pipeline]
- **ClipService specification:** [Source: docs/architecture.md#Phase-3-Service-Architecture]

### Project Structure Notes

- Modify existing file: `backend/app/services/event_processor.py`
- Modify existing file: `backend/app/models/event.py`
- Modify existing file: `backend/app/schemas/event.py`
- Create migration: `backend/alembic/versions/xxx_add_fallback_reason.py`
- Add tests to existing: `backend/tests/test_services/test_event_processor.py`

### Implementation Guidance

1. **Async clip download:** Use `await ClipService.download_clip()` to avoid blocking
   ```python
   clip_service = get_clip_service()
   clip_path = await clip_service.download_clip(
       controller_id=controller_id,
       camera_id=camera_id,
       event_start=event_start,
       event_end=event_end,
       event_id=event_id
   )
   if clip_path is None:
       fallback_reason = "clip_download_failed"
   ```

2. **Fallback pattern:** When clip unavailable, continue with existing thumbnail
   ```python
   if clip_path:
       # Future: Extract frames and pass to AI
       pass
   else:
       # Use existing thumbnail for AI analysis
       # Set fallback_reason for tracking
       pass
   ```

3. **Cleanup pattern:** Always cleanup after processing
   ```python
   try:
       # AI analysis...
   finally:
       if clip_path:
           clip_service.cleanup_clip(event_id)
   ```

### Testing Standards

- Mock ClipService for unit tests
- Use `AsyncMock` for async method mocking
- Test both success and failure paths
- Verify fallback_reason is set correctly on failures
- Follow existing test patterns in `test_event_processor.py`

### Learnings from Previous Story

**From Story p3-1-3-implement-retry-logic-with-exponential-backoff (Status: done)**

- **ClipService API**: Use `download_clip(controller_id, camera_id, event_start, event_end, event_id)` - returns `Optional[Path]`
- **Cleanup API**: Use `cleanup_clip(event_id)` - returns `bool` (True if deleted)
- **Singleton Pattern**: Use `get_clip_service()` to get service instance, `reset_clip_service()` for testing
- **Exception Classes Available**: `RetriableClipError`, `NonRetriableClipError` - but caller doesn't need to handle these, `download_clip()` catches all exceptions and returns None
- **Retry Logic Built-in**: Retries 3 times with exponential backoff (1s, 2s, 4s) automatically
- **Structured Logging**: Log events with `extra={}` dict pattern for consistency
- **66 tests exist** in test_clip_service.py - follow established patterns

[Source: docs/sprint-artifacts/p3-1-3-implement-retry-logic-with-exponential-backoff.md#Dev-Agent-Record]

### References

- [Source: docs/architecture.md#Event-Processing-Pipeline]
- [Source: docs/PRD-phase3.md#FR5-Fallback]
- [Source: docs/PRD-phase3.md#NFR8-Independent-Processing]
- [Source: docs/epics-phase3.md#Story-P3-1.4]
- [Source: docs/sprint-artifacts/p3-1-3-implement-retry-logic-with-exponential-backoff.md]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-1-4-integrate-clip-download-into-event-pipeline.context.xml`

### Agent Model Used

- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 25 Protect event integration tests passing
- All 10 new P3-1.4 tests (TestClipDownloadIntegration, TestClipCleanup, TestConcurrentClipDownloads) passing

### Completion Notes List

1. **Event model extended**: Added `fallback_reason` column (String(100), nullable) to track clip download failures
2. **Alembic migration created**: `f7f1243134d4_add_fallback_reason_to_events.py` - minimal migration that only adds the new column
3. **ProcessingEvent dataclass extended**: Added `clip_path: Optional[Path]` and `fallback_reason: Optional[str]` fields
4. **ProtectEventHandler integration**:
   - Added `_download_clip_for_event()` method that downloads 30-second clips centered on event timestamp
   - Modified `handle_event()` to download clips before AI analysis
   - Implemented fallback pattern: if download fails, returns `(None, "clip_download_failed")`
   - Added cleanup logic: calls `ClipService.cleanup_clip()` after AI processing
5. **API response updated**: Added `fallback_reason` and `provider_used` to event detail response in `events.py`
6. **Schema updates**: Added `fallback_reason` to both `EventCreate` and `EventResponse` schemas
7. **Tests added**: 10 new integration tests covering clip download, fallback, cleanup, and concurrent operations

### File List

| Status | File Path |
|--------|-----------|
| Modified | `backend/app/models/event.py` |
| Modified | `backend/app/schemas/event.py` |
| Modified | `backend/app/services/event_processor.py` |
| Modified | `backend/app/services/protect_event_handler.py` |
| Modified | `backend/app/api/v1/events.py` |
| Created | `backend/alembic/versions/f7f1243134d4_add_fallback_reason_to_events.py` |
| Modified | `backend/tests/test_integration/test_protect_events.py` |

## Senior Developer Review (AI)

### Reviewer
Brent

### Date
2025-12-05

### Outcome
**APPROVE** ✅

All acceptance criteria are fully implemented with comprehensive test coverage. All tasks marked complete have been verified with code evidence.

### Summary

Story P3-1.4 successfully integrates ClipService clip download functionality into the Protect event processing pipeline. The implementation follows the established patterns from P3-1.3 (retry logic) and correctly implements fallback behavior when clips are unavailable. Code quality is high with proper error handling, structured logging, and async patterns.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- Note: `clip_path` parameter is passed to `_submit_to_ai_pipeline()` but not yet used by AI service (expected - future stories P3-2 will add multi-frame extraction)

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | ClipService.download_clip() called before AI analysis, clip_path passed if successful | ✅ IMPLEMENTED | `protect_event_handler.py:251-260` (download call), `protect_event_handler.py:305` (passed to AI) |
| AC2 | Fallback to thumbnail on failure with fallback_reason="clip_download_failed" | ✅ IMPLEMENTED | `protect_event_handler.py:688-699` (fallback logic), `protect_event_handler.py:352` (stored in event), `models/event.py:61` (model field) |
| AC3 | ClipService.cleanup_clip() called after AI completes | ✅ IMPLEMENTED | `protect_event_handler.py:308-329` (cleanup with logging) |
| AC4 | Independent concurrent downloads | ✅ IMPLEMENTED | Async pattern in `_download_clip_for_event()` - each event downloads independently, failures don't block |

**Summary: 4 of 4 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Add fallback_reason field to Event model | ✅ Complete | ✅ Verified | `models/event.py:61`, `alembic/versions/f7f1243134d4_add_fallback_reason_to_events.py`, `schemas/event.py:29,91` |
| Task 2: Extend event processing context | ✅ Complete | ✅ Verified | `event_processor.py:60-61,69-71` - ProcessingEvent dataclass with clip_path and fallback_reason |
| Task 3: Integrate clip download into Protect handler | ✅ Complete | ✅ Verified | `protect_event_handler.py:53,251-260,621-713` - imports, download call, `_download_clip_for_event()` method |
| Task 4: Pass clip_path to AI service | ✅ Complete | ✅ Verified | `protect_event_handler.py:299-306` - clip_path passed, `protect_event_handler.py:836,849` - method signature accepts parameter |
| Task 5: Implement clip cleanup after AI | ✅ Complete | ✅ Verified | `protect_event_handler.py:308-329` - cleanup with success/failure logging, also cleanup on snapshot failure `protect_event_handler.py:273-279` |
| Task 6: Store fallback_reason in database | ✅ Complete | ✅ Verified | `protect_event_handler.py:352,932,948,970` - passed through and stored |
| Task 7: Write integration tests | ✅ Complete | ✅ Verified | `test_protect_events.py:446-757` - TestClipDownloadIntegration (6 tests), TestClipCleanup (2 tests), TestConcurrentClipDownloads (2 tests) |

**Summary: 7 of 7 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

**Test Files Modified:**
- `backend/tests/test_integration/test_protect_events.py` - 10 new tests added

**Test Coverage:**
- ✅ AC1: `test_download_clip_for_event_method_exists`, `test_download_clip_returns_tuple`, `test_successful_download_no_fallback`
- ✅ AC2: `test_event_with_fallback_reason_stored`, `test_event_without_fallback_reason`, `test_fallback_reason_in_api_response`
- ✅ AC3: `test_cleanup_clip_method_exists`, `test_cleanup_called_after_processing`
- ✅ AC4: `test_multiple_downloads_independent`, `test_one_failure_doesnt_block_others`

**Test Results:**
- All 25 Protect event tests passing (including 10 new P3-1.4 tests)

### Architectural Alignment

- ✅ Follows existing singleton pattern (`get_clip_service()`)
- ✅ Uses async/await for non-blocking operations
- ✅ Implements fallback pattern per FR5 specification
- ✅ Uses structured logging with extra={} dict pattern
- ✅ Database migration follows existing Alembic patterns

### Security Notes

- No security concerns identified
- Clip files stored in controlled temp directory with proper cleanup

### Best-Practices and References

- [Python async patterns](https://docs.python.org/3/library/asyncio.html) - Used correctly for concurrent operations
- [SQLAlchemy nullable columns](https://docs.sqlalchemy.org/en/20/core/defaults.html) - `fallback_reason` properly nullable

### Action Items

**Code Changes Required:**
None - all acceptance criteria met

**Advisory Notes:**
- Note: Future story P3-2 will implement multi-frame extraction using the clip_path parameter (currently passed but unused by AI service)
- Note: Consider adding metrics for clip download success rate in production monitoring

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-05 | 1.0.0 | Initial implementation complete |
| 2025-12-05 | 1.0.1 | Senior Developer Review notes appended - APPROVED |
