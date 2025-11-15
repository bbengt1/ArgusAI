# Epic Technical Specification: Motion Detection

Date: 2025-11-15
Author: Brent
Epic ID: f2
Status: Draft

---

## Overview

Epic F2 implements motion detection capabilities to trigger AI-powered event analysis in the Live Object AI Classifier system. Building on Epic F1's camera feed integration, this epic adds computer vision-based motion detection using OpenCV to identify movement in video streams and trigger downstream AI processing only when motion is detected. This event-driven approach reduces computational overhead and API costs by processing only relevant frames rather than continuous analysis.

The motion detection system will support configurable sensitivity levels, detection zones, and optional scheduling to provide users fine-grained control over when and where motion triggers events. This aligns with the PRD's goal of achieving <5 second end-to-end latency from motion detection to AI description generation while maintaining a false positive rate below 20%.

## Objectives and Scope

**In Scope:**
- Motion detection algorithm implementation using OpenCV (frame differencing or background subtraction)
- Configurable sensitivity levels (low, medium, high)
- Motion detection zones (user-defined rectangular regions)
- Detection scheduling (time-based and day-of-week activation)
- Cooldown period between motion triggers (30-60 seconds default)
- Integration with existing camera capture threads from Epic F1
- Motion event storage and API endpoints

**Out of Scope:**
- Object recognition/classification (handled by Epic F3: AI Description Generation)
- Multi-object tracking across frames
- Advanced computer vision (pose estimation, facial recognition)
- Video recording or playback
- Motion-triggered alert notifications (Epic F5: Alert Rule Engine)

## System Architecture Alignment

**Components Referenced:**
- **CameraService** (F1): Extends existing camera capture loop to integrate motion detection processing
- **Database Layer** (F1): Reuses SQLAlchemy ORM and migrations infrastructure
- **FastAPI Backend** (F1): Adds motion detection API endpoints to existing REST API structure
- **Frontend (Next.js)**: Adds motion configuration UI pages and components

**Architectural Constraints:**
- Motion detection must run in camera capture thread (non-blocking, <100ms per frame)
- OpenCV already dependency from F1 (version 4.12.0+)
- Thread-safe status tracking pattern from F1 applies to motion detector state
- SQLite database for MVP (motion events table alongside cameras table)
- Backend-first implementation approach (consistent with F1 pattern)

**Technology Stack Alignment:**
- Python 3.13+ backend (established in F1)
- OpenCV 4.12+ for motion detection algorithms
- FastAPI 0.115+ for REST API
- SQLAlchemy 2.0.44+ for ORM
- Next.js 15+ / React 18+ for frontend UI

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| **MotionDetectionService** | Core motion detection logic using OpenCV algorithms | Video frames from CameraService, sensitivity config, detection zones | Motion detected events, bounding box coordinates, motion confidence score | Backend/Services |
| **MotionDetector** | Algorithm implementation (frame differencing, background subtraction MOG2/KNN) | Current frame, previous frame(s), sensitivity threshold | Boolean (motion detected), contours, motion intensity | Backend/Services |
| **DetectionZoneManager** | Manages user-defined polygon detection zones per camera | Polygon vertices, motion contours/bounding box | Filtered motion events (only within polygon zones) | Backend/Services |
| **ScheduleManager** | Handles time-based detection scheduling | Current time, schedule config (time ranges, days of week) | Boolean (detection active) | Backend/Services |
| **MotionEventStore** | Persists motion detection events to database | Event data (timestamp, camera_id, confidence, bounding_box) | Event ID | Backend/Services |
| **MotionAPI** | REST API endpoints for motion configuration and event retrieval | HTTP requests (config updates, event queries) | JSON responses (events, settings) | Backend/API |
| **MotionConfigUI** | Frontend UI for configuring motion settings | User interactions (sensitivity sliders, zone drawing) | API calls to update config | Frontend/Components |
| **DetectionZoneDrawer** | Interactive zone drawing on camera preview | Mouse/touch events on canvas, camera preview image | Zone coordinates array | Frontend/Components |

**Service Interaction Flow:**
1. CameraService captures frame → Passes to MotionDetectionService
2. MotionDetectionService → ScheduleManager (check if detection active)
3. MotionDetectionService → MotionDetector (run algorithm on frame)
4. MotionDetector → DetectionZoneManager (filter by zones)
5. MotionDetectionService → MotionEventStore (save event if motion detected)
6. MotionEventStore → Database (persist event record)

### Data Models and Contracts

**Motion Detection Configuration (extends Camera model from F1)**

