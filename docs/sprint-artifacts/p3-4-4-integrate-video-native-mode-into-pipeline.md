# Story P3-4.4: Integrate Video Native Mode into Pipeline

Status: review

## Story

As a **system**,
I want **video_native mode to work end-to-end with proper fallback handling**,
So that **cameras configured for video_native analysis receive full video analysis with automatic fallback to multi_frame when needed**.

## Acceptance Criteria

1. **AC1:** Given camera with `analysis_mode='video_native'`, when Protect event is processed, then clip is downloaded, sent directly to video-capable provider (Gemini), and description captures full video narrative.

2. **AC2:** Given video_native analysis succeeds, when event is saved, then `event.analysis_mode = 'video_native'` and `event.frame_count_used = null` (video, not frames).

3. **AC3:** Given video_native provider fails (Gemini error, timeout, etc.), when fallback triggers, then system tries next video-capable provider, and if none available, falls back to multi_frame mode.

4. **AC4:** Given all video providers exhausted, when fallback continues, then system extracts frames using FrameExtractor, uses multi_frame analysis, and `event.fallback_reason` includes `"video_native:all_providers_failed"`.

5. **AC5:** Given video_native mode for non-Protect camera (RTSP/USB), when analysis is attempted, then system immediately falls back to multi_frame (no clip source), and `event.fallback_reason = "video_native:no_clip_source"`.

## Tasks / Subtasks

- [x] **Task 1: Update protect_event_handler video_native routing** (AC: 1, 2)
  - [x] 1.1 Modify `_try_video_native_analysis()` to actually call `_try_video_native_upload()` for Gemini
  - [x] 1.2 Ensure clip download happens before video analysis
  - [x] 1.3 Set `event.analysis_mode = 'video_native'` on success
  - [x] 1.4 Set `event.frame_count_used = None` for video mode

- [x] **Task 2: Implement provider fallback for video analysis** (AC: 3)
  - [x] 2.1 Create video-capable provider iteration list from PROVIDER_CAPABILITIES
  - [x] 2.2 Try each video-capable provider with `video_method='native_upload'` in order
  - [x] 2.3 On provider failure, log and continue to next provider
  - [x] 2.4 Track which providers were tried in `fallback_reason`

