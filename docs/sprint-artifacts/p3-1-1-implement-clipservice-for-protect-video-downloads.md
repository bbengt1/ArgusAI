# Story P3-1.1: Implement ClipService for Protect Video Downloads

Status: done

## Story

As a **system operator**,
I want **the backend to download motion clips from UniFi Protect**,
so that **video content is available for AI analysis**.

## Acceptance Criteria

1. **AC1:** ClipService class exists at `backend/app/services/clip_service.py` with `download_clip()` method
2. **AC2:** Given a Protect smart detection event with camera_id and event timestamps, when `ClipService.download_clip()` is called, then the system downloads the MP4 clip via uiprotect library
3. **AC3:** Downloaded clips are saved to `data/clips/{event_id}.mp4` file path
4. **AC4:** Method returns the file path on success or None on failure (no exceptions raised)
5. **AC5:** Download completes within 10 seconds for typical motion events (10-30 second clips) - NFR1
6. **AC6:** Uses existing controller credentials from ProtectService (no duplicate authentication)
7. **AC7:** When Protect controller is unreachable, method returns None and logs failure with event_id and error details
8. **AC8:** `data/clips/` directory is created if it doesn't exist on first download

## Tasks / Subtasks

- [x] **Task 1: Research uiprotect clip download API** (AC: 2)
  - [x] 1.1 Investigate uiprotect library for video clip download method
  - [x] 1.2 Determine if `get_camera_video()` or equivalent method exists
  - [x] 1.3 Document required parameters (camera_id, start_time, end_time, etc.)
  - [x] 1.4 Note any format or duration constraints

- [x] **Task 2: Create ClipService class** (AC: 1, 8)
  - [x] 2.1 Create `backend/app/services/clip_service.py`
  - [x] 2.2 Define ClipService class with constants:
    - `TEMP_CLIP_DIR = "data/clips"`
    - `MAX_CLIP_AGE_HOURS = 1`
    - `MAX_STORAGE_MB = 1024`
  - [x] 2.3 Add `__init__` method to accept ProtectService dependency
  - [x] 2.4 Add `_ensure_clip_dir()` helper method to create directory

- [x] **Task 3: Implement download_clip() method** (AC: 2, 3, 4, 5, 6, 7)
  - [x] 3.1 Define async method signature:
    ```python
    async def download_clip(
        self,
        controller_id: str,
        camera_id: str,
        event_start: datetime,
        event_end: datetime,
        event_id: str
    ) -> Optional[Path]
    ```
  - [x] 3.2 Get ProtectService client for controller_id
  - [x] 3.3 Call uiprotect's clip download method with time range
  - [x] 3.4 Save MP4 to `data/clips/{event_id}.mp4`
  - [x] 3.5 Return Path on success, None on any failure
  - [x] 3.6 Add timeout handling (10 second limit)
  - [x] 3.7 Add comprehensive error logging

- [x] **Task 4: Add helper method for clip path** (AC: 3)
  - [x] 4.1 Implement `_get_clip_path(event_id: str) -> Path`
  - [x] 4.2 Ensure consistent path generation

- [x] **Task 5: Write unit tests** (AC: All)
  - [x] 5.1 Create `backend/tests/test_services/test_clip_service.py`
  - [x] 5.2 Test successful clip download (mock uiprotect)
  - [x] 5.3 Test directory creation on first download
  - [x] 5.4 Test failure handling (controller unreachable)
  - [x] 5.5 Test timeout behavior
  - [x] 5.6 Test file path generation

- [x] **Task 6: Add PyAV dependency** (AC: 2)
  - [x] 6.1 Add `av>=12.0.0` to `backend/requirements.txt` if not present
  - [x] 6.2 Verify import works

## Dev Notes

### Architecture References

