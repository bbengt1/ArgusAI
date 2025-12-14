# Phase 3 Additions

This section documents the architectural additions for Phase 3, which transforms the system from snapshot-based to video-aware AI analysis by downloading and analyzing motion clips from UniFi Protect.

## Phase 3 Executive Summary

Phase 3 addresses a fundamental limitation: **a single frame cannot capture action or narrative**. By analyzing video clips instead of snapshots, the system can describe:

- **Direction of movement** - "walked toward the street"
- **Actions and behaviors** - "placed package on doorstep"
- **Temporal sequences** - "arrived, knocked, waited, then left"
- **Intent resolution** - distinguish delivery from suspicious activity

**Key Architectural Principles (Phase 3):**
1. **Configurable Analysis Depth** - Users choose cost/quality trade-off per camera
2. **Graceful Degradation** - Fallback chain from video → multi-frame → single-frame
3. **Temporary Storage** - Clips are ephemeral, only descriptions persist
4. **Provider Flexibility** - Route to providers based on capability (multi-image vs video)

---

## Phase 3 Technology Stack Additions

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Video Processing** | PyAV | 12.x+ | Video file reading and frame extraction |
| **Frame Selection** | OpenCV | 4.8+ (existing) | Frame quality analysis, blur detection |

**New Dependencies (backend/requirements.txt):**
```bash
# Phase 3: Video clip processing
av>=12.0.0                    # PyAV for video frame extraction

# OpenCV already installed for motion detection
# opencv-python>=4.8.0
```

**No new frontend dependencies required.**

---

## Phase 3 Project Structure Additions

```
backend/
├── app/
│   ├── models/
│   │   └── camera.py               # MODIFIED: Add analysis_mode field
│   ├── schemas/
│   │   └── camera.py               # MODIFIED: Add analysis_mode to schemas
│   ├── services/
│   │   ├── clip_service.py         # NEW: Download and manage video clips
│   │   ├── frame_extractor.py      # NEW: Extract frames from video clips
│   │   ├── video_analyzer.py       # NEW: Native video analysis routing
│   │   ├── ai_service.py           # MODIFIED: Multi-image and video support
│   │   ├── protect_service.py      # MODIFIED: Add clip download method
│   │   ├── protect_event_handler.py # MODIFIED: Route to video analysis
│   │   └── cost_tracker.py         # NEW: Track AI usage and costs
│   └── utils/
│       └── video_utils.py          # NEW: Video format utilities
├── data/
│   └── clips/                      # NEW: Temporary clip storage (gitignored)
│       └── {event_id}/
│           ├── clip.mp4            # Downloaded clip
│           └── frames/             # Extracted frames
│               ├── frame_001.jpg
│               ├── frame_002.jpg
│               └── ...
└── ...

frontend/
├── components/
│   ├── cameras/
│   │   └── AnalysisModeSelector.tsx  # NEW: Analysis mode dropdown
│   ├── events/
│   │   ├── AnalysisModeBadge.tsx     # NEW: Show mode used
│   │   ├── ConfidenceIndicator.tsx   # NEW: Confidence score display
│   │   └── FrameStrip.tsx            # NEW: Show extracted frames
│   └── settings/
│       └── CostMonitoringPanel.tsx   # NEW: Usage and cost display
└── ...
```

---

## Phase 3 Database Schema Additions

**cameras** table (EXTENDED):
```sql
-- Add analysis mode configuration
ALTER TABLE cameras ADD COLUMN analysis_mode TEXT DEFAULT 'single_frame';
-- Values: 'single_frame', 'multi_frame', 'video_native'

ALTER TABLE cameras ADD COLUMN frame_count INTEGER DEFAULT 5;
-- Number of frames to extract for multi_frame mode (3-10)

-- Index for mode-based queries
CREATE INDEX idx_cameras_analysis_mode ON cameras(analysis_mode);
```

**events** table (EXTENDED):
```sql
-- Add analysis metadata
ALTER TABLE events ADD COLUMN analysis_mode TEXT DEFAULT 'single_frame';
-- Mode actually used for this event

ALTER TABLE events ADD COLUMN frame_count_used INTEGER;
-- Number of frames analyzed (for multi_frame)

ALTER TABLE events ADD COLUMN ai_confidence REAL;
-- Confidence score from AI (0.0 to 1.0)

ALTER TABLE events ADD COLUMN ai_tokens_used INTEGER;
-- Token count for cost tracking

ALTER TABLE events ADD COLUMN ai_cost_estimate REAL;
-- Estimated cost in USD

ALTER TABLE events ADD COLUMN fallback_reason TEXT;
-- If fallback used, why? ("clip_download_failed", "provider_timeout", etc.)

-- Index for confidence-based filtering
CREATE INDEX idx_events_ai_confidence ON events(ai_confidence);
```

