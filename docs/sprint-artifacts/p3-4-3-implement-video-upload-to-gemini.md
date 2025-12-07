# Story P3-4.3: Implement Video Upload to Gemini

Status: done

## Story

As a **system**,
I want **to send video clips to Google Gemini**,
So that **users get video-native analysis from Gemini for the highest quality event descriptions**.

## Acceptance Criteria

1. **AC1:** Given a video clip under 20MB, when `GeminiProvider.describe_video()` is called, then video is sent as inline_data base64, and description is returned. For larger videos (20MB-2GB), use File API upload approach.

2. **AC2:** Given video needs format conversion for Gemini, when original format unsupported, then converts to supported format (mp4/mov/webm) using PyAV, and retries with converted file.

3. **AC3:** Given Gemini video analysis completes, when response is received, then token usage is tracked, and cost estimate is calculated.

4. **AC4:** Given Gemini provider is configured with valid API key, when `describe_video()` is called with valid clip path, then method succeeds and returns AIResult with description.

5. **AC5:** Given video exceeds Gemini limits (>2GB via File API), when video analysis is attempted, then returns AIResult with success=False, and error message indicates size exceeded, and triggers fallback to multi_frame.

## Tasks / Subtasks

- [x] **Task 1: Research Gemini Video API** (AC: All)
  - [x] 1.1 Verify Gemini 1.5 Flash/Pro video input format requirements
  - [x] 1.2 Confirm file upload vs inline base64 approach
  - [x] 1.3 Document size limits, duration limits, and supported formats
  - [x] 1.4 Identify model requirements (gemini-1.5-flash vs gemini-1.5-pro)

- [x] **Task 2: Implement `describe_video()` method in GeminiProvider** (AC: 1, 4)
  - [x] 2.1 Add `describe_video()` async method to GeminiProvider class
  - [x] 2.2 Read video file and convert to Gemini-compatible format
  - [x] 2.3 Use genai library to send video content with prompt
  - [x] 2.4 Parse response and return AIResult

- [x] **Task 3: Add video size/duration validation** (AC: 5)
  - [x] 3.1 Validate file exists and check size
  - [x] 3.2 Check file size against max_video_size_mb from PROVIDER_CAPABILITIES (2GB)
  - [x] 3.3 Get video duration using PyAV for token estimation
  - [x] 3.4 Return early with descriptive error if limits exceeded

- [x] **Task 4: Implement video format conversion** (AC: 2)
  - [x] 4.1 Add `_convert_video_format()` method using PyAV
  - [x] 4.2 Support conversion to MP4/H.264 (most compatible)
  - [x] 4.3 Add `_is_supported_video_format()` validation
  - [x] 4.4 Clean up converted file after use in finally block

- [x] **Task 5: Add token/cost tracking for video requests** (AC: 3)
  - [x] 5.1 Token estimation: 150 base + (frames * 258) per frame at 1fps
  - [x] 5.2 Cost calculation using COST_RATES for gemini
  - [x] 5.3 Integrated into AIResult returned by describe_video()

- [x] **Task 6: Update `_try_video_native_analysis()` in protect_event_handler** (AC: All)
  - [x] 6.1 Added `_try_video_native_upload()` method for native_upload video_method
  - [x] 6.2 Call gemini_provider.describe_video() directly
  - [x] 6.3 Handle success/failure with proper fallback chain updates
  - [x] 6.4 Track analysis_mode as "video_native" on success

- [x] **Task 7: Add AIService orchestration for describe_video** (AC: All)
  - [x] 7.1 Add `describe_video()` method to AIService class
  - [x] 7.2 Route to video-capable providers with native_upload method only
  - [x] 7.3 Handle provider fallback for video analysis
  - [x] 7.4 Track usage with video_native analysis mode

- [x] **Task 8: Write tests** (AC: All)
  - [x] 8.1 Unit test GeminiProvider.describe_video() with mocked genai (13 tests)
  - [x] 8.2 Unit test video validation (size/duration limits)
  - [x] 8.3 Unit test format conversion triggers and error handling
  - [x] 8.4 Unit test AIService.describe_video() routing (2 tests)
  - [x] 8.5 Unit test format validation (supported/unsupported formats)