```python
# app/models/camera.py (extend existing Camera model)
class Camera(Base):
    # ... existing fields from F1 ...

    # Motion Detection Fields (new in F2)
    motion_enabled: bool = Column(Boolean, default=True)
    motion_sensitivity: str = Column(String, default="medium")  # low, medium, high
    motion_cooldown_seconds: int = Column(Integer, default=30)
    motion_algorithm: str = Column(String, default="mog2")  # mog2, knn, frame_diff

    # Detection Zones (JSON array of polygon zone objects)
    detection_zones: str = Column(Text, nullable=True)  # JSON: [{"id": "zone1", "name": "Front Door", "vertices": [{"x": 100, "y": 50}, ...], "enabled": true}, ...]

    # Scheduling (JSON object)
    detection_schedule: str = Column(Text, nullable=True)  # JSON: {"enabled": false, "time_ranges": [...], "days": [...]}
```

**Motion Event Model**

```python
# app/models/motion_event.py (NEW)
class MotionEvent(Base):
    __tablename__ = "motion_events"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id: str = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    timestamp: datetime = Column(DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(timezone.utc))

    # Motion Detection Metadata
    confidence: float = Column(Float, nullable=False)  # 0.0 - 1.0
    motion_intensity: float = Column(Float, nullable=True)  # Pixel change intensity
    algorithm_used: str = Column(String, nullable=False)  # mog2, knn, frame_diff

    # Bounding Box (largest contour)
    bounding_box: str = Column(Text, nullable=True)  # JSON: {"x": 100, "y": 50, "width": 200, "height": 150}

    # Frame Reference (optional - base64 thumbnail or file path)
    frame_thumbnail: str = Column(Text, nullable=True)  # Base64 JPEG or file path

    # AI Processing Link (null until F3 processes)
    ai_event_id: str = Column(String, ForeignKey("ai_events.id"), nullable=True)

    created_at: datetime = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    camera = relationship("Camera", back_populates="motion_events")
```

**Pydantic Schemas**

```python
# app/schemas/motion.py (NEW)
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DetectionZone(BaseModel):
    id: str
    name: str
    vertices: List[dict] = Field(min_length=3)  # [{"x": 100, "y": 50}, {"x": 200, "y": 50}, ...]
    enabled: bool = True

    @validator('vertices')
    def validate_polygon(cls, v):
        """Ensure polygon has at least 3 vertices and forms closed shape"""
        if len(v) < 3:
            raise ValueError("Polygon must have at least 3 vertices")
        # Auto-close polygon if first and last vertex don't match
        if v[0] != v[-1]:
            v.append(v[0])
        return v

class DetectionSchedule(BaseModel):
    enabled: bool = False
    time_range: Optional[dict] = None  # {"start": "09:00", "end": "17:00"} - Single range only (DECISION-3)
    days: List[str] = []  # ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

class MotionConfigUpdate(BaseModel):
    motion_enabled: Optional[bool] = None
    motion_sensitivity: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    motion_cooldown_seconds: Optional[int] = Field(None, ge=5, le=300)
    motion_algorithm: Optional[str] = Field(None, pattern="^(mog2|knn|frame_diff)$")
    detection_zones: Optional[List[DetectionZone]] = None
    detection_schedule: Optional[DetectionSchedule] = None

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class MotionEventResponse(BaseModel):
    id: str
    camera_id: str
    timestamp: datetime
    confidence: float
    motion_intensity: Optional[float]
    algorithm_used: str
    bounding_box: Optional[BoundingBox]
    ai_event_id: Optional[str]

    class Config:
        from_attributes = True
```

### APIs and Interfaces

**Motion Configuration Endpoints**

```python
# PUT /api/v1/cameras/{camera_id}/motion/config
# Update motion detection configuration for specific camera
Request Body: MotionConfigUpdate
Response: 200 OK + CameraResponse (includes updated motion config)
Errors: 404 (camera not found), 422 (validation error)

# GET /api/v1/cameras/{camera_id}/motion/config
# Get current motion detection configuration
Response: 200 OK + MotionConfigUpdate
Errors: 404 (camera not found)
```

**Motion Events Endpoints**

```python
# GET /api/v1/motion-events
# List motion detection events with filters
Query Parameters:
  - camera_id: Optional[str] - Filter by camera
  - start_date: Optional[datetime] - Filter events after date
  - end_date: Optional[datetime] - Filter events before date
  - min_confidence: Optional[float] - Filter by minimum confidence (0.0-1.0)
  - limit: int = 50 - Max results
  - offset: int = 0 - Pagination offset
Response: 200 OK + List[MotionEventResponse]

# GET /api/v1/motion-events/{event_id}
# Get single motion event details
Response: 200 OK + MotionEventResponse
Errors: 404 (event not found)

# DELETE /api/v1/motion-events/{event_id}
# Delete motion event (admin/cleanup)
Response: 200 OK + {"deleted": true}
Errors: 404 (event not found)

# GET /api/v1/motion-events/stats
# Motion event statistics
Query Parameters:
  - camera_id: Optional[str]
  - days: int = 7 - Number of days to analyze
Response: 200 OK + {
  "total_events": int,
  "events_by_camera": dict,
  "events_by_hour": dict,
  "average_confidence": float
}
```

**Motion Detection Testing Endpoint**