**ai_usage** table (NEW):
```sql
CREATE TABLE ai_usage (
    id TEXT PRIMARY KEY,                    -- UUID
    date DATE NOT NULL,                     -- Date of usage
    camera_id TEXT REFERENCES cameras(id),  -- Which camera
    provider TEXT NOT NULL,                 -- 'openai', 'grok', 'gemini', 'anthropic'
    analysis_mode TEXT NOT NULL,            -- 'single_frame', 'multi_frame', 'video_native'
    request_count INTEGER DEFAULT 0,        -- Number of requests
    total_tokens INTEGER DEFAULT 0,         -- Total tokens used
    estimated_cost REAL DEFAULT 0.0,        -- Estimated cost in USD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, camera_id, provider, analysis_mode)
);

CREATE INDEX idx_ai_usage_date ON ai_usage(date);
CREATE INDEX idx_ai_usage_camera ON ai_usage(camera_id);
```

---

## Phase 3 Service Architecture

### ClipService (NEW)

**File:** `backend/app/services/clip_service.py`

**Responsibilities:**
- Download motion clips from UniFi Protect
- Manage temporary clip storage
- Handle download retries with exponential backoff
- Clean up clips after analysis

**Key Methods:**
```python
class ClipService:
    """Manages video clip download and storage for analysis."""

    TEMP_CLIP_DIR = "data/clips"
    MAX_CLIP_AGE_HOURS = 1
    MAX_STORAGE_MB = 1024  # 1GB limit

    async def download_clip(
        self,
        controller_id: str,
        camera_id: str,
        event_start: datetime,
        event_end: datetime,
        event_id: str
    ) -> Optional[Path]:
        """Download motion clip from Protect for the given time range.

        Returns path to downloaded clip, or None if download fails.
        Retries up to 3 times with exponential backoff (1s, 2s, 4s).
        """

    async def cleanup_clip(self, event_id: str) -> None:
        """Remove clip and extracted frames for given event."""

    async def cleanup_old_clips(self) -> int:
        """Remove clips older than MAX_CLIP_AGE_HOURS. Returns count removed."""

    async def get_storage_usage_mb(self) -> float:
        """Get current temporary storage usage in MB."""

    def _get_clip_path(self, event_id: str) -> Path:
        """Get path for clip storage."""
        return Path(self.TEMP_CLIP_DIR) / event_id / "clip.mp4"
```

### FrameExtractor (NEW)

**File:** `backend/app/services/frame_extractor.py`

**Responsibilities:**
- Extract frames from video clips using PyAV
- Select frames using configurable strategy
- Filter out low-quality frames (blur detection)
- Encode frames as JPEG for AI analysis

**Key Methods:**
```python
class FrameExtractor:
    """Extracts and selects frames from video clips."""

    async def extract_frames(
        self,
        clip_path: Path,
        frame_count: int = 5,
        strategy: str = "evenly_spaced"
    ) -> List[bytes]:
        """Extract frames from video clip.

        Args:
            clip_path: Path to video file
            frame_count: Number of frames to extract (3-10)
            strategy: Selection strategy
                - "evenly_spaced": Equal intervals through clip
                - "motion_peaks": Frames with highest motion (future)

        Returns:
            List of JPEG-encoded frame bytes
        """

    def _is_frame_usable(self, frame: np.ndarray) -> bool:
        """Check if frame is sharp enough for AI analysis.

        Uses Laplacian variance for blur detection.
        Threshold: 100 (configurable)
        """

    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """Encode frame as JPEG with 85% quality."""
```

**Frame Selection Algorithm (Evenly Spaced):**
```
Clip duration: 10 seconds, Frame count: 5

Frame indices (at 30fps = 300 total frames):
  Frame 1: index 0 (0.0s)
  Frame 2: index 75 (2.5s)
  Frame 3: index 150 (5.0s)
  Frame 4: index 225 (7.5s)
  Frame 5: index 300 (10.0s)

Skip any frame failing blur detection, take next frame.
```