## Dev Notes

### Research Findings (2025-12-07)

**Gemini API DOES support native video upload for descriptions, summaries, and analysis.**

There are two primary methods depending on file size:

#### Method 1: File API (Recommended for most videos)

For videos larger than 20MB (up to 2GB):
1. **Upload:** Use `genai.upload_file(path=clip_path)` to upload to Google's servers
2. **Wait:** Poll until `video_file.state.name != "PROCESSING"`
3. **Generate:** Pass the file reference to `generate_content()`

- **Max Size:** Up to 2GB per file
- **Storage:** Files stored temporarily (48 hours) then auto-deleted

```python
import google.generativeai as genai
import time

# 1. Upload the video
video_file = genai.upload_file(path="path/to/video.mp4")

# Wait for processing to complete (important for videos)
while video_file.state.name == "PROCESSING":
    print("Processing video...")
    time.sleep(5)
    video_file = genai.get_file(video_file.name)

if video_file.state.name == "FAILED":
    raise ValueError(video_file.state.name)

# 2. Generate the description
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    "Describe exactly what is happening in this video in detail.",
    video_file
])
print(response.text)
```

#### Method 2: Inline Data (for small videos < 20MB)

For very short, small video clips under 20MB:
- Pass video data directly as base64-encoded string in request payload
- Best for real-time applications with small snippets
- Total request payload (video + text) cannot exceed 20MB

```python
video_bytes = Path(clip_path).read_bytes()
video_part = {"mime_type": "video/mp4", "data": video_bytes}

response = await model.generate_content_async([prompt, video_part])
```

### Key Technical Details

| Aspect | Value |
|--------|-------|
| **Supported Models** | Gemini 1.5 Flash, Gemini 1.5 Pro |
| **Max File Size (File API)** | 2GB |
| **Max Inline Size** | 20MB |
| **File Storage Duration** | 48 hours |
| **Token Usage** | ~258 tokens/frame at 1fps |
| **Audio Support** | Yes - models can "hear" video audio |

### Implementation Decision

For security camera clips (typically 10-30 seconds, 5-20MB):
- **Use inline_data** for clips under 20MB (most common case)
- **Use File API** for clips over 20MB as fallback
- This avoids the upload/polling overhead for typical clips

### PROVIDER_CAPABILITIES Update Required

```python
"gemini": {
    "video": True,
    "video_method": "native_upload",
    "max_video_duration": 300,  # 5 min practical limit (tokens)
    "max_video_size_mb": 2048,  # 2GB via File API
    "inline_max_size_mb": 20,   # NEW: Inline data limit
    "max_frames": 0,  # N/A for native upload
    "supported_formats": ["mp4", "mov", "webm", "avi", "flv", "mpg", "mpeg", "wmv"],
    "max_images": 16,
    "supports_audio": True,  # NEW: Native audio support
}
```

### Key Implementation Patterns from Previous Stories

**From P3-4.1 (Provider Capability Detection):**
- PROVIDER_CAPABILITIES dict at `ai_service.py:94-136` defines video support
- Use `ai_service.get_video_capable_providers()` to get list of video-capable providers
- Use `ai_service.supports_video(provider)` to check if specific provider supports video

**From P3-4.2 (OpenAI Frame Extraction):**
- OpenAI uses frame extraction (video_method: "frame_extraction")
- Gemini uses native upload (video_method: "native_upload")
- Current `_try_video_native_analysis()` routes based on video_method
- Fallback chain: video_native -> multi_frame -> single_frame

**From P3-2.3/P3-2.6 (Multi-Image Implementation):**
- GeminiProvider.generate_multi_image_description() shows pattern for multi-part content
- Use `genai.GenerativeModel('gemini-1.5-flash')`
- Pass parts array with prompt + media to `generate_content_async()`

### Video-Specific Prompt Considerations

For video analysis, prompt should emphasize temporal narrative:
- Reference MULTI_FRAME_SYSTEM_PROMPT pattern from P3-2.4
- Add video-specific context: "This is a video clip from a security camera"
- Request action-based descriptions

