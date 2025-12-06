# Story P3-2.3: Extend AIService for Multi-Image Analysis

Status: done

## Story

As a **system**,
I want **AIService to accept multiple images in one request**,
So that **AI can analyze frame sequences together for richer descriptions**.

## Acceptance Criteria

1. **AC1:** Given a list of 3-5 image bytes, when `AIService.describe_images(images: List[bytes], prompt: str)` is called, then all images are sent to the AI provider in a single request and returns a single description covering all frames
2. **AC2:** Given multi-image request to OpenAI, when API is called, then images are sent as multiple image_url content blocks and each image is base64 encoded with proper MIME type
3. **AC3:** Given multi-image request to Claude, when API is called, then images are sent as multiple image content blocks and uses claude-3-haiku or configured model
4. **AC4:** Given multi-image request to Gemini, when API is called, then images are sent using Gemini's multi-part format and handles Gemini's specific image requirements
5. **AC5:** Given multi-image request to Grok, when API is called, then images are sent using Grok's vision API format (OpenAI-compatible)

## Tasks / Subtasks

- [x] **Task 1: Add describe_images method to AIProviderBase** (AC: 1)
  - [x] 1.1 Add abstract method `generate_multi_image_description(images: List[str], ...)` to AIProviderBase
  - [x] 1.2 Define method signature matching existing `generate_description` pattern
  - [x] 1.3 Add docstring explaining multi-image usage and expected format

- [x] **Task 2: Implement multi-image for OpenAI provider** (AC: 2)
  - [x] 2.1 Add `generate_multi_image_description` to OpenAIProvider class
  - [x] 2.2 Build message content array with multiple image_url objects
  - [x] 2.3 Each image as `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{base64}"}}`
  - [x] 2.4 Handle response and extract description
  - [x] 2.5 Track token usage for multi-image requests

- [x] **Task 3: Implement multi-image for Grok provider** (AC: 5)
  - [x] 3.1 Add `generate_multi_image_description` to GrokProvider class
  - [x] 3.2 Use OpenAI-compatible format (same as Task 2)
  - [x] 3.3 Verify Grok supports multiple images in single request
  - [x] 3.4 Handle grok-2-vision-1212 model specifics

- [x] **Task 4: Implement multi-image for Claude provider** (AC: 3)
  - [x] 4.1 Add `generate_multi_image_description` to ClaudeProvider class
  - [x] 4.2 Build content array with multiple image blocks using Anthropic format
  - [x] 4.3 Each image as `{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64}}`
  - [x] 4.4 Handle Claude-specific response format
  - [x] 4.5 Track token usage

- [x] **Task 5: Implement multi-image for Gemini provider** (AC: 4)
  - [x] 5.1 Add `generate_multi_image_description` to GeminiProvider class
  - [x] 5.2 Build contents array with inline_data parts for each image
  - [x] 5.3 Each image as `{"inline_data": {"mime_type": "image/jpeg", "data": base64}}`
  - [x] 5.4 Handle Gemini's multi-part response format
  - [x] 5.5 Track token usage (estimate if not provided)

- [x] **Task 6: Add describe_images to AIService facade** (AC: 1)
  - [x] 6.1 Add `describe_images(images: List[bytes], camera_name: str, timestamp: str, detected_objects: List[str], custom_prompt: Optional[str]) -> AIResult` method
  - [x] 6.2 Preprocess all images (resize, JPEG encode, base64)
  - [x] 6.3 Call provider's `generate_multi_image_description` with fallback chain
  - [x] 6.4 Return AIResult with combined description

- [x] **Task 7: Write unit tests** (AC: All)
  - [x] 7.1 Test describe_images with mocked OpenAI returning combined description
  - [x] 7.2 Test describe_images with mocked Claude returning combined description
  - [x] 7.3 Test describe_images with mocked Gemini returning combined description
  - [x] 7.4 Test describe_images with mocked Grok returning combined description
  - [x] 7.5 Test fallback chain works for multi-image requests
  - [x] 7.6 Test image preprocessing for multiple images
  - [x] 7.7 Test token usage tracking for multi-image

## Dev Notes

### Architecture References