```python
# POST /api/v1/cameras/{camera_id}/motion/test
# Test motion detection settings with current frame
Request Body: {
  "sensitivity": "medium",  # Optional override
  "algorithm": "mog2"  # Optional override
}
Response: 200 OK + {
  "motion_detected": bool,
  "confidence": float,
  "bounding_box": Optional[BoundingBox],
  "preview_image": str  # Base64 JPEG with bounding box overlay
}
```

### Workflows and Sequencing

**Motion Detection Processing Flow (Frame-by-Frame)**

```
1. CameraService captures frame (every 1/FPS seconds)
   ↓
2. Check if motion detection enabled for camera
   │ If disabled → Skip to step 10
   ↓
3. ScheduleManager: Check if detection active (time/day filters)
   │ If outside schedule → Skip to step 10
   ↓
4. Check cooldown period (has 30s elapsed since last event?)
   │ If in cooldown → Skip to step 10
   ↓
5. MotionDetector: Run algorithm (MOG2/KNN/FrameDiff)
   │ Input: Current frame + background model/previous frame
   │ Output: Foreground mask (binary image)
   ↓
6. Apply sensitivity threshold
   │ Count non-zero pixels in mask
   │ Compare to threshold (low: 5%, medium: 2%, high: 0.5% of frame)
   │ If below threshold → No motion (skip to step 10)
   ↓
7. DetectionZoneManager: Filter motion by zones
   │ If zones defined → Check if motion overlaps zones
   │ If no overlap → Skip to step 10
   ↓
8. Extract largest contour → Calculate bounding box
   ↓
9. MotionEventStore: Create motion event record
   │ Save to database with timestamp, confidence, bounding box
   │ Emit motion event to queue (for F3 AI processing)
   ↓
10. Continue to next frame
```

**Motion Configuration Update Flow**

```
User Action (Frontend)
   ↓
1. User adjusts sensitivity slider → "medium" to "high"
   ↓
2. Frontend calls: PUT /api/v1/cameras/{id}/motion/config
   Request: {"motion_sensitivity": "high"}
   ↓
3. Backend validates request (Pydantic schema)
   ↓
4. Update Camera model in database
   ↓
5. MotionDetectionService detects config change
   │ Reload config for camera
   │ Update sensitivity threshold in detector
   ↓
6. Response: 200 OK + Updated camera config
   ↓
7. Frontend updates UI to reflect change
```

**Detection Zone Drawing Flow (Polygon - DECISION-1)**

```
User Action (Frontend)
   ↓
1. User clicks "Draw Zone" button on camera preview
   ↓
2. Canvas overlay enabled with click handlers
   ↓
3. User clicks to add vertices (polygon drawing mode)
   │ First click: Start polygon at (x1, y1)
   │ Second click: Add vertex at (x2, y2)
   │ Third+ clicks: Add more vertices
   │ Double-click or "Finish" button: Close polygon
   ↓
4. Validate polygon (minimum 3 vertices)
   │ Auto-close polygon (connect last vertex to first)
   │ Normalize coordinates (relative to image dimensions, 0-1 scale)
   ↓
5. User names zone (e.g., "Front Door")
   ↓
6. Frontend calls: PUT /api/v1/cameras/{id}/motion/config
   Request: {
     "detection_zones": [
       <existing zones>,
       {
         "id": "zone-uuid",
         "name": "Front Door",
         "vertices": [{"x": 0.2, "y": 0.3}, {"x": 0.5, "y": 0.3}, {"x": 0.5, "y": 0.8}, {"x": 0.2, "y": 0.8}],
         "enabled": true
       }
     ]
   }
   ↓
7. Backend validates polygon (Pydantic DetectionZone schema)
   │ Check: At least 3 vertices
   │ Check: All vertices within bounds (0 ≤ x,y ≤ 1)
   ↓
8. Backend updates Camera.detection_zones (JSON)
   ↓
9. DetectionZoneManager reloads zones for camera
   ↓
10. Response: 200 OK
   ↓
11. Frontend renders polygon overlay on preview (connected lines, semi-transparent fill)
```

**Polygon Drawing UX Notes:**
- Provide "Undo Last Vertex" button
- Show vertex count indicator (e.g., "3 vertices - click to add more, double-click to finish")
- Highlight first vertex (shows where polygon will close)
- Preset templates: Rectangle (4 clicks), Triangle (3 clicks), L-shape (6 clicks)

## Non-Functional Requirements

### Performance

**Motion Detection Latency (CRITICAL):**
- Motion detection processing: <100ms per frame (PRD NFR1.1)
- Target: 50-80ms on 2-core system at 5 FPS
- Algorithm selection based on performance:
  - MOG2: ~30-50ms (fastest, recommended default)
  - KNN: ~40-60ms (better accuracy, slight slowdown)
  - Frame Differencing: ~20-30ms (fastest but less accurate)