- [x] **Task 3: Implement fallback to multi_frame when video fails** (AC: 4)
  - [x] 3.1 After all video providers fail, call `_try_multi_frame_analysis()`
  - [x] 3.2 Use existing clip for frame extraction (don't re-download)
  - [x] 3.3 Set `fallback_reason = "video_native:all_providers_failed,multi_frame:success"` on multi_frame success
  - [x] 3.4 If multi_frame also fails, continue to single_frame fallback

- [x] **Task 4: Handle non-Protect cameras for video_native** (AC: 5)
  - [x] 4.1 Check `camera.source_type` before attempting video download
  - [x] 4.2 For RTSP/USB cameras, skip video_native immediately
  - [x] 4.3 Set `fallback_reason = "video_native:no_clip_source"` for non-Protect
  - [x] 4.4 Route directly to multi_frame for non-Protect cameras with video_native setting

- [x] **Task 5: Add video analysis timeout handling** (AC: 3)
  - [x] 5.1 Set 30-second timeout for video analysis requests
  - [x] 5.2 Handle timeout gracefully with fallback trigger
  - [x] 5.3 Log timeout events with provider and duration

- [x] **Task 6: Write tests** (AC: All)
  - [x] 6.1 Test video_native success path with Gemini mock
  - [x] 6.2 Test provider fallback when first provider fails
  - [x] 6.3 Test multi_frame fallback when all video providers fail
  - [x] 6.4 Test non-Protect camera fallback behavior
  - [x] 6.5 Test timeout handling and fallback trigger
  - [x] 6.6 Test event metadata is set correctly (analysis_mode, frame_count_used, fallback_reason)

## Dev Notes

### Relevant Architecture Patterns and Constraints

**From Phase 3 Architecture:**
- Fallback chain: `video_native -> multi_frame -> single_frame`
- Video-capable providers: Gemini (native_upload method), OpenAI (frame_extraction method)
- For video_native mode, only Gemini has true native upload capability
- OpenAI "video" support is actually frame extraction, not native video upload

**From PROVIDER_CAPABILITIES (ai_service.py):**
```python
"gemini": {
    "video": True,
    "video_method": "native_upload",
    "max_video_duration": 300,  # 5 min
    "max_video_size_mb": 2048,  # 2GB via File API
    "inline_max_size_mb": 20,   # For inline data
}
```

**Event Pipeline Flow:**
```
video_native mode requested
    -> Download clip (ClipService)
    -> Try Gemini video upload (AIService.describe_video)
    -> On failure: Try next video provider
    -> All video providers failed: Extract frames (FrameExtractor)
    -> Multi-frame analysis (AIService.describe_images)
    -> On failure: Single-frame fallback
```

### Source Tree Components to Touch

**Backend:**
- `backend/app/services/protect_event_handler.py` - Main routing logic for video_native mode
- `backend/app/services/ai_service.py` - AIService.describe_video() already implemented in P3-4.3
- `backend/tests/test_services/test_protect_event_handler.py` - Integration tests

### Testing Standards Summary

- Mock external API calls (Gemini, OpenAI)
- Test success and failure paths
- Test fallback chain behavior
- Verify event metadata is set correctly
- Use pytest fixtures for common test setup

[Source: docs/architecture.md#Phase-3-Fallback-Chain]
[Source: docs/epics-phase3.md#Story-P3-4.4]

### Project Structure Notes

- Alignment with unified project structure: All modifications in existing service files
- No new files needed - extending protect_event_handler.py
- Test file location: `backend/tests/test_services/test_protect_event_handler.py`

### References

- [Source: docs/epics-phase3.md#Story-P3-4.4] - Story requirements
- [Source: docs/architecture.md#Phase-3-Event-Processing-Flow] - Event flow diagram
- [Source: docs/architecture.md#Phase-3-Fallback-Chain] - Fallback chain description
- [Source: backend/app/services/ai_service.py:116-136] - PROVIDER_CAPABILITIES
- [Source: backend/app/services/protect_event_handler.py] - Event handler to modify

### Learnings from Previous Story

**From Story p3-4-3-implement-video-upload-to-gemini (Status: review)**

- **GeminiProvider.describe_video() Implemented**: Native video upload with two methods:
  - Inline data for videos under 20MB (fast, no server upload)
  - File API for videos 20MB-2GB (upload to Google servers, poll for processing)

- **AIService.describe_video() Implemented**: Orchestration method that:
  - Routes to video-capable providers with native_upload method only
  - Handles provider fallback on failure
  - Tracks usage with video_native analysis mode

- **PROVIDER_CAPABILITIES Updated**:
  - max_video_size_mb: 2048 (2GB via File API)
  - max_video_duration: 300 (5 min practical limit)
  - inline_max_size_mb: 20 (for inline data method)
  - supports_audio: True (Gemini natively processes video audio)

- **protect_event_handler integration**: `_try_video_native_upload()` method added for native_upload video_method routing

- **Key Files Created/Modified**:
  - `backend/app/services/ai_service.py` - GeminiProvider.describe_video(), AIService.describe_video()
  - `backend/app/services/protect_event_handler.py` - _try_video_native_upload()
  - `backend/tests/test_services/test_ai_service.py` - 16 new tests

- **Critical Finding from P3-4.2**: Only Gemini supports native video file upload. OpenAI does NOT support video upload via API - it uses frame extraction.

[Source: docs/sprint-artifacts/p3-4-3-implement-video-upload-to-gemini.md#Dev-Agent-Record]

### Implementation Notes

**Existing Code to Leverage (from P3-4.3):**
1. `_try_video_native_upload()` in protect_event_handler.py - calls Gemini directly
2. `AIService.describe_video()` - orchestration with provider fallback
3. `GeminiProvider.describe_video()` - actual video upload implementation

**What This Story Adds:**
1. End-to-end integration testing
2. Proper fallback to multi_frame when video fails
3. Non-Protect camera handling
4. Timeout handling
5. Comprehensive test coverage for the full pipeline

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p3-4-4-integrate-video-native-mode-into-pipeline.context.xml

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Tests run: `python -m pytest tests/test_services/test_fallback_chain.py -v` - 21 passed
- Full test suite: `python -m pytest tests/ --tb=no -q` - 1004 tests collected, all passed

### Completion Notes List

1. **Video native metadata tracking implemented**: Added `_last_analysis_mode = "video_native"` and `_last_frame_count = None` on successful video analysis in both `_try_video_native_upload()` and `_try_video_frame_extraction()` methods.

2. **30-second timeout implemented**: Added `asyncio.wait_for()` with `VIDEO_ANALYSIS_TIMEOUT_SECONDS = 30` constant. Timeout triggers fallback with reason `video_native:timeout`.

3. **Non-Protect camera fallback reasons**: Added proper fallback_reason tracking for RTSP/USB cameras:
   - `video_native:no_clip_source` for video_native mode on non-Protect cameras
   - `multi_frame:no_clip_source` for multi_frame mode on non-Protect cameras

4. **Exception handling improved**: Added `asyncio.TimeoutError` handler and generic exception handler that captures exception type in fallback_reason (e.g., `video_native:exception:ValueError`).

5. **Test coverage added**: 10 new tests in 4 new test classes covering all ACs:
   - `TestVideoNativeSuccessMetadata` - AC1, AC2
   - `TestVideoNativeTimeoutHandling` - AC3 (timeout)
   - `TestNonProtectCameraFallbackReason` - AC5
   - `TestVideoNativeProviderFailure` - AC3 (provider errors)

### File List

**Modified:**
- `backend/app/services/protect_event_handler.py` - Added timeout handling, metadata tracking, exception handlers
- `backend/tests/test_services/test_fallback_chain.py` - Added 10 new tests for P3-4.4 ACs

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-07 | 1.0 | Story drafted from epics-phase3.md with context from P3-4.3 learnings |
| 2025-12-07 | 1.1 | Implementation complete - all tasks done, tests passing |