- **AIService Extension**: Add `describe_images()` method to existing `AIService` class in `backend/app/services/ai_service.py`
- **Provider Pattern**: Follow existing `AIProviderBase` abstract class pattern with each provider implementing `generate_multi_image_description`
- **Fallback Chain**: Use existing provider fallback logic (OpenAI → Grok → Claude → Gemini)
- [Source: docs/architecture.md#Phase-3-Service-Architecture]
- [Source: docs/epics-phase3.md#Story-P3-2.3]

### Project Structure Notes

- Modify existing service: `backend/app/services/ai_service.py`
- Add tests to: `backend/tests/test_services/test_ai_service.py`
- All AI provider libraries are already installed (openai, anthropic, google-generativeai)

### Implementation Guidance

1. **OpenAI Multi-Image Format:**
   ```python
   messages = [{
       "role": "user",
       "content": [
           {"type": "text", "text": prompt},
           {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1}"}},
           {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2}"}},
           # ... more images
       ]
   }]
   ```

2. **Claude Multi-Image Format:**
   ```python
   content = [
       {"type": "text", "text": prompt},
       {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img1}},
       {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img2}},
       # ... more images
   ]
   ```

3. **Gemini Multi-Image Format:**
   ```python
   parts = [
       {"text": prompt},
       {"inline_data": {"mime_type": "image/jpeg", "data": img1}},
       {"inline_data": {"mime_type": "image/jpeg", "data": img2}},
       # ... more images
   ]
   ```

4. **Image Preprocessing:**
   - Reuse existing `_preprocess_image()` from AIService
   - Apply to each image in the list before sending

### Learnings from Previous Story

**From Story p3-2-2-add-blur-detection-for-frame-filtering (Status: done)**

- **FrameExtractor Now Available**: Use `FrameExtractor.extract_frames()` to get quality-filtered frames as bytes
- **Frame Quality Filtering**: Frames returned from FrameExtractor are already filtered for blur (Laplacian variance ≥ 100)
- **Configuration Constants**: Follow module-level constant pattern (from blur detection)
- **Structured Logging**: Use `extra={}` dict pattern for all log calls
- **Test Coverage**: 54 tests in test_frame_extractor.py - follow similar patterns for AI tests
- **Existing AIService Patterns**: Use existing `_preprocess_image()`, `_encode_image()`, `_calculate_cost()` methods

**Files to REUSE (not recreate):**
- `backend/app/services/ai_service.py` - Add new methods here
- `backend/app/services/frame_extractor.py` - Provides frames for multi-image analysis
- `backend/tests/test_services/test_ai_service.py` - Add new tests here

[Source: docs/sprint-artifacts/p3-2-2-add-blur-detection-for-frame-filtering.md#Dev-Agent-Record]

### Testing Standards

- Add tests to existing `backend/tests/test_services/test_ai_service.py`
- Mock all AI provider API calls (no real API calls in tests)
- Test each provider's multi-image format independently
- Test fallback behavior when primary provider fails
- Follow existing test patterns in test_ai_service.py

### References

- [Source: docs/architecture.md#AIService]
- [Source: docs/epics-phase3.md#Story-P3-2.3]
- [Source: docs/sprint-artifacts/p3-2-2-add-blur-detection-for-frame-filtering.md]
- OpenAI Vision API: https://platform.openai.com/docs/guides/vision
- Anthropic Claude Vision: https://docs.anthropic.com/en/docs/build-with-claude/vision
- Google Gemini Vision: https://ai.google.dev/gemini-api/docs/vision

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p3-2-3-extend-aiservice-for-multi-image-analysis.context.xml`

### Agent Model Used

- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **All 5 Acceptance Criteria Satisfied**:
  - AC1: `AIService.describe_images()` accepts list of image bytes and returns single combined description covering all frames
  - AC2: OpenAI multi-image uses multiple `image_url` content blocks with base64 encoded images
  - AC3: Claude multi-image uses multiple `image` blocks with `source.type=base64` and `media_type=image/jpeg`
  - AC4: Gemini multi-image uses multiple `inline_data` parts with `mime_type` and decoded bytes
  - AC5: Grok uses OpenAI-compatible format with multiple `image_url` content blocks
- **Implementation approach**: Extended AIProviderBase with abstract `generate_multi_image_description()` method; each provider implements with their specific API format
- **Multi-image prompt builder**: Added `_build_multi_image_prompt()` to generate sequence-aware prompts mentioning frame count
- **Image preprocessing**: Added `_preprocess_image_bytes()` for raw bytes input from FrameExtractor (resize to 2048, JPEG encode, base64)
- **Fallback chain**: Uses existing provider order (OpenAI → Grok → Claude → Gemini) with `_try_multi_image_with_backoff()`
- **SLA enforcement**: 10s default timeout for multi-image requests (longer than 5s single-image)
- **Structured logging**: All log calls use `extra={}` dict pattern per project standards
- **Test coverage**: 19 new tests added (54 total in test_ai_service.py), all passing

### File List

- `backend/app/services/ai_service.py` - Extended with multi-image analysis
  - Added `generate_multi_image_description()` abstract method to AIProviderBase (lines 104-128)
  - Added `_build_multi_image_prompt()` helper method (lines 158-194)
  - Added `generate_multi_image_description()` to OpenAIProvider (lines 380-484)
  - Added `generate_multi_image_description()` to ClaudeProvider (lines 585-692)
  - Added `generate_multi_image_description()` to GeminiProvider (lines 772-864)
  - Added `generate_multi_image_description()` to GrokProvider (lines 881-988)
  - Added `describe_images()` facade method to AIService (lines 1452-1695)
  - Added `_preprocess_image_bytes()` method (lines 1743-1799)
  - Added `_try_multi_image_with_backoff()` method (lines 1858-1933)
- `backend/tests/test_services/test_ai_service.py` - Added 19 new multi-image tests
  - Added `sample_image_bytes` and `sample_image_bytes_list` fixtures
  - Added `TestMultiImagePreprocessing` class (3 tests)
  - Added `TestMultiImagePromptBuilder` class (3 tests)
  - Added `TestOpenAIMultiImageProvider` class (2 tests)
  - Added `TestGrokMultiImageProvider` class (1 test)
  - Added `TestClaudeMultiImageProvider` class (1 test)
  - Added `TestGeminiMultiImageProvider` class (1 test)
  - Added `TestDescribeImagesMethod` class (4 tests)
  - Added `TestMultiImageFallbackChain` class (2 tests)
  - Added `TestMultiImageRetryLogic` class (1 test)
  - Added `TestMultiImageUsageTracking` class (1 test)

## Senior Developer Review (AI)

### Reviewer
- Brent

### Date
- 2025-12-06

### Outcome
- **APPROVE** - All 5 acceptance criteria fully implemented with comprehensive test coverage

### Summary
Story P3-2.3 successfully extends the AIService to support multi-image analysis, enabling AI providers to analyze frame sequences together for richer descriptions. The implementation follows existing patterns, provides proper fallback chain support, and includes 19 new tests (54 total in test_ai_service.py). All 7 tasks are verified complete.

### Key Findings
**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- Note: The `_preprocess_image_bytes()` method (lines 1743-1799) is similar to `_preprocess_image()` but accepts bytes instead of numpy array. This is acceptable duplication given the different input types.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | AIService.describe_images() accepts List[bytes], returns combined description | IMPLEMENTED | `ai_service.py:1452-1695` |
| AC2 | OpenAI uses multiple image_url content blocks with base64 | IMPLEMENTED | `ai_service.py:380-484` |
| AC3 | Claude uses multiple image blocks with source.type=base64 | IMPLEMENTED | `ai_service.py:585-692` |
| AC4 | Gemini uses inline_data parts with mime_type and data | IMPLEMENTED | `ai_service.py:772-864` |
| AC5 | Grok uses OpenAI-compatible format | IMPLEMENTED | `ai_service.py:881-988` |

**Summary: 5 of 5 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Add abstract method to AIProviderBase | [x] | ✓ VERIFIED | `ai_service.py:104-128` |
| Task 2: Implement multi-image for OpenAI | [x] | ✓ VERIFIED | `ai_service.py:380-484` |
| Task 3: Implement multi-image for Grok | [x] | ✓ VERIFIED | `ai_service.py:881-988` |
| Task 4: Implement multi-image for Claude | [x] | ✓ VERIFIED | `ai_service.py:585-692` |
| Task 5: Implement multi-image for Gemini | [x] | ✓ VERIFIED | `ai_service.py:772-864` |
| Task 6: Add describe_images to AIService | [x] | ✓ VERIFIED | `ai_service.py:1452-1695` |
| Task 7: Write unit tests | [x] | ✓ VERIFIED | `test_ai_service.py:1115-1766` (19 tests) |

**Summary: 7 of 7 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps
- **Excellent coverage**: 19 new tests added for P3-2.3 functionality
- **Total tests**: 54 tests in test_ai_service.py, all passing
- **Test classes added**:
  - `TestMultiImagePreprocessing` (3 tests) - image bytes preprocessing
  - `TestMultiImagePromptBuilder` (3 tests) - multi-frame prompt generation
  - `TestOpenAIMultiImageProvider` (2 tests) - OpenAI multi-image
  - `TestGrokMultiImageProvider` (1 test) - Grok multi-image
  - `TestClaudeMultiImageProvider` (1 test) - Claude multi-image
  - `TestGeminiMultiImageProvider` (1 test) - Gemini multi-image
  - `TestDescribeImagesMethod` (4 tests) - facade method
  - `TestMultiImageFallbackChain` (2 tests) - fallback behavior
  - `TestMultiImageRetryLogic` (1 test) - retry with backoff
  - `TestMultiImageUsageTracking` (1 test) - usage tracking
- **No gaps identified**

### Architectural Alignment
- ✓ Extends existing `AIProviderBase` with abstract method (follows pattern)
- ✓ Each provider implements `generate_multi_image_description()` (polymorphism)
- ✓ Uses existing fallback chain logic (OpenAI → Grok → Claude → Gemini)
- ✓ Added `_preprocess_image_bytes()` for bytes input from FrameExtractor
- ✓ Uses structured logging with `extra={}` dict per project standards
- ✓ 10s SLA timeout for multi-image (appropriate for longer processing)

### Security Notes
- No security concerns identified. Multi-image analysis uses same encrypted API key handling as single-image.

### Best-Practices and References
- OpenAI Vision API multi-image format verified: https://platform.openai.com/docs/guides/vision
- Anthropic Claude Vision multi-image verified: https://docs.anthropic.com/en/docs/build-with-claude/vision
- Google Gemini multi-part content verified: https://ai.google.dev/gemini-api/docs/vision

### Action Items

**Code Changes Required:**
- None

**Advisory Notes:**
- Note: Consider adding multi-image token cost estimation per provider for budget tracking (future enhancement)