### AIService Extensions

**File:** `backend/app/services/ai_service.py` (MODIFIED)

**Add multi-image and video analysis:**
```python
class AIService:
    """Extended for Phase 3 video analysis."""

    async def analyze_frames(
        self,
        frames: List[bytes],
        prompt: str,
        provider: Optional[str] = None
    ) -> AnalysisResult:
        """Analyze multiple frames as a sequence.

        Args:
            frames: List of JPEG-encoded frame bytes
            prompt: Analysis prompt (mode-specific)
            provider: Specific provider or None for fallback chain

        Returns:
            AnalysisResult with description, confidence, tokens, cost
        """

    async def analyze_video(
        self,
        video_path: Path,
        prompt: str,
        provider: Optional[str] = None
    ) -> AnalysisResult:
        """Analyze video clip directly (GPT-4o, Gemini only).

        Falls back to multi-frame if provider doesn't support video.
        """

    def _get_multi_frame_prompt(self) -> str:
        """Return prompt optimized for frame sequences."""
        return """Analyze these sequential frames from a security camera.
Describe:
1. What is happening (action, movement, behavior)
2. Who or what is involved (person, vehicle, animal, package)
3. The sequence of events (what happened first, then, finally)
4. Direction of movement if applicable

Be specific and concise. Focus on security-relevant details."""

    def _get_video_prompt(self) -> str:
        """Return prompt optimized for video analysis."""
        return """Analyze this security camera video clip.
Describe in detail:
1. The complete sequence of events from start to finish
2. All people, vehicles, animals, or objects involved
3. Actions taken and their apparent purpose
4. Direction of arrival and departure
5. Any notable behaviors or items (packages, etc.)

Be specific and concise. This is for home security monitoring."""
```

**AnalysisResult dataclass:**
```python
@dataclass
class AnalysisResult:
    description: str
    confidence: float  # 0.0 to 1.0
    tokens_used: int
    estimated_cost: float  # USD
    provider_used: str
    analysis_mode: str  # 'single_frame', 'multi_frame', 'video_native'
    fallback_reason: Optional[str] = None
```

### CostTracker (NEW)

**File:** `backend/app/services/cost_tracker.py`

**Responsibilities:**
- Track AI usage per request
- Aggregate daily/monthly costs
- Enforce cost caps
- Provide usage analytics

**Key Methods:**
```python
class CostTracker:
    """Tracks AI API usage and costs."""

    # Cost per 1K tokens (approximate, configurable)
    COSTS = {
        "openai": {"input": 0.00015, "output": 0.0006},  # GPT-4o-mini
        "grok": {"input": 0.00010, "output": 0.0003},    # Estimate
        "gemini": {"input": 0.0, "output": 0.0},         # Free tier
        "anthropic": {"input": 0.00025, "output": 0.00125}  # Haiku
    }

    async def record_usage(
        self,
        camera_id: str,
        provider: str,
        analysis_mode: str,
        tokens_used: int
    ) -> None:
        """Record AI usage for tracking."""

    async def get_daily_usage(self, date: date) -> Dict[str, Any]:
        """Get usage summary for a specific date."""

    async def get_monthly_usage(self, year: int, month: int) -> Dict[str, Any]:
        """Get usage summary for a month."""

    async def check_cap(self, cap_type: str, limit: float) -> bool:
        """Check if usage is within cap. Returns True if OK."""

    def estimate_cost(self, provider: str, tokens: int) -> float:
        """Estimate cost for given token count."""
```

---

