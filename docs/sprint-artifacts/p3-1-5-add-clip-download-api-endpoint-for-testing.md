# Story P3-1.5: Add Clip Download API Endpoint for Testing

Status: done

## Story

As a **developer**,
I want **an API endpoint to test clip downloads**,
so that **I can verify Protect clip retrieval works correctly**.

## Acceptance Criteria

1. **AC1:** Given a valid Protect camera_id and event timestamps, when `POST /api/v1/protect/test-clip-download` is called, then system attempts to download a clip and returns `{success: true, file_size_bytes: N, duration_seconds: N}`
2. **AC2:** Given clip download fails, when API endpoint is called, then returns `{success: false, error: "description"}` with HTTP 200 (test result, not server error)
3. **AC3:** Given camera_id doesn't belong to any controller, when API endpoint is called, then returns `{success: false, error: "Camera not found in any Protect controller"}`
4. **AC4:** Given successful test download, when response is returned, then test clip is cleaned up (deleted) automatically

## Tasks / Subtasks

- [x] **Task 1: Create API endpoint schemas** (AC: 1, 2, 3)
  - [x] 1.1 Create `TestClipDownloadRequest` schema with camera_id, start_time, end_time fields
  - [x] 1.2 Create `TestClipDownloadResponse` schema with success, file_size_bytes, duration_seconds, error fields
  - [x] 1.3 Add validation for timestamp format (ISO 8601 with timezone)

- [x] **Task 2: Implement test-clip-download endpoint** (AC: 1, 2, 3, 4)
  - [x] 2.1 Add `POST /api/v1/protect/test-clip-download` route to protect.py
  - [x] 2.2 Look up camera by camera_id to get controller_id and protect_camera_id
  - [x] 2.3 Call `ClipService.download_clip()` with test event_id
  - [x] 2.4 If successful, get file size and extract duration using PyAV
  - [x] 2.5 Always clean up test clip after getting metadata (use finally block)
  - [x] 2.6 Return appropriate response based on success/failure

- [x] **Task 3: Add video metadata extraction** (AC: 1)
  - [x] 3.1 Add `_get_video_duration(clip_path)` helper function
  - [x] 3.2 Use PyAV to extract duration_seconds from video file
  - [x] 3.3 Handle corrupted/invalid video files gracefully

- [x] **Task 4: Write unit tests** (AC: All)
  - [x] 4.1 Test successful clip download returns correct response format
  - [x] 4.2 Test failed download returns success=false with error message
  - [x] 4.3 Test unknown camera returns appropriate error
  - [x] 4.4 Test clip is cleaned up after successful test
  - [x] 4.5 Test clip is cleaned up even if metadata extraction fails

## Dev Notes

### Architecture References