**End-to-End Event Processing:**
- Motion detection → Event storage: <200ms
- Total latency budget (motion → AI description): <5 seconds (PRD requirement)
- Motion detection budget: <500ms (10% of total)

**Throughput:**
- Support 1-4 cameras simultaneously with motion detection enabled
- Process up to 120 frames/second total (4 cameras × 30 FPS) with <5% CPU increase per camera
- Motion event storage: Handle bursts of 10 events/second without queue backup

**Resource Utilization:**
- CPU usage: <10% additional per camera with motion detection (on top of F1 baseline)
- Memory: <100MB additional for background models (MOG2/KNN maintain frame history)
- Database: Motion events ~1KB each, estimate 100 events/day/camera = 36MB/year/camera

**Sensitivity Thresholds (calibrated):**
- **Low:** 5% of frame pixels changed (fewer false positives, may miss small movements)
- **Medium:** 2% of frame pixels changed (balanced, default)
- **High:** 0.5% of frame pixels changed (sensitive, catches all movement, higher false positives)

**Performance Baseline (from F1 Retrospective Action Item #4):**
- Document actual CPU/memory with 1 camera @ 5 FPS + motion detection
- Test on: macOS (M1/Intel), Linux (Ubuntu 22.04, 2-core VM)
- Use as reference for optimization

### Security

**Input Validation:**
- Detection zone coordinates validated (bounds checking: 0 ≤ x,y < frame dimensions)
- Sensitivity parameter validated (enum: low, medium, high only)
- Schedule time ranges validated (24-hour format, valid days of week)
- SQL injection prevented (SQLAlchemy ORM, no raw SQL)

**Data Privacy:**
- Motion event thumbnails stored as base64 JPEG (no raw video)
- Thumbnail storage optional (configurable per camera)
- No continuous video recording (event-driven only)
- Motion events deletable by user (data ownership)

**API Security:**
- Motion configuration endpoints require authentication (Phase 1.5: F7.1)
- Rate limiting on motion test endpoint (10 requests/minute to prevent abuse)
- No sensitive data in motion event responses (only metadata, no credentials)

**Thread Safety:**
- MotionDetector state thread-safe (separate instance per camera thread)
- Background models (MOG2/KNN) not shared between threads
- Event storage uses database transactions (ACID guarantees)

### Reliability/Availability

**Fault Tolerance:**
- Motion detection failures logged but don't crash camera thread
- If algorithm throws exception → Log error, continue with next frame
- Invalid detection zones ignored with warning (don't block detection)
- Schedule parsing errors → Default to "always enabled"

**Graceful Degradation:**
- If database unavailable → Motion events queued in memory (max 100 events)
- If memory queue full → Drop oldest events, log warning
- If motion detector initialization fails → Disable detection, log error, camera capture continues

**Recovery:**
- Background model reset on sensitivity change (prevents stale data)
- Automatic background model update (MOG2/KNN learn over time)
- If detection stuck (no events >1 hour) → Reset background model

**Cooldown Behavior:**
- Cooldown period prevents alert spam (30s default, configurable 5-300s)
- Cooldown tracked per camera (not global)
- Manual trigger bypasses cooldown (user-initiated test)

### Observability

**Logging Requirements:**
- **INFO:** Motion detected events (timestamp, camera, confidence, bounding box size)
- **DEBUG:** Frame processing metrics (algorithm timing, pixel change %, zone filtering)
- **WARNING:** False positive suppression (motion below threshold), invalid zones, schedule parse errors
- **ERROR:** Algorithm exceptions, database write failures, memory queue overflow

**Metrics to Track:**
- Motion events per camera per hour (detect anomalies)
- Average detection confidence per camera
- Algorithm processing time (p50, p95, p99)
- False positive rate (manual user feedback in F5)
- Detection zone hit rate (which zones trigger most events)

**Structured Logging Format:**
```python
logger.info(
    "Motion detected",
    extra={
        "camera_id": camera.id,
        "confidence": 0.87,
        "algorithm": "mog2",
        "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 150},
        "zone_triggered": "front_door",
        "processing_time_ms": 45
    }
)
```

**Debugging Support:**
- Motion test endpoint returns preview image with bounding box overlay (visual verification)
- Detection zone overlay rendering in frontend (verify zone placement)
- Event timeline shows confidence scores (identify low-confidence events)
- Export motion events to CSV for analysis (future enhancement)

## Dependencies and Integrations

### Backend Dependencies (Python 3.13+)

**Existing Dependencies (from F1):**
- `opencv-python >= 4.12.0` - **REUSED** for motion detection algorithms (MOG2, KNN, frame differencing)
- `fastapi[standard] == 0.115.0` - REST API framework
- `sqlalchemy >= 2.0.36` - ORM for motion_events table
- `alembic >= 1.14.0` - Database migrations
- `pydantic >= 2.10.0` - Data validation schemas

**New Dependencies (none required):**
- All motion detection functionality available in existing OpenCV installation
- No additional Python packages needed for F2

### Frontend Dependencies (Node.js 18+)

**Existing Dependencies (from F1.2):**
- `next 16.0.3` - React framework
- `react 19.2.0` / `react-dom 19.2.0` - UI library
- `react-hook-form ^7.66.0` - Form management (reuse for motion config forms)
- `zod ^4.1.12` - Schema validation (extend for motion schemas)
- `@radix-ui/react-slider ^1.3.6` - **REUSED** for sensitivity slider
- `lucide-react ^0.553.0` - Icons (motion icons: Activity, Eye, Clock, Calendar)

**New Dependencies (for polygon drawing - DECISION-1):**
- **Option A:** `react-konva` - Canvas library with built-in polygon/line drawing tools
  - Pros: Rich feature set, touch support, undo/redo built-in
  - Cons: Larger bundle size (~150KB)
- **Option B:** Custom HTML5 Canvas implementation with click handlers
  - Pros: Zero dependencies, full control, smaller bundle
  - Cons: Must implement polygon drawing, undo, touch support manually
- **Recommendation:** Evaluate both in F2.2 implementation (likely custom canvas for simplicity)

### Integration Points

**Epic F1 Dependencies:**
- **CameraService** (F1.1) - Extends `_capture_loop()` to call MotionDetectionService
- **Camera Model** (F1.1) - Add motion_* fields via Alembic migration
- **Database** (F1.1) - Reuse SQLAlchemy session management, add motion_events table
- **API Router** (F1.1) - Mount motion endpoints at `/api/v1/motion-*`
- **Frontend Components** (F1.2) - Reuse Loading, EmptyState, ConfirmDialog components

**Future Epic Dependencies:**
- **Epic F3 (AI Description Generation)** - Consumes motion events (ai_event_id foreign key)
- **Epic F5 (Alert Rule Engine)** - Evaluates motion events against alert rules
- **Epic F6 (Dashboard UI)** - Displays motion event timeline

**External System Integrations:**
- None (motion detection is self-contained, no external APIs)

### Version Constraints

**Backend:**
- Python >= 3.13 (established in F1)
- OpenCV >= 4.12.0 (Python 3.13 compatibility)
- FastAPI >= 0.115.0 (async support)

**Frontend:**
- Node.js >= 18 (ES modules support)
- Next.js 16.0.3 (App Router)
- TypeScript >= 5 (strict mode)

**Database:**
- SQLite 3.35+ (JSON functions for detection_zones)
- PostgreSQL 12+ (future migration path, optional)

## Acceptance Criteria (Authoritative)

**From PRD F2.1: Motion Detection Algorithm**

**AC-1:** System detects person entering frame >90% of the time
- Algorithm must identify motion when person walks into camera view
- Test with 10 video clips (person entering from different angles)
- Success: 9+ clips trigger motion detection

**AC-2:** False positive rate <20% (non-person motion)
- Test with 10 video clips (trees swaying, shadows, rain, lights changing)
- Success: ≤2 clips trigger false positive motion events

**AC-3:** Motion detection processing latency <100ms per frame
- Measure time from frame read to motion detection result
- Test at 5 FPS, 15 FPS, 30 FPS on reference hardware (2-core system)
- Success: p95 latency <100ms

**AC-4:** Configurable sensitivity levels (low, medium, high) work as expected
- Low: Detects only large/obvious movements (person walking)
- Medium: Detects medium movements (person waving, pet moving)
- High: Detects small movements (leaves, curtains, small animals)
- Test each sensitivity level with 5 video clips of varying motion intensity

**AC-5:** Cooldown period prevents repeated triggers (30-60 seconds default)
- Trigger motion event at T=0
- Continuous motion detected for next 60 seconds
- Success: Only 1 event created (subsequent motion ignored during cooldown)

**From PRD F2.2: Motion Detection Zones**

**AC-6:** UI allows drawing polygon zones on camera preview (DECISION-1)
- User can click to add vertices (minimum 3) to create arbitrary polygon shapes
- Zone coordinates saved relative to image dimensions (0-1 normalized)
- Multiple zones per camera supported (max 10)
- Polygon auto-closes when user finishes drawing

**AC-7:** Motion outside defined zones doesn't trigger events (polygon geometry)
- Define polygon zone covering 50% of frame (e.g., left half as 4-vertex polygon)
- Generate motion in right half (outside zone polygon)
- Success: No motion event created (point-in-polygon check excludes motion)

**AC-8:** Zones can be enabled/disabled independently
- Create 2 zones: "Zone A" (enabled), "Zone B" (disabled)
- Generate motion in Zone B
- Success: No event (Zone B disabled)
- Generate motion in Zone A
- Success: Event created (Zone A enabled)

**From PRD F2.3: Detection Schedule**

**AC-9:** Time-based schedules work correctly
- Set schedule: 9:00 AM - 5:00 PM only
- Test at 8:59 AM (before): No detection
- Test at 9:01 AM (during): Detection active
- Test at 5:01 PM (after): No detection

**AC-10:** Day-of-week scheduling works correctly
- Set schedule: Monday, Wednesday, Friday only
- Test on Tuesday: No detection (even within time range)
- Test on Wednesday: Detection active

**From PRD F2 General:**

**AC-11:** Motion events stored in database with metadata
- Trigger motion detection
- Verify database record created with:
  - camera_id, timestamp, confidence, algorithm, bounding_box
  - Event ID generated (UUID)

**AC-12:** Motion configuration persists across system restarts
- Set sensitivity = "high", cooldown = 60s, zones = [zone1]
- Restart backend server
- Verify configuration loaded from database (same values)

## Traceability Mapping

| AC # | Description | Spec Section | Components/APIs | Test Type | Story |
|------|-------------|--------------|-----------------|-----------|-------|
| AC-1 | Person detection >90% | Detailed Design → MotionDetector | MotionDetectionService, MotionDetector | Integration test with video clips | F2.1 |
| AC-2 | False positive <20% | NFR Performance → Sensitivity Thresholds | MotionDetector, sensitivity thresholds | Integration test with negative clips | F2.1 |
| AC-3 | Latency <100ms | NFR Performance → Motion Detection Latency | MotionDetector algorithms (MOG2/KNN) | Performance test (timing) | F2.1 |
| AC-4 | Sensitivity levels work | Data Models → motion_sensitivity | Camera model, MotionDetector | Unit test (threshold variations) | F2.1 |
| AC-5 | Cooldown prevents spam | Workflows → Motion Detection Flow (Step 4) | MotionDetectionService cooldown tracking | Unit test (time-based) | F2.1 |
| AC-6 | UI zone drawing | APIs → PUT /motion/config, Frontend DetectionZoneDrawer | DetectionZoneDrawer component, Canvas API | E2E test (Playwright) | F2.2 |
| AC-7 | Zones filter motion | Detailed Design → DetectionZoneManager | DetectionZoneManager.filter_by_zones() (point-in-polygon) | Unit test (polygon geometry) | F2.2 |
| AC-8 | Enable/disable zones | Data Models → DetectionZone.enabled | DetectionZoneManager, Camera.detection_zones | Unit test (config) | F2.2 |
| AC-9 | Time-based schedule | Detailed Design → ScheduleManager | ScheduleManager.is_active() | Unit test (datetime) | F2.3 |
| AC-10 | Day-of-week schedule | Data Models → DetectionSchedule.days | ScheduleManager, Camera.detection_schedule | Unit test (day checking) | F2.3 |
| AC-11 | Event storage | Data Models → MotionEvent | MotionEventStore, motion_events table | Integration test (DB) | F2.1 |
| AC-12 | Config persistence | Data Models → Camera (motion fields) | Camera model, database migration | Integration test (restart) | F2.1 |

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: Algorithm Selection Uncertainty** (HIGH)
- **Description:** Uncertain which OpenCV algorithm (MOG2, KNN, frame differencing) best balances accuracy vs performance
- **Impact:** Wrong algorithm choice may require rework, fail to meet <100ms latency or >90% detection rate
- **Mitigation:**
  - Research spike at start of F2.1 (1 day): Test all 3 algorithms with real footage
  - Benchmark performance (latency) and accuracy (detection rate) on reference hardware
  - Document decision rationale in F2.1 story
  - Make algorithm configurable (allow users to switch if needed)

**RISK-2: False Positive Rate Too High** (HIGH)
- **Description:** PRD requires <20% false positive rate, difficult to achieve with generic motion detection
- **Impact:** Alert fatigue, users disable motion detection, product value diminished
- **Mitigation:**
  - Sensitivity tuning during development (test with diverse footage)
  - Detection zones reduce false positives (ignore trees, street, etc.)
  - Cooldown period limits spam from repeated false positives
  - User feedback loop (future: ML model to learn false positives)
  - Action Item from F1 Retro: Acquire diverse test footage early

**RISK-3: Performance Impact on Multi-Camera Setups** (MEDIUM)
- **Description:** Motion detection adds CPU overhead, may not support 4 cameras simultaneously at 30 FPS
- **Impact:** System unusable with multiple cameras, users limited to 1-2 cameras
- **Mitigation:**
  - Performance baseline story (F1 Retro Action Item #4) - measure actual impact
  - Optimize algorithm (use MOG2 for speed, reduce FPS if needed)
  - Hardware recommendations in documentation (4-core minimum for 4 cameras)
  - Graceful degradation (auto-reduce FPS if CPU >80%)

**RISK-4: Detection Zone UI Complexity** (MEDIUM)
- **Description:** Drawing zones on camera preview with mouse/touch is complex, poor UX if buggy
- **Impact:** Users struggle to configure zones, abandon feature
- **Mitigation:**
  - Use existing canvas library (react-sketch-canvas) vs custom implementation
  - Provide preset zone templates ("Top Half", "Bottom Half", "Center")
  - Include zone drawing tutorial/demo in UI
  - Test on mobile devices early (touch events different from mouse)

**RISK-5: Scheduling Edge Cases** (LOW)
- **Description:** Time zone handling, daylight saving time transitions may cause schedule bugs
- **Impact:** Detection active/inactive at wrong times
- **Mitigation:**
  - Use UTC timestamps internally, convert to user timezone for display
  - Test schedule transitions (midnight, DST change)
  - Document timezone behavior in UI
  - Simple schedule format (avoid complex recurrence rules in MVP)

### Assumptions

**ASSUMPTION-1:** OpenCV 4.12+ includes MOG2 and KNN algorithms (cv2.createBackgroundSubtractorMOG2, cv2.createBackgroundSubtractorKNN)
- **Validation:** Verify in OpenCV documentation and test installation
- **Fallback:** Use frame differencing if background subtractors unavailable

**ASSUMPTION-2:** Users will configure detection zones to reduce false positives
- **Validation:** User testing in beta (F1 Retro Action Item #1)
- **Fallback:** Provide good default sensitivity (medium) that works without zones

**ASSUMPTION-3:** 30-second cooldown is acceptable to users (not too long, not too short)
- **Validation:** User feedback during beta testing
- **Fallback:** Make cooldown configurable (5-300 seconds) in F2.1

**ASSUMPTION-4:** SQLite JSON functions (json_extract) work reliably for detection_zones and detection_schedule
- **Validation:** Test JSON queries on SQLite 3.35+
- **Fallback:** Use TEXT columns with manual JSON parsing in Python

**ASSUMPTION-5:** Motion detection processing <100ms leaves sufficient CPU headroom for AI processing (F3)
- **Validation:** Performance baseline story (measure actual CPU with motion enabled)
- **Fallback:** Reduce FPS or resolution if CPU constrained

### Decisions Made (2025-11-15)

**DECISION-1: Detection Zones - Polygons** ✅
- **Decision:** Implement polygon-based detection zones (not rectangles)
- **Rationale:** Greater flexibility for users to define complex zones (exclude doorways, include only driveway sections)
- **Implementation Impact:**
  - Frontend: Polygon drawing tool (click to add vertices, close polygon)
  - Backend: Point-in-polygon algorithm for geometry checks (ray casting or winding number)
  - Performance: Slightly slower than rectangles (~5-10ms overhead), acceptable for <100ms budget
- **User Benefit:** Can precisely match detection zones to property boundaries, ignore specific areas
- **Future Enhancement:** Provide preset zone templates (rectangle, triangle, L-shape) for common use cases

**DECISION-2: Motion Event Thumbnails - Full Frame** ✅
- **Decision:** Store full frame thumbnail (not bounding box crop or no thumbnail)
- **Rationale:** Provides complete visual context for reviewing motion events, helps identify false positives
- **Storage Impact:**
  - Size: ~50KB per event (640x480 JPEG, quality 85%)
  - Estimate: 100 events/day/camera = 5MB/day = 150MB/month/camera
  - Acceptable for MVP (SQLite can handle, user can delete old events)
- **Implementation:** Base64 encode JPEG, store in motion_event.frame_thumbnail column (TEXT)
- **Future Enhancement:** Add configurable thumbnail options (full frame, bounding box crop, none) in settings

**DECISION-3: Schedule Complexity - Single Time Range** ✅
- **Decision:** Support single time range per day only (not multiple ranges)
- **Rationale:** Simpler UI and implementation for MVP, covers 80% of use cases (e.g., "9am-5pm only")
- **Implementation:** DetectionSchedule schema has single time_range field: {"start": "09:00", "end": "17:00"}
- **User Workaround:** Users needing multiple ranges (e.g., 6-9am AND 6-11pm) can use two cameras or disable/enable manually
- **Future Enhancement:** If user feedback demands it, extend to support array of time ranges

**DECISION-4: Motion Test Endpoint - Ephemeral** ✅
- **Decision:** POST /motion/test returns result only, does NOT save to database
- **Rationale:** Matches camera test connection pattern from F1, prevents test pollution in motion events table
- **Implementation:** Run motion detection algorithm on current frame, return preview image with bounding box overlay, no database write
- **Consistency:** Aligns with F1 design philosophy (test endpoints are non-mutating)

**DECISION-5: Real-time Notifications - Polling** ✅
- **Decision:** Use polling (GET /motion-events) for F2, defer WebSocket to Epic F6
- **Rationale:** Simpler implementation, 5-10 second latency acceptable for motion event review (not real-time critical)
- **Implementation:** Frontend polls GET /motion-events?since=<last_timestamp> every 5-10 seconds
- **WebSocket Deferral:** Epic F6 (Dashboard & Notifications) will implement WebSocket for real-time updates across all event types
- **Performance:** Polling every 5s with 4 cameras = 0.8 requests/sec, negligible load

## Test Strategy Summary

### Test Levels

**Unit Tests (pytest):**
- **MotionDetector algorithms:** Test MOG2, KNN, frame differencing with synthetic images (black background, white moving square)
- **Sensitivity thresholds:** Verify low/medium/high correctly filter based on pixel change percentage
- **DetectionZoneManager (DECISION-1):** Test polygon zone filtering geometry
  - Point-in-polygon algorithm (ray casting or winding number)
  - Test with triangles, rectangles, complex polygons (L-shape, concave)
  - Edge cases: Motion on polygon boundary, polygon with self-intersecting edges
- **ScheduleManager:** Test single time range checking (DECISION-3), day-of-week logic, edge cases (midnight, DST)
- **Cooldown logic:** Test time-based cooldown enforcement
- **Target Coverage:** 80%+ for motion detection services

**Integration Tests (pytest + TestClient):**
- **Motion API endpoints:** Test all CRUD operations (create config, update, get events, delete)
- **Database persistence:** Verify motion events saved correctly with all fields
- **Camera integration:** Test motion detection in camera capture loop (mocked VideoCapture)
- **Config reload:** Test configuration changes applied to running detectors
- **Target Coverage:** All API endpoints, all database operations

**Performance Tests:**
- **Latency benchmarks:** Measure motion detection processing time (p50, p95, p99) at different resolutions
- **Multi-camera load:** Test 1, 2, 4 cameras with motion detection enabled, measure CPU/memory
- **Baseline documentation:** Record metrics on reference hardware (Action Item #4 from F1 Retro)
- **Tools:** pytest-benchmark, cProfile for profiling

**Algorithm Accuracy Tests (Real Footage):**
- **True Positive Rate:** 10 videos with person entering frame → 9+ detections required (AC-1)
- **False Positive Rate:** 10 videos with non-person motion → ≤2 false positives required (AC-2)
- **Footage Sources:**
  - Action Item from F1 Retro: Acquire diverse test footage (indoor, outdoor, day, night)
  - Use public datasets (PETS, ChangeDetection.net) if available
  - Record own test footage with physical cameras

**Frontend Tests (Deferred - see F1 Retro Action Item #3):**
- **Component tests (Jest + React Testing Library):**
  - MotionConfigForm validation
  - DetectionZoneDrawer canvas interactions
  - MotionEventList rendering
- **E2E tests (Playwright):**
  - Full flow: Configure sensitivity → Draw zone → Trigger motion → Verify event appears
  - Schedule configuration flow
  - Motion test endpoint integration

**Manual Testing Checklist:**
- [ ] Test all 3 algorithms (MOG2, KNN, frame differencing) with real camera footage
- [ ] Verify sensitivity levels work as expected (low detects large motion only, high detects all motion)
- [ ] Draw polygon detection zones on camera preview (DECISION-1)
  - [ ] Test simple polygon (triangle, rectangle)
  - [ ] Test complex polygon (L-shape, 6+ vertices)
  - [ ] Verify motion outside polygon zones ignored
  - [ ] Test zone enable/disable toggle
- [ ] Configure single time range schedule + days (DECISION-3), verify detection only active during schedule
- [ ] Test cooldown period (30s), verify repeated motion doesn't spam events
- [ ] Test motion detection with RTSP camera (from F1.1)
- [ ] Test motion detection with USB camera (from F1.3)
- [ ] Verify motion events appear in database with full frame thumbnails (DECISION-2)
- [ ] Test configuration persistence (restart backend, verify config reloaded including polygon zones)
- [ ] Performance validation: Measure CPU/memory with 1 camera @ 5 FPS + motion enabled + polygon zone filtering

### Test Data

**Video Clips Needed:**
- 10 clips with person entering frame (true positives)
- 10 clips with non-person motion (false positives): trees, rain, shadows, lights, curtains, reflections
- 5 clips with varying motion intensity (for sensitivity testing)
- Duration: 10-30 seconds each
- Resolution: 640x480 (VGA) minimum

**Test Environments:**
- macOS (M1/Intel) - Primary development
- Linux (Ubuntu 22.04, 2-core VM) - CI/CD
- Windows 10+ (optional, lower priority - PRD NFR6.3)

### Exit Criteria

**Epic F2 Complete When:**
- [ ] All 12 acceptance criteria met (AC-1 through AC-12)
- [ ] 80%+ backend test coverage (unit + integration)
- [ ] All API endpoints tested and documented
- [ ] Performance baseline documented (CPU/memory with motion enabled)
- [ ] Algorithm selection decision documented with rationale
- [ ] False positive rate <20% validated with real footage
- [ ] Motion detection works with both RTSP and USB cameras
- [ ] Frontend manual testing checklist completed
- [ ] Code review approved (systematic validation per F1 pattern)
- [ ] No blocking bugs, <5 high-severity bugs