## Phase 3 Event Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Phase 3 Event Processing Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  UniFi Protect Event                                                        │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                  ProtectEventHandler                              │       │
│  │  1. Receive event from WebSocket                                 │       │
│  │  2. Check camera's analysis_mode setting                         │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌───────────────────────────────────────────────────┐                     │
│  │            Analysis Mode Router                     │                     │
│  │                                                     │                     │
│  │   analysis_mode = ?                                 │                     │
│  │                                                     │                     │
│  │   ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │                     │
│  │   │single_frame │  │ multi_frame │  │video_native│ │                     │
│  │   └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │                     │
│  └──────────┼────────────────┼───────────────┼───────┘                     │
│             │                │               │                              │
│             ▼                │               │                              │
│  ┌─────────────────┐         │               │                              │
│  │ Get Snapshot    │         │               │                              │
│  │ (existing flow) │         │               │                              │
│  └────────┬────────┘         │               │                              │
│           │                  ▼               ▼                              │
│           │         ┌─────────────────────────────┐                        │
│           │         │      ClipService            │                        │
│           │         │  1. Download motion clip    │                        │
│           │         │  2. Store in temp directory │                        │
│           │         │  3. Retry on failure        │                        │
│           │         └────────────┬────────────────┘                        │
│           │                      │                                          │
│           │                      │ clip_path                                │
│           │                      ▼                                          │
│           │         ┌─────────────────────────────┐                        │
│           │         │    FrameExtractor           │                        │
│           │         │  (multi_frame mode only)    │                        │
│           │         │  1. Extract N frames        │                        │
│           │         │  2. Filter blurry frames    │                        │
│           │         │  3. Encode as JPEG          │                        │
│           │         └────────────┬────────────────┘                        │
│           │                      │ frames[]                                 │
│           │                      │                                          │
│           │    ┌─────────────────┴─────────────────┐                       │
│           │    │                                   │                        │
│           ▼    ▼                                   ▼                        │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                        AIService                                  │       │
│  │                                                                   │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │       │
│  │  │ analyze()    │  │analyze_frames│  │analyze_video │           │       │
│  │  │ single image │  │ multi-image  │  │ native video │           │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │       │
│  │                                                                   │       │
│  │  Provider Fallback Chain:                                        │       │
│  │  OpenAI → Grok → Gemini → Claude                                 │       │
│  │                                                                   │       │
│  │  Video Support: GPT-4o ✓, Gemini ✓, Others ✗ (→ fallback)       │       │
│  │                                                                   │       │
│  └────────────────────────────────┬────────────────────────────────┘       │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                      AnalysisResult                               │       │
│  │  - description: "Delivery driver arrived, placed package..."     │       │
│  │  - confidence: 0.92                                              │       │
│  │  - tokens_used: 450                                              │       │
│  │  - estimated_cost: 0.00027                                       │       │
│  │  - analysis_mode: "multi_frame"                                  │       │
│  │  - provider_used: "openai"                                       │       │
│  └────────────────────────────────┬────────────────────────────────┘       │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Post-Processing                                │       │
│  │  1. CostTracker.record_usage()                                   │       │
│  │  2. ClipService.cleanup_clip()                                   │       │
│  │  3. Store event with analysis metadata                           │       │
│  │  4. Broadcast via WebSocket                                      │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 3 Fallback Chain

```
video_native mode requested
         │
         ▼
   Download clip
         │
    ┌────┴────┐
    │ Success │
    └────┬────┘
         │
         ▼
   Send to video-capable provider (GPT-4o, Gemini)
         │
    ┌────┴────┐
    │ Success │────────────────────────────────────────▶ Return result
    └────┬────┘
    │ Failure │ (provider doesn't support video, timeout, etc.)
    └────┬────┘
         │
         ▼
   Fallback to multi_frame
         │
         ▼
   Extract frames from clip
         │
         ▼
   Send frames to any provider
         │
    ┌────┴────┐
    │ Success │────────────────────────────────────────▶ Return result
    └────┬────┘                                          (with fallback_reason)
    │ Failure │
    └────┬────┘
         │
         ▼
   Fallback to single_frame
         │
         ▼
   Get snapshot from clip (first frame) or Protect API
         │
         ▼
   Existing single-frame analysis
         │
         ▼
   Return result (with fallback_reason)
```

---

## Phase 3 API Additions

**Base URL:** `http://localhost:8000/api/v1`

### Camera Analysis Mode

**PUT /cameras/{id}** (EXTENDED)
- Body now accepts `analysis_mode` and `frame_count`:
```json
{
  "analysis_mode": "multi_frame",
  "frame_count": 5
}
```

**GET /cameras/{id}** (EXTENDED)
- Response includes new fields:
```json
{
  "data": {
    "id": "uuid",
    "name": "Front Door",
    "analysis_mode": "multi_frame",
    "frame_count": 5,
    "...": "..."
  }
}
```

### AI Usage/Cost Endpoints