- **ClipService API**: Use `get_clip_service()` singleton, `download_clip()` returns `Optional[Path]`
- **Cleanup API**: Use `cleanup_clip(event_id)` to remove test clips
- [Source: docs/architecture.md#Phase-3-Service-Architecture]
- [Source: docs/epics-phase3.md#Story-P3-1.5]

### Project Structure Notes

- Add endpoint to: `backend/app/api/v1/protect.py`
- Add schemas to: `backend/app/schemas/protect.py`
- Add tests to: `backend/tests/test_api/test_protect.py`

### Implementation Guidance

1. **Request Schema:**
   ```python
   class TestClipDownloadRequest(BaseModel):
       camera_id: str = Field(..., description="Camera UUID (internal)")
       start_time: datetime = Field(..., description="Clip start time (ISO 8601)")
       end_time: datetime = Field(..., description="Clip end time (ISO 8601)")
   ```

2. **Response Schema:**
   ```python
   class TestClipDownloadResponse(BaseModel):
       success: bool
       file_size_bytes: Optional[int] = None
       duration_seconds: Optional[float] = None
       error: Optional[str] = None
   ```

3. **Endpoint Pattern:**
   ```python
   @router.post("/test-clip-download", response_model=TestClipDownloadResponse)
   async def test_clip_download(request: TestClipDownloadRequest, db: Session = Depends(get_db)):
       # Look up camera
       camera = db.query(Camera).filter(Camera.id == request.camera_id).first()
       if not camera or camera.source_type != 'protect':
           return TestClipDownloadResponse(success=False, error="Camera not found in any Protect controller")

       # Generate test event ID
       test_event_id = f"test-{uuid.uuid4()}"
       clip_service = get_clip_service()

       try:
           clip_path = await clip_service.download_clip(
               controller_id=camera.protect_controller_id,
               camera_id=camera.protect_camera_id,
               event_start=request.start_time,
               event_end=request.end_time,
               event_id=test_event_id
           )

           if not clip_path:
               return TestClipDownloadResponse(success=False, error="Clip download failed")

           # Get metadata
           file_size = clip_path.stat().st_size
           duration = _get_video_duration(clip_path)

           return TestClipDownloadResponse(
               success=True,
               file_size_bytes=file_size,
               duration_seconds=duration
           )
       finally:
           # Always cleanup
           clip_service.cleanup_clip(test_event_id)
   ```

4. **Video Duration Extraction:**
   ```python
   def _get_video_duration(clip_path: Path) -> Optional[float]:
       try:
           import av
           with av.open(str(clip_path)) as container:
               if container.duration:
                   return container.duration / av.time_base
       except Exception:
           pass
       return None
   ```

### Testing Standards

- Mock ClipService for unit tests
- Use `AsyncMock` for async download_clip
- Test both success and failure paths
- Verify cleanup is always called
- Follow existing test patterns in `test_protect.py`

### Learnings from Previous Story

**From Story p3-1-4-integrate-clip-download-into-event-pipeline (Status: done)**

- **ClipService Singleton**: Use `get_clip_service()` from `backend/app/services/clip_service.py`
- **Download API**: `download_clip(controller_id, camera_id, event_start, event_end, event_id)` returns `Optional[Path]`
- **Cleanup API**: `cleanup_clip(event_id)` returns `bool` - True if deleted
- **Event Model**: Has `fallback_reason` field for tracking failures
- **Async Pattern**: Use `await` for `download_clip()` - it's async
- **Structured Logging**: Log events with `extra={}` dict pattern

[Source: docs/sprint-artifacts/p3-1-4-integrate-clip-download-into-event-pipeline.md#Dev-Agent-Record]

### References

- [Source: docs/architecture.md#Phase-3-Service-Architecture]
- [Source: docs/epics-phase3.md#Story-P3-1.5]
- [Source: docs/sprint-artifacts/p3-1-4-integrate-clip-download-into-event-pipeline.md]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-1-5-add-clip-download-api-endpoint-for-testing.context.xml`

### Agent Model Used

- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 8 P3-1.5 tests passing (TestClipDownloadEndpoint: 7 tests, TestClipDownloadResponseFormat: 1 test)

### Completion Notes List

1. **Schema creation**: Added `TestClipDownloadRequest` and `TestClipDownloadResponse` to `backend/app/schemas/protect.py` with proper validation (end_time must be after start_time)
2. **Endpoint implementation**: Added `POST /api/v1/protect/test-clip-download` to `backend/app/api/v1/protect.py`
3. **Video metadata extraction**: Added `_get_video_duration()` helper using PyAV to extract duration in seconds from MP4 container
4. **Camera validation**: Validates camera exists, is a Protect camera, and has proper controller/camera IDs
5. **Cleanup in finally block**: Test clips are always cleaned up regardless of success/failure using test-prefixed event IDs
6. **HTTP 200 for all outcomes**: Returns success=true/false in response body, not HTTP error codes
7. **Test coverage**: 8 tests covering success, failure, non-existent camera, non-Protect camera, cleanup, and validation

### File List

| Status | File Path |
|--------|-----------|
| Modified | `backend/app/schemas/protect.py` |
| Modified | `backend/app/api/v1/protect.py` |
| Modified | `backend/tests/test_api/test_protect.py` |

## Senior Developer Review (AI)

### Reviewer
- Brent

### Date
- 2025-12-05

### Outcome
**APPROVE** - All acceptance criteria implemented with evidence, all tasks verified complete, code quality excellent.

### Summary
Story P3-1.5 implements a test-clip-download API endpoint for developers to verify Protect clip retrieval functionality. The implementation is clean, well-structured, follows existing patterns, and includes comprehensive test coverage. All 4 ACs are implemented correctly, and all 20 tasks/subtasks are verified complete.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- None identified.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Valid camera_id + timestamps → returns {success: true, file_size_bytes, duration_seconds} | ✅ IMPLEMENTED | `protect.py:1298-1302` |
| AC2 | Download fails → returns {success: false, error: "description"} with HTTP 200 | ✅ IMPLEMENTED | `protect.py:1278-1281` |
| AC3 | Camera not found → returns {success: false, error: "Camera not found..."} | ✅ IMPLEMENTED | `protect.py:1222-1252` (multiple validation points) |
| AC4 | Test clip is cleaned up automatically | ✅ IMPLEMENTED | `protect.py:1304-1315` (finally block) |

**Summary**: 4 of 4 acceptance criteria fully implemented

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Create API endpoint schemas | [x] | ✅ VERIFIED | `schemas/protect.py:425-483` |
| Task 1.1: TestClipDownloadRequest | [x] | ✅ VERIFIED | `schemas/protect.py:425-451` |
| Task 1.2: TestClipDownloadResponse | [x] | ✅ VERIFIED | `schemas/protect.py:454-483` |
| Task 1.3: Timestamp validation | [x] | ✅ VERIFIED | `schemas/protect.py:432-439` |
| Task 2: Implement endpoint | [x] | ✅ VERIFIED | `protect.py:1177-1315` |
| Task 2.1: POST route | [x] | ✅ VERIFIED | `protect.py:1177` |
| Task 2.2: Camera lookup | [x] | ✅ VERIFIED | `protect.py:1212` |
| Task 2.3: Call ClipService | [x] | ✅ VERIFIED | `protect.py:1261-1267` |
| Task 2.4: Get metadata | [x] | ✅ VERIFIED | `protect.py:1284-1285` |
| Task 2.5: Cleanup in finally | [x] | ✅ VERIFIED | `protect.py:1304-1315` |
| Task 2.6: Return response | [x] | ✅ VERIFIED | `protect.py:1222-1302` |
| Task 3: Video metadata extraction | [x] | ✅ VERIFIED | `protect.py:1142-1174` |
| Task 3.1: _get_video_duration helper | [x] | ✅ VERIFIED | `protect.py:1142-1174` |
| Task 3.2: PyAV duration | [x] | ✅ VERIFIED | `protect.py:1154-1163` |
| Task 3.3: Handle corrupted files | [x] | ✅ VERIFIED | `protect.py:1165-1174` |
| Task 4: Write unit tests | [x] | ✅ VERIFIED | `test_protect.py:4089-4379` |
| Task 4.1: Success test | [x] | ✅ VERIFIED | `test_protect.py:4179-4222` |
| Task 4.2: Failure test | [x] | ✅ VERIFIED | `test_protect.py:4224-4250` |
| Task 4.3: Unknown camera test | [x] | ✅ VERIFIED | `test_protect.py:4146-4160` |
| Task 4.4: Cleanup success test | [x] | ✅ VERIFIED | `test_protect.py:4252-4290` |
| Task 4.5: Cleanup failure test | [x] | ✅ VERIFIED | `test_protect.py:4292-4335` |

**Summary**: 20 of 20 completed tasks verified, 0 questionable, 0 falsely marked complete

### Test Coverage and Gaps

**Test Coverage**: Excellent
- 8 tests covering all acceptance criteria
- Tests include: success path, failure paths, validation errors, cleanup verification
- All 8 P3-1.5 tests passing

**No gaps identified.**

### Architectural Alignment

- ✅ Uses singleton pattern `get_clip_service()` per architecture guidelines
- ✅ Follows existing Protect endpoint patterns (async def, structured logging)
- ✅ Uses `finally` block for guaranteed cleanup
- ✅ Returns HTTP 200 for all outcomes (test result semantics, not error semantics)
- ✅ Proper separation of concerns (schemas in schemas/, endpoint in api/)

### Security Notes

- No security concerns - endpoint is for development/testing purposes
- Camera validation prevents unauthorized access to non-existent cameras
- Test event IDs are UUID-based to prevent collision with real events

### Best-Practices and References

- FastAPI async endpoint patterns: https://fastapi.tiangolo.com/async/
- PyAV video metadata: https://pyav.org/docs/stable/
- Pydantic field validators: https://docs.pydantic.dev/latest/concepts/validators/

### Action Items

**Code Changes Required:**
- None

**Advisory Notes:**
- Note: Consider adding rate limiting for production if endpoint remains available (no action required for MVP)