### Files to Modify

1. `backend/app/services/ai_service.py`
   - Add `describe_video()` to GeminiProvider class
   - Add `describe_video()` to AIService class for orchestration

2. `backend/app/services/protect_event_handler.py`
   - Update `_try_video_native_analysis()` to call actual Gemini video analysis

3. `backend/tests/test_services/test_ai_service.py`
   - Add video analysis tests

### Project Structure Notes

- Video processing uses PyAV (av library) - already in requirements
- ClipService downloads clips to `data/clips/{event_id}.mp4`
- Format conversion should use same library for consistency

### Error Handling

- Gemini quota exceeded: Return error, don't retry
- Network timeout: Retry once, then fallback
- Invalid video format: Try conversion, then fallback
- Empty/corrupt video: Return error immediately

### References

- [Source: docs/epics-phase3.md#Story-P3-4.3]
- [Source: backend/app/services/ai_service.py:116-123] - Gemini PROVIDER_CAPABILITIES
- [Source: backend/app/services/ai_service.py:776-945] - GeminiProvider class
- [Source: backend/app/services/protect_event_handler.py:1093-1114] - _try_video_native_analysis placeholder
- [Source: docs/sprint-artifacts/p3-4-2-implement-video-upload-to-openai.md] - OpenAI research findings

### Learnings from Previous Story

**From Story p3-4-2-implement-video-upload-to-openai (Status: done)**

- **Critical Finding**: Only Gemini supports native video file upload. OpenAI does NOT support video upload via API.
- **Capability Update**: PROVIDER_CAPABILITIES already correctly shows Gemini `video: true` with 60s/20MB limits
- **Fallback Placeholder**: Current code at protect_event_handler.py:1099-1100 sets `reason = "video_upload_not_implemented"` - this story will replace this with actual Gemini video analysis
- **Testing Pattern**: Tests in test_ai_service.py verify capability detection - extend for actual video analysis

[Source: docs/sprint-artifacts/p3-4-2-implement-video-upload-to-openai.md#Dev-Agent-Record]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-4-3-implement-video-upload-to-gemini.context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 131 AI service tests pass (115 original + 16 new)

### Completion Notes List

1. **GeminiProvider.describe_video()** - Implemented native video upload with two methods:
   - Inline data for videos under 20MB (fast, no server upload)
   - File API for videos 20MB-2GB (upload to Google servers, poll for processing)

2. **Video Format Validation & Conversion** - Added support for:
   - `_is_supported_video_format()` checks against PROVIDER_CAPABILITIES formats
   - `_convert_video_format()` converts unsupported formats to MP4/H.264 using PyAV
   - Automatic cleanup of converted files after use

3. **Token Estimation** - Video tokens estimated at:
   - 150 base tokens + (video_duration_seconds * 258 tokens/frame at 1fps)
   - Cost calculated using COST_RATES for gemini

4. **PROVIDER_CAPABILITIES Updated**:
   - max_video_size_mb: 2048 (2GB via File API)
   - max_video_duration: 300 (5 min practical limit)
   - inline_max_size_mb: 20 (for inline data method)
   - supports_audio: True (Gemini natively processes video audio)

5. **AIService.describe_video()** - Added orchestration method that:
   - Routes to video-capable providers with native_upload method
   - Handles provider fallback on failure
   - Tracks usage with video_native analysis mode

6. **protect_event_handler integration** - Added `_try_video_native_upload()` for native video upload routing

### File List

- `backend/app/services/ai_service.py` - GeminiProvider.describe_video(), AIService.describe_video(), PROVIDER_CAPABILITIES
- `backend/app/services/protect_event_handler.py` - _try_video_native_upload()
- `backend/tests/test_services/test_ai_service.py` - 16 new tests (TestGeminiDescribeVideo, TestAIServiceDescribeVideo, TestGeminiVideoFormatConversion)
- `docs/sprint-artifacts/p3-4-3-implement-video-upload-to-gemini.md` - This story file
- `docs/sprint-artifacts/p3-4-3-implement-video-upload-to-gemini.context.xml` - Story context

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-07 | 1.0 | Story drafted from epics-phase3.md with context from P3-4.1 and P3-4.2 |
| 2025-12-07 | 1.1 | Research complete - Gemini supports 2 methods: File API (up to 2GB) and inline_data (<20MB). Task 1 marked complete. ACs updated to reflect actual API capabilities. |
| 2025-12-07 | 2.0 | Implementation complete - All 8 tasks done. GeminiProvider.describe_video(), format conversion, AIService orchestration, 16 new tests. Status: review |
| 2025-12-07 | 3.0 | Senior Developer Review: APPROVED. All 5 ACs verified, all 8 tasks validated, 19 tests pass. Status: done |

## Senior Developer Review (AI)

### Reviewer
Brent

### Date
2025-12-07

### Outcome
**APPROVE** - All acceptance criteria implemented with evidence. All tasks verified complete. 19 tests pass.

### Summary
Story P3-4.3 implements native video upload to Google Gemini for the highest quality event descriptions. Implementation includes two upload methods (inline data for <20MB, File API for 20MB-2GB), format conversion with PyAV, token/cost tracking, and full orchestration through AIService.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- [ ] [Low] Replace deprecated `datetime.utcnow()` with `datetime.now(datetime.UTC)` [file: backend/app/services/ai_service.py:2739]

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Videos <20MB use inline_data; >20MB use File API | IMPLEMENTED | `ai_service.py:1364-1373` |
| AC2 | Format conversion for unsupported formats | IMPLEMENTED | `ai_service.py:1321-1345,1661-1755` |
| AC3 | Token usage tracking and cost estimation | IMPLEMENTED | `ai_service.py:1439-1442,1559-1562` |
| AC4 | describe_video() returns AIResult on success | IMPLEMENTED | `ai_service.py:1462-1471,1588-1596` |
| AC5 | Videos >2GB return error with fallback | IMPLEMENTED | `ai_service.py:1294-1316` |

**Summary: 5 of 5 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Research Gemini Video API | Complete | VERIFIED | Story Dev Notes lines 75-146 |
| Task 2: Implement describe_video() | Complete | VERIFIED | `ai_service.py:1220-1408` |
| Task 3: Add size/duration validation | Complete | VERIFIED | `ai_service.py:1288-1316,1599-1617` |
| Task 4: Format conversion | Complete | VERIFIED | `ai_service.py:1661-1755` |
| Task 5: Token/cost tracking | Complete | VERIFIED | `ai_service.py:1439-1442` |
| Task 6: Update protect_event_handler | Complete | VERIFIED | `protect_event_handler.py:1166` |
| Task 7: AIService orchestration | Complete | VERIFIED | `ai_service.py:2708-2875` |
| Task 8: Write tests | Complete | VERIFIED | 19 Gemini video tests pass |

**Summary: 8 of 8 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

- **Tests Added:** 19 tests covering all ACs
- **Test Classes:** TestGeminiDescribeVideo, TestAIServiceDescribeVideo, TestGeminiVideoFormatConversion
- **Coverage:** AC1-AC5 all have corresponding tests
- **Gaps:** None identified

### Architectural Alignment

- ✅ Follows existing GeminiProvider pattern
- ✅ Uses PROVIDER_CAPABILITIES for limits
- ✅ Proper async/await throughout
- ✅ Structured logging with extra dict
- ✅ Resource cleanup in finally blocks

### Security Notes

- ✅ No API keys logged
- ✅ Input validation on file paths
- ✅ Temp files cleaned up properly

### Best-Practices and References

- [Google AI Gemini Video Documentation](https://ai.google.dev/gemini-api/docs/vision?lang=python#video)
- Token estimation: ~258 tokens/frame at 1fps per Gemini documentation

### Action Items

**Code Changes Required:**
- [ ] [Low] Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)` [file: backend/app/services/ai_service.py:2739]

**Advisory Notes:**
- Note: File API uploaded videos are auto-deleted after 48 hours by Google - no action needed