**GET /ai/usage**
- Query params: `start_date`, `end_date`, `camera_id`, `provider`
- Response:
```json
{
  "data": {
    "total_requests": 142,
    "total_tokens": 63500,
    "estimated_cost": 0.95,
    "by_camera": {
      "camera-1": { "requests": 80, "tokens": 35000, "cost": 0.53 },
      "camera-2": { "requests": 62, "tokens": 28500, "cost": 0.42 }
    },
    "by_provider": {
      "openai": { "requests": 100, "tokens": 45000, "cost": 0.68 },
      "grok": { "requests": 42, "tokens": 18500, "cost": 0.27 }
    },
    "by_mode": {
      "single_frame": { "requests": 50, "tokens": 15000, "cost": 0.23 },
      "multi_frame": { "requests": 92, "tokens": 48500, "cost": 0.72 }
    }
  },
  "meta": {...}
}
```

**GET /ai/usage/daily**
- Query params: `days` (default 30)
- Response: Array of daily usage summaries

**PUT /settings/ai_cost_cap**
- Body:
```json
{
  "daily_cap": 1.00,
  "monthly_cap": 25.00,
  "action_on_cap": "fallback_to_single_frame"
}
```

---

## Phase 3 Frontend Components

### AnalysisModeSelector

**Location:** `frontend/components/cameras/AnalysisModeSelector.tsx`

**Props:**
```typescript
interface AnalysisModeSelectorProps {
  currentMode: 'single_frame' | 'multi_frame' | 'video_native';
  frameCount: number;
  onModeChange: (mode: string) => void;
  onFrameCountChange: (count: number) => void;
}
```

**Display:**
```
┌─────────────────────────────────────────────────┐
│ AI Analysis Mode                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ ○ Single Frame (Fastest, lowest cost)          │
│   Analyzes one snapshot per event              │
│                                                 │
│ ● Multi-Frame (Recommended)                    │
│   Analyzes [5 ▼] frames for better context     │
│   ~$0.002/event                                │
│                                                 │
│ ○ Video Native (Best quality, highest cost)    │
│   Sends full video clip to AI                  │
│   ~$0.01/event                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

### AnalysisModeBadge

**Location:** `frontend/components/events/AnalysisModeBadge.tsx`

Shows which analysis mode was used for an event:
- `single_frame` → "Single" (gray badge)
- `multi_frame` → "Multi (5)" (blue badge)
- `video_native` → "Video" (purple badge)
- With fallback indicator if applicable

### ConfidenceIndicator

**Location:** `frontend/components/events/ConfidenceIndicator.tsx`

Visual confidence display:
- ≥90%: Green checkmark
- 70-89%: Yellow indicator
- <70%: Orange warning with "Low confidence" tooltip

---

## Phase 3 Configuration

**New Environment Variables:**
```bash
# Temporary clip storage location (default: backend/data/clips)
CLIP_STORAGE_PATH=/app/data/clips

# Maximum clip storage in MB (default: 1024)
MAX_CLIP_STORAGE_MB=1024

# Maximum clip age before cleanup in hours (default: 1)
MAX_CLIP_AGE_HOURS=1

# Default analysis mode for new cameras
DEFAULT_ANALYSIS_MODE=multi_frame

# Default frame count for multi_frame mode
DEFAULT_FRAME_COUNT=5

