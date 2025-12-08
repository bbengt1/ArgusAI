# Story P3-5.1: Implement Audio Extraction from Video Clips

## Story

**As a** system,
**I want** to extract audio tracks from video clips,
**So that** audio can be analyzed separately for speech transcription in doorbell events.

## Status: review

## Acceptance Criteria

### AC1: Extract Audio from Video Clip with Audio Track
- [x] Given a video clip with an audio track
- [x] When `AudioExtractor.extract_audio(clip_path)` is called
- [x] Then returns audio as WAV bytes (16kHz, mono)
- [x] And extraction completes within 2 seconds

### AC2: Handle Video Clips Without Audio Track
- [x] Given a video clip with no audio track
- [x] When extraction is attempted
- [x] Then returns None
- [x] And logs "No audio track found in clip"

### AC3: Handle Silent Audio Tracks
- [x] Given audio track exists but is completely silent
- [x] When extraction and analysis occur
- [x] Then returns audio bytes (let downstream transcription handle silence)
- [x] And logs audio level metrics for diagnostics

### AC4: Singleton Pattern and Initialization
- [x] AudioExtractor follows singleton pattern matching FrameExtractor
- [x] Provides `get_audio_extractor()` function
- [x] Provides `reset_audio_extractor()` function for testing

### AC5: Audio Level Detection
- [x] Detect if extracted audio has content (not silent)
- [x] Calculate RMS level or peak amplitude
- [x] Log audio level for diagnostics

## Tasks / Subtasks

- [x] **Task 1: Create AudioExtractor Service** (AC: 1, 4)
  - [x] Create `backend/app/services/audio_extractor.py`
  - [x] Implement `AudioExtractor` class with singleton pattern (matching FrameExtractor)
  - [x] Add `get_audio_extractor()` and `reset_audio_extractor()` functions
  - [x] Configure logging with structured JSON format

- [x] **Task 2: Implement extract_audio Method** (AC: 1, 2, 3)
  - [x] Use PyAV (`av` library) to open video container
  - [x] Check for audio stream: `container.streams.audio[0]`
  - [x] If no audio stream, return None and log appropriately (AC2)
  - [x] Decode audio frames and resample to 16kHz mono WAV
  - [x] Use io.BytesIO to create WAV bytes in memory
  - [x] Ensure extraction completes within 2 seconds (performance requirement)

- [x] **Task 3: Implement Audio Level Detection** (AC: 3, 5)
  - [x] Calculate RMS level or peak amplitude from decoded audio
  - [x] Log audio level metrics for diagnostics
  - [x] Define silence threshold (e.g., RMS < -50dB)
  - [x] Return audio bytes even if silent (downstream handles silence)

- [x] **Task 4: Add Error Handling** (AC: 1, 2)
  - [x] Handle FileNotFoundError gracefully
  - [x] Handle av.FFmpegError for corrupt files
  - [x] Handle missing audio codecs
  - [x] Return None on any error (never raise)
  - [x] Log errors with structured format

- [x] **Task 5: Write Unit Tests** (AC: 1, 2, 3, 4)
  - [x] Create `backend/tests/test_services/test_audio_extractor.py`
  - [x] Test extraction from video with audio track
  - [x] Test extraction from video without audio track
  - [x] Test silent audio track handling
  - [x] Test singleton pattern behavior
  - [x] Test error handling for missing/corrupt files

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Service Pattern:** Follow the `FrameExtractor` pattern exactly:
- Singleton with module-level instance
- Async method returning Optional[bytes]
- Graceful error handling (returns None, never raises)
- Structured JSON logging with `extra={}` dictionary