- **ClipService specification:** [Source: docs/architecture.md#Phase-3-Service-Architecture]
- **File path pattern:** `data/clips/{event_id}.mp4` or `data/clips/{event_id}/clip.mp4`
- **Constants defined:**
  - `TEMP_CLIP_DIR = "data/clips"`
  - `MAX_CLIP_AGE_HOURS = 1`
  - `MAX_STORAGE_MB = 1024`

### Project Structure Notes

- Create new file: `backend/app/services/clip_service.py`
- Create new directory: `backend/data/clips/` (add to .gitignore)
- Test file: `backend/tests/test_services/test_clip_service.py`

### Implementation Guidance

1. **Reuse ProtectService:** The ClipService should take ProtectService as a dependency and use its authenticated client connection rather than creating new connections.

2. **uiprotect API Investigation Required:** The exact method for downloading clips needs investigation. Possibilities:
   - `camera.get_video()` method
   - `protect.get_camera_video()`
   - REST endpoint with authenticated session

3. **Error Handling Pattern:** Follow existing service patterns:
   ```python
   try:
       # Download logic
       return clip_path
   except Exception as e:
       logger.error(f"Clip download failed for event {event_id}: {e}")
       return None
   ```

4. **Timeout Implementation:**
   ```python
   import asyncio
   async with asyncio.timeout(10):
       # Download operation
   ```

5. **File Storage:**
   - Use `pathlib.Path` for cross-platform compatibility
   - Ensure parent directory exists before writing

### Testing Standards

- Mock uiprotect library responses
- Test both success and failure paths
- Verify logging on failures
- Test timeout behavior with `pytest-asyncio`

### References

- [Source: docs/architecture.md#ClipService-NEW]
- [Source: docs/architecture.md#Phase-3-Project-Structure-Additions]
- [Source: docs/PRD-phase3.md#Video-Clip-Management]
- [Source: docs/epics-phase3.md#Story-P3-1.1]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-1-1-implement-clipservice-for-protect-video-downloads.context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- uiprotect API research: Found `ProtectApiClient.get_camera_video(camera_id, start, end, output_file)` method via GitHub source code analysis
- PyAV verification: v16.0.1 installed (satisfies >=12.0.0 requirement)

### Completion Notes List

1. **Task 1 (Research)**: Confirmed uiprotect library provides `get_camera_video()` method on `ProtectApiClient`. Parameters: camera_id (str), start (datetime), end (datetime), output_file (Path). Video is downloaded directly to the output file.

2. **Task 2-4 (Implementation)**: Created ClipService class following existing service patterns:
   - Singleton pattern matching ProtectService
   - Dependency injection for ProtectService
   - Constants defined as specified in architecture.md
   - Comprehensive structured logging with extra={} dict

3. **Task 5 (Testing)**: Created 23 unit tests covering all acceptance criteria:
   - Constants verification (4 tests)
   - Init and directory creation (2 tests)
   - Helper methods (4 tests)
   - Download success/failure scenarios (7 tests)
   - Logging behavior (3 tests)
   - Singleton pattern (3 tests)

4. **Task 6 (Dependency)**: PyAV already present in requirements.txt as `av>=12.0.0`. Verified import works with installed version 16.0.1.

5. **Additional**: Added `backend/data/clips/` to .gitignore as specified in Dev Notes.

### File List

| Status | File Path |
|--------|-----------|
| Created | backend/app/services/clip_service.py |
| Created | backend/tests/test_services/test_clip_service.py |
| Modified | .gitignore |

---

## Senior Developer Review (AI)

### Reviewer
Brent (via Claude Opus 4.5)

### Date
2025-12-05

### Outcome
**✅ APPROVE**

All 8 acceptance criteria are fully implemented with evidence. All 27 tasks verified as complete. No HIGH or MEDIUM severity issues found.

### Summary

The ClipService implementation is well-structured, follows existing project patterns (singleton, structured logging), and includes comprehensive error handling. The 23 unit tests provide excellent coverage of success and failure scenarios.

### Key Findings

**LOW Severity:**
- Note: `event_id` used in path construction (`clip_service.py:88`) without sanitization. Low risk since event_id is system-generated, not user input. Consider adding validation in future story if external input is added.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | ClipService class exists with download_clip() method | ✅ IMPLEMENTED | `clip_service.py:31-46`, `clip_service.py:90-233` |
| AC2 | Downloads MP4 clip via uiprotect library | ✅ IMPLEMENTED | `clip_service.py:157-162` |
| AC3 | Clips saved to data/clips/{event_id}.mp4 | ✅ IMPLEMENTED | `clip_service.py:23,78-88` |
| AC4 | Returns Path on success, None on failure | ✅ IMPLEMENTED | `clip_service.py:147,177,192,212,233` |
| AC5 | 10 second timeout (NFR1) | ✅ IMPLEMENTED | `clip_service.py:28,154` |
| AC6 | Uses existing ProtectService credentials | ✅ IMPLEMENTED | `clip_service.py:136` |
| AC7 | Returns None and logs on unreachable | ✅ IMPLEMENTED | `clip_service.py:137-147,214-233` |
| AC8 | Creates data/clips/ directory if not exists | ✅ IMPLEMENTED | `clip_service.py:57-58,60-76` |

**Summary: 8 of 8 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked | Verified | Evidence |
|------|--------|----------|----------|
| Task 1: Research uiprotect API | [x] | ✅ | Debug logs, `clip_service.py:157` |
| Task 2: Create ClipService class | [x] | ✅ | `clip_service.py:31-76` |
| Task 3: Implement download_clip() | [x] | ✅ | `clip_service.py:90-233` |
| Task 4: Add helper for clip path | [x] | ✅ | `clip_service.py:78-88` |
| Task 5: Write unit tests | [x] | ✅ | `test_clip_service.py` (23 tests) |
| Task 6: Add PyAV dependency | [x] | ✅ | requirements.txt, PyAV v16.0.1 |

**Summary: 27 of 27 completed tasks verified, 0 questionable, 0 false completions**

### Test Coverage and Gaps

- ✅ 23 unit tests covering all ACs
- ✅ Success path tested
- ✅ Failure paths tested (timeout, error, controller unreachable)
- ✅ Directory creation tested
- ✅ Logging behavior tested
- ✅ Singleton pattern tested

### Architectural Alignment

- ✅ Follows singleton pattern matching ProtectService
- ✅ Uses dependency injection for ProtectService
- ✅ Follows structured logging pattern with `extra={}` dict
- ✅ Uses `pathlib.Path` for cross-platform compatibility
- ✅ Constants match architecture.md specifications

### Security Notes

- ✅ No credentials logged
- ✅ Partial file cleanup on failure prevents data leakage
- ⚠️ (Low) event_id not sanitized but comes from internal system

### Best-Practices and References

- [Python asyncio.timeout](https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout) - Used correctly for NFR1
- [uiprotect library](https://github.com/uilibs/uiprotect) - get_camera_video() method used
- Project patterns: Follows existing service patterns in `backend/app/services/`

### Action Items

**Advisory Notes:**
- Note: Consider adding event_id validation if external input is ever added (currently low risk)
- Note: Test against real UniFi Protect controller for integration validation

---

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-05 | 1.0 | Senior Developer Review notes appended - APPROVED |