# Cost caps (optional)
AI_DAILY_COST_CAP=1.00
AI_MONTHLY_COST_CAP=25.00
```

**New System Settings (database):**
- `analysis_default_mode`: Default mode for new cameras
- `analysis_default_frame_count`: Default frame count
- `ai_daily_cost_cap`: Daily cost limit in USD
- `ai_monthly_cost_cap`: Monthly cost limit in USD
- `ai_cap_action`: What to do when cap reached (`pause`, `fallback_to_single_frame`)

---

## Phase 3 Epic to Architecture Mapping

| Epic | Architecture Components | Key Files |
|------|------------------------|-----------|
| **P3-1: Motion Clip Download** | ClipService, ProtectService extension | `clip_service.py`, `protect_service.py` |
| **P3-2: Multi-Frame Analysis** | FrameExtractor, AIService extension | `frame_extractor.py`, `ai_service.py` |
| **P3-3: Analysis Mode Config** | Camera model, settings UI | `camera.py`, `AnalysisModeSelector.tsx` |
| **P3-4: Video Native Mode** | AIService video support | `ai_service.py`, `video_analyzer.py` |
| **P3-5: Audio Analysis** | Audio extraction, transcription | `audio_extractor.py` (future) |
| **P3-6: Confidence Scoring** | AIService, event display | `ai_service.py`, `ConfidenceIndicator.tsx` |
| **P3-7: Cost Monitoring** | CostTracker, usage API | `cost_tracker.py`, `CostMonitoringPanel.tsx` |

---

## Phase 3 Architecture Decision Records

### ADR-012: Temporary Clip Storage

**Decision:** Store video clips temporarily during analysis, then delete them. Do not persist clips.

**Rationale:**
- **Storage:** Video clips are large (10-50MB each), persisting would quickly consume disk
- **Privacy:** Aligns with "description-first" philosophy - store descriptions, not footage
- **Performance:** Smaller database, faster backups
- **Simplicity:** No video playback features needed

**Trade-offs:**
- Cannot re-analyze events later (must re-download if needed)
- Cannot show video playback in UI

**Status:** Accepted (maintains Phase 1 design principles)

---

### ADR-013: Evenly-Spaced Frame Selection

**Decision:** Use evenly-spaced frame selection as the default algorithm.

**Rationale:**
- **Simple:** Easy to implement and understand
- **Predictable:** Same frame positions every time
- **Effective:** Captures full timeline of event
- **Fast:** O(1) frame index calculation

**Trade-offs:**
- May miss peak action if it falls between selected frames
- Motion-based selection could be better (future enhancement)

**Status:** Accepted (simple first, enhance later)

---

### ADR-014: Multi-Provider Video Support Detection

**Decision:** Maintain a capability matrix of which providers support video vs multi-image.

**Rationale:**
- **Dynamic routing:** Send video to capable providers, frames to others
- **Graceful fallback:** If video fails, extract frames and retry
- **Provider updates:** Can update matrix without code changes

**Trade-offs:**
- Must maintain accurate capability data
- Provider capabilities may change over time

**Status:** Accepted

**Current Capability Matrix:**
| Provider | Multi-Image | Video | Notes |
|----------|-------------|-------|-------|
| OpenAI GPT-4o | ✓ | ✓ | Preferred for video |
| xAI Grok | ✓ | ? | Testing required |
| Google Gemini | ✓ | ✓ | Good video support |
| Anthropic Claude | ✓ | ✗ | Images only |

---

### ADR-015: Cost Estimation Approach

**Decision:** Use pre-configured cost-per-token estimates for each provider.

**Rationale:**
- **Predictability:** Users can estimate costs before configuring
- **Simplicity:** No real-time API cost lookup needed
- **Configurable:** Can update estimates in settings

**Trade-offs:**
- Estimates may drift from actual costs
- Provider pricing changes require config updates

**Status:** Accepted (accurate within 20% is acceptable per NFR12)

---

## Phase 3 Performance Considerations

**Clip Download:**
- Target: <10 seconds for typical 10-30 second clips
- Parallel download + analysis when possible
- Timeout: 15 seconds, then fallback to snapshot

**Frame Extraction:**
- Target: <2 seconds for 10-second clip
- Use PyAV (faster than OpenCV for video decoding)
- Extract directly to JPEG bytes (no intermediate disk writes)

**Multi-Frame AI Analysis:**
- Expect ~3x tokens vs single frame
- Target: <10 seconds total (download + extract + AI)
- Parallel frame extraction while downloading

**Storage Management:**
- Background cleanup task runs every 15 minutes
- Aggressive cleanup: delete clips >1 hour old
- Monitor storage usage, pause downloads if >1GB

---

## Phase 3 Validation Checklist

- ✅ All PRD Phase 3 functional requirements (FR1-FR41) have architectural support
- ✅ All PRD Phase 3 non-functional requirements (NFR1-NFR14) addressed
- ✅ Video clip download and storage architecture defined
- ✅ Frame extraction pipeline designed with quality filtering
- ✅ Multi-image AI analysis integrated into existing service
- ✅ Analysis mode configuration added to camera model
- ✅ Cost tracking and monitoring system designed
- ✅ Fallback chain ensures graceful degradation
- ✅ Frontend components identified for new features
- ✅ Database schema extended for analysis metadata
- ✅ Phase 3 ADRs documented with rationale

---

**Phase 3 Architecture Update:**
- **Updated by:** BMad Architect Agent
- **Date:** 2025-12-05
- **PRD Reference:** `docs/PRD-phase3.md`
- **Brainstorming Reference:** `docs/brainstorming-session-results-2025-12-05.md`

---