**Dependencies:**
- PyAV (`av` library) - already in use for FrameExtractor
- io.BytesIO for in-memory WAV encoding
- wave module for WAV file creation (or PyAV's audio encoder)

### Audio Format Requirements

**Output Format:** WAV (16kHz, mono) for transcription compatibility with OpenAI Whisper
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Sample format: PCM 16-bit signed

**Why WAV?**
- OpenAI Whisper API accepts WAV, MP3, MP4, M4A, WebM
- WAV is uncompressed and simplest to create from raw audio frames
- No additional encoding libraries needed

### Project Structure Notes

**Files to Create:**
```
backend/app/services/audio_extractor.py
backend/tests/test_services/test_audio_extractor.py
```

**No Files to Modify:** This is foundational infrastructure for Epic P3-5. Integration with event pipeline happens in P3-5.3.

### Technical Implementation Reference

```python
# Pattern from FrameExtractor to follow:
import av
import io
import wave
import logging
from pathlib import Path
from typing import Optional

AUDIO_SAMPLE_RATE = 16000  # 16kHz for Whisper compatibility
AUDIO_CHANNELS = 1  # Mono

class AudioExtractor:
    def __init__(self):
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        logger.info("AudioExtractor initialized", extra={...})

    async def extract_audio(self, clip_path: Path) -> Optional[bytes]:
        """
        Extract audio from video clip as WAV bytes.
        Returns None if no audio track or on error.
        """
        try:
            with av.open(str(clip_path)) as container:
                if not container.streams.audio:
                    logger.info("No audio track found", extra={...})
                    return None

                # Decode and resample audio frames...
                # Encode as WAV bytes...
                return wav_bytes
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}", extra={...})
            return None
```

### References

- [Source: docs/epics-phase3.md#Story-P3-5.1] - Story definition and acceptance criteria
- [Source: docs/PRD-phase3.md#Audio-Analysis] - FR23, FR26 requirements
- [Source: backend/app/services/frame_extractor.py] - Pattern reference for singleton, PyAV usage
- [Source: OpenAI Whisper API docs] - Audio format requirements for transcription

## Learnings from Previous Story

**From Story p3-4-5-add-ai-provider-badge-to-event-cards (Status: review)**

- **Component Pattern**: Used PROVIDER_CONFIG record pattern for type-safe configuration - similar pattern can be used for audio format configuration
- **Testing**: No unit tests added for AIProviderBadge component (advisory note to add tests) - ensure this story includes comprehensive unit tests
- **Review Outcome**: Approved - straightforward implementation following existing patterns

[Source: docs/sprint-artifacts/p3-4-5-add-ai-provider-badge-to-event-cards.md#Dev-Agent-Record]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p3-5-1-implement-audio-extraction-from-video-clips.context.xml

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- N/A - Implementation was straightforward following FrameExtractor pattern

### Completion Notes List

- Implementation follows established singleton pattern from FrameExtractor
- Uses PyAV for audio extraction with AudioResampler for format conversion
- WAV output: 16kHz sample rate, mono channel, 16-bit PCM
- Audio level detection includes RMS and peak amplitude calculations
- Silence threshold set at RMS < 0.001 (approximately -60dB)
- All errors handled gracefully (returns None, never raises)
- Structured JSON logging throughout
- Test coverage: 97% (37 tests passing)

### File List

**Created:**
- `backend/app/services/audio_extractor.py` - AudioExtractor service (348 lines)
- `backend/tests/test_services/test_audio_extractor.py` - Unit tests (631 lines)

## Change Log

- 2025-12-07: Story drafted from sprint-status backlog
- 2025-12-07: Implementation complete, all tests passing (97% coverage), moved to review

---

## Definition of Done

- [x] AudioExtractor service created with singleton pattern
- [x] extract_audio method implemented using PyAV
- [x] WAV output at 16kHz mono confirmed
- [x] No audio track handled gracefully (returns None)
- [x] Silent audio handled (returns bytes, logs level)
- [x] Unit tests pass with >80% coverage (97% achieved)
- [x] No TypeScript/Python errors
- [ ] Manual testing with real video clips (deferred to integration testing)

## Dependencies

- **Prerequisites Met:** P3-1.1 (ClipService exists and provides video clips)
- **PyAV Library:** Already installed (used by FrameExtractor)

## Estimate

**Medium** - Backend service creation following established patterns, includes unit tests
