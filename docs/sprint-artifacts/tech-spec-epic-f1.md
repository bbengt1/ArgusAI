# Epic Technical Specification: Camera Feed Integration

Date: 2025-11-15
Author: Brent
Epic ID: f1
Status: Draft

---

## Overview

The Camera Feed Integration epic establishes the foundational infrastructure for capturing video feeds from both RTSP-enabled IP cameras and USB webcams. This epic serves as the entry point for all video data into the Live Object AI Classifier system. The implementation focuses on robust connection handling, automatic reconnection logic, and a user-friendly configuration interface that enables non-technical users to set up cameras in under 5 minutes.

This epic is the prerequisite for all downstream functionality (motion detection, AI analysis, and event generation). Without reliable camera capture, the entire system cannot function. The architecture supports single-camera MVP with design patterns that scale to multi-camera in Phase 2.

## Objectives and Scope

**In Scope:**
- RTSP camera connection with authentication (basic auth, digest auth)
- USB/webcam support for local cameras
- Camera configuration CRUD operations via REST API
- Dashboard UI for camera setup and management
- Automatic reconnection on stream dropout (30-second retry intervals)
- Frame capture at configurable rates (1-30 FPS, default 5 FPS)
- Connection testing and preview thumbnail generation
- Multi-codec support (H.264, H.265, MJPEG)

**Out of Scope (Deferred to Phase 2):**
- Multi-camera simultaneous capture (MVP = single camera)
- PTZ (Pan-Tilt-Zoom) camera controls
- Motion detection zones (covered in Epic F2)
- ONVIF discovery protocol for camera auto-detection
- Audio capture from camera streams
- Recording/storage of video footage (system stores descriptions only)

## System Architecture Alignment

**Backend Components:**
- `app/services/camera_service.py` - Core capture logic, thread management, RTSP/USB handling
- `app/api/v1/cameras.py` - REST API endpoints for camera CRUD operations
- `app/models/camera.py` - SQLAlchemy ORM model for camera configuration
- `app/schemas/camera.py` - Pydantic schemas for request/response validation
- `app/core/database.py` - Database connection and session management

**Frontend Components:**
- `app/cameras/page.tsx` - Camera list/grid view with status indicators
- `app/cameras/new/page.tsx` - Add camera form
- `app/cameras/[id]/page.tsx` - Edit camera configuration
- `components/cameras/CameraForm.tsx` - Reusable form component
- `components/cameras/CameraPreview.tsx` - Preview tile with thumbnail
- `components/cameras/CameraStatus.tsx` - Connection status indicator
- `hooks/useCameras.ts` - Custom hook for camera CRUD operations

**External Dependencies:**
- OpenCV (`opencv-python 4.8+`) - Camera capture via `cv2.VideoCapture`
- FastAPI (`0.115+`) - REST API framework
- SQLAlchemy (`2.0+`) - Database ORM for camera persistence
- Next.js (`15.x`) - Frontend framework with App Router
- shadcn/ui components - Form inputs, buttons, dialogs

**Architecture Constraints:**
- Single camera active in MVP (enforced at API layer)
- Frame capture runs in dedicated background thread per camera
- Camera passwords encrypted at rest using Fernet (AES-256)
- All timestamps stored in UTC (SQLite without timezone)
- API responses use HTTP-only cookies for session management (Phase 1.5)

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs | Owner |
|--------|---------------|--------|---------|-------|
| `CameraService` | Manages camera capture threads, handles connection lifecycle | Camera config from DB | Raw frames (numpy arrays), connection status events | Backend |
| `CameraAPI` | REST endpoints for camera CRUD, validation | HTTP requests with camera data | JSON responses, HTTP status codes | Backend |
| `CameraModel` | SQLAlchemy ORM, defines schema, encryption hooks | SQL queries | Camera entities | Backend |
| `CameraSchema` | Pydantic validation, serialization | Request bodies, DB models | Validated data objects | Backend |
| `CameraForm` | React form component, validation, submit logic | User input | API calls to create/update camera | Frontend |
| `useCameras` | React hook, manages camera state, API calls | User actions | Camera list, loading state, errors | Frontend |
| `CameraPreview` | Display camera thumbnail, status, actions | Camera entity | Rendered UI tile | Frontend |

### Data Models and Contracts

**Database Schema (`cameras` table):**

```sql
CREATE TABLE cameras (
    id TEXT PRIMARY KEY,                    -- UUID v4
    name TEXT NOT NULL,                     -- User-friendly name (e.g., "Front Door")
    type TEXT NOT NULL,                     -- 'rtsp' | 'usb'
    rtsp_url TEXT,                          -- Full RTSP URL (e.g., rtsp://192.168.1.50:554/stream1)
    username TEXT,                          -- RTSP auth username (nullable)
    password TEXT,                          -- Encrypted password (Fernet, nullable)
    device_index INTEGER,                   -- USB device index (0, 1, 2..., nullable for RTSP)
    frame_rate INTEGER DEFAULT 5,           -- Target FPS (1-30)
    is_enabled BOOLEAN DEFAULT TRUE,        -- Active/inactive toggle
    motion_sensitivity TEXT DEFAULT 'medium', -- 'low' | 'medium' | 'high' (used in F2)
    motion_cooldown INTEGER DEFAULT 60,     -- Seconds between motion triggers (used in F2)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Constraints
CHECK (type IN ('rtsp', 'usb'))
CHECK (frame_rate >= 1 AND frame_rate <= 30)
CHECK (motion_sensitivity IN ('low', 'medium', 'high'))
CHECK (motion_cooldown >= 0 AND motion_cooldown <= 300)

-- Indexes
CREATE INDEX idx_cameras_is_enabled ON cameras(is_enabled);
```

**SQLAlchemy Model:**

```python
# app/models/camera.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import validates
from app.core.database import Base
from app.utils.encryption import encrypt_password, decrypt_password
import uuid
from datetime import datetime

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'rtsp' or 'usb'
    rtsp_url = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)  # Encrypted
    device_index = Column(Integer, nullable=True)
    frame_rate = Column(Integer, default=5)
    is_enabled = Column(Boolean, default=True)
    motion_sensitivity = Column(String, default='medium')
    motion_cooldown = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("type IN ('rtsp', 'usb')", name='check_camera_type'),
        CheckConstraint("frame_rate >= 1 AND frame_rate <= 30", name='check_frame_rate'),
        CheckConstraint("motion_sensitivity IN ('low', 'medium', 'high')", name='check_sensitivity'),
    )
    
    @validates('password')
    def encrypt_password(self, key, value):
        """Encrypt password before storing."""
        if value and not value.startswith('encrypted:'):
            return encrypt_password(value)
        return value
    
    def get_decrypted_password(self) -> str:
        """Decrypt password for use in RTSP connection."""
        if self.password and self.password.startswith('encrypted:'):
            return decrypt_password(self.password)
        return self.password
```

**Pydantic Schemas:**

```python
# app/schemas/camera.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

class CameraBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal['rtsp', 'usb']
    frame_rate: int = Field(default=5, ge=1, le=30)
    is_enabled: bool = True
    motion_sensitivity: Literal['low', 'medium', 'high'] = 'medium'
    motion_cooldown: int = Field(default=60, ge=0, le=300)

class CameraCreate(CameraBase):
    rtsp_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    device_index: Optional[int] = None
    
    @validator('rtsp_url')
    def validate_rtsp_url(cls, v, values):
        if values.get('type') == 'rtsp' and not v:
            raise ValueError("RTSP URL required for RTSP cameras")
        if v and not v.startswith(('rtsp://', 'rtsps://')):
            raise ValueError("RTSP URL must start with rtsp:// or rtsps://")
        return v
    
    @validator('device_index')
    def validate_device_index(cls, v, values):
        if values.get('type') == 'usb' and v is None:
            raise ValueError("Device index required for USB cameras")
        return v

class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rtsp_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    frame_rate: Optional[int] = Field(None, ge=1, le=30)
    is_enabled: Optional[bool] = None
    motion_sensitivity: Optional[Literal['low', 'medium', 'high']] = None
    motion_cooldown: Optional[int] = Field(None, ge=0, le=300)

class CameraResponse(CameraBase):
    id: str
    rtsp_url: Optional[str] = None
    username: Optional[str] = None
    device_index: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### APIs and Interfaces

**REST API Endpoints:**

```
Base URL: http://localhost:8000/api/v1
```

**1. List Cameras**
```
GET /cameras
Query Params:
  - is_enabled: boolean (optional filter)
Response 200:
  {
    "data": [
      {
        "id": "uuid",
        "name": "Front Door",
        "type": "rtsp",
        "rtsp_url": "rtsp://192.168.1.50:554/stream1",
        "username": "admin",
        "frame_rate": 5,
        "is_enabled": true,
        "motion_sensitivity": "medium",
        "motion_cooldown": 60,
        "created_at": "2025-11-15T10:00:00Z",
        "updated_at": "2025-11-15T10:00:00Z"
      }
    ],
    "meta": {
      "total": 1
    }
  }
```

**2. Get Camera by ID**
```
GET /cameras/{id}
Response 200: Same as list item
Response 404: { "detail": "Camera not found" }
```

**3. Create Camera**
```
POST /cameras
Body:
  {
    "name": "Front Door",
    "type": "rtsp",
    "rtsp_url": "rtsp://192.168.1.50:554/stream1",
    "username": "admin",
    "password": "secret123",
    "frame_rate": 5,
    "is_enabled": true
  }
Response 201: CameraResponse object
Response 400: { "detail": "Validation error message" }
Response 409: { "detail": "Camera with this name already exists" }
```

**4. Update Camera**
```
PUT /cameras/{id}
Body: Partial CameraUpdate object
Response 200: Updated CameraResponse
Response 404: { "detail": "Camera not found" }
Response 400: { "detail": "Validation error" }
```

**5. Delete Camera**
```
DELETE /cameras/{id}
Response 200: { "data": { "deleted": true }, "meta": {} }
Response 404: { "detail": "Camera not found" }
```

**6. Test Camera Connection**
```
POST /cameras/{id}/test
Response 200:
  {
    "data": {
      "success": true,
      "message": "Connection successful",
      "thumbnail": "base64_encoded_jpeg_image"
    },
    "meta": {}
  }
Response 200 (failure):
  {
    "data": {
      "success": false,
      "message": "Connection failed: RTSP authentication failed (401)"
    }
  }
Response 404: { "detail": "Camera not found" }
```

**Error Response Format:**
```json
{
  "detail": "Error message",
  "status_code": 400,
  "errors": [
    {
      "field": "rtsp_url",
      "message": "RTSP URL must start with rtsp://"
    }
  ]
}
```

### Workflows and Sequencing

**Camera Setup Flow:**

```
User → Frontend                   → Backend API              → CameraService       → OpenCV        → Database
  |                                   |                         |                     |               |
  1. Open "Add Camera" form          |                         |                     |               |
  2. Fill in details                 |                         |                     |               |
     (name, RTSP URL, creds)         |                         |                     |               |
  3. Click "Test Connection" ────────→ POST /cameras/test     |                     |               |
                                      |  (temp camera data)     |                     |               |
                                      └────────────────────────→ 4. Create VideoCapture              |
                                                                |    with RTSP URL    |               |
                                                                └────────────────────→ 5. Attempt connection
                                                                                      |    (3 sec timeout)
                                                                6. Capture 1 frame   ←────────────────┘
                                      ←────────────────────────┐    or error         |
  ← 7. Show "Connected!" or error   |                         |                     |
     with thumbnail preview          |                         |                     |
  8. Click "Save Camera"  ──────────→ POST /cameras           |                     |
                                      |  (validated data)      |                     |
                                      └────────────────────────────────────────────────→ 9. INSERT camera
                                      ←────────────────────────────────────────────────┘    return ID
  10. Redirect to camera list        ←─────────────────────────                      |
```

**Camera Capture Thread Lifecycle:**

```
App Startup
    |
    ├── Load all cameras from DB (is_enabled=true)
    |
    └── For each enabled camera:
            |
            ├── Spawn CameraService.start_camera(camera)
            |       |
            |       ├── Create background thread
            |       └── Start _capture_loop(camera)
            |               |
            |               ├── Initialize cv2.VideoCapture
            |               |   (RTSP URL or USB device_index)
            |               |
            |               ├── Loop: while is_enabled:
            |               |       |
            |               |       ├── Read frame (ret, frame = cap.read())
            |               |       |
            |               |       ├── If ret == False:
            |               |       |   └── Log error, attempt reconnect (30s delay)
            |               |       |
            |               |       ├── Pass frame to MotionDetectionService (F2)
            |               |       |
            |               |       ├── Sleep to maintain target FPS
            |               |       |   (e.g., sleep(1/5) for 5 FPS)
            |               |       |
            |               |       └── Check if camera disabled in DB
            |               |
            |               └── On exit: Release VideoCapture
            |
            └── Store thread reference in _capture_threads[camera_id]

User Disables Camera
    |
    └── PUT /cameras/{id} (is_enabled=false)
            |
            └── CameraService.stop_camera(camera_id)
                    |
                    ├── Set stop flag for thread
                    ├── Wait for thread to join (5s timeout)
                    └── Remove from _capture_threads
```

**Reconnection Logic:**

```
Frame Capture Error Detected
    |
    ├── Log warning: "Camera {id} disconnected"
    |
    ├── Emit WebSocket event: CAMERA_STATUS_CHANGED
    |   { camera_id, status: "disconnected", timestamp }
    |
    ├── Sleep 30 seconds
    |
    ├── Attempt reconnection:
    |   ├── Release old VideoCapture
    |   ├── Create new VideoCapture with same config
    |   └── Try to read test frame
    |
    ├── If successful:
    |   ├── Log info: "Camera {id} reconnected"
    |   ├── Emit WebSocket: CAMERA_STATUS_CHANGED (status: "connected")
    |   └── Resume normal capture loop
    |
    └── If failed:
        └── Repeat from "Sleep 30 seconds" (infinite retry)
```

## Non-Functional Requirements

### Performance

**Target Metrics:**
- Camera connection establishment: <3 seconds (RTSP), <1 second (USB)
- Frame capture latency: <100ms per frame (at configured FPS)
- Test connection endpoint response: <5 seconds (includes 1 frame capture)
- API endpoint response time: <200ms (p95) for CRUD operations
- Memory usage per camera thread: <50MB baseline + frame buffer
- CPU usage per camera: <5% at 5 FPS (H.264 hardware decode if available)

**Performance Strategies:**
- Use hardware-accelerated decoding when available (OpenCV auto-detection)
- Background thread per camera prevents blocking main event loop
- Frame buffer size limited to 5 frames to prevent memory bloat
- Skip frames if processing falls behind (don't queue indefinitely)
- Connection pooling for database queries (SQLAlchemy default pool)
- Thumbnail generation offloaded to BackgroundTasks (async)

**Measurement Plan:**
- Log frame capture time for each frame (DEBUG level)
- Track reconnection attempts and success rate (INFO level)
- Monitor thread count and memory usage (health check endpoint)
- Unit tests with simulated slow cameras (inject delays)

### Security

**Authentication & Authorization (Phase 1.5):**
- Camera CRUD endpoints require valid JWT token
- Test connection endpoint requires authentication (prevents abuse)
- API key encryption using Fernet (symmetric encryption)
- HTTP-only cookies for session management (XSS protection)

**Data Protection:**
- Camera passwords encrypted at rest (AES-256 via Fernet)
- RTSP URLs with credentials never logged (sanitize logs)
- Password field write-only (never returned in API responses)
- Database backups include encrypted passwords (safe to store)

**Input Validation:**
- RTSP URL format validation (regex: `^rtsps?://`)
- Device index validation (integer >= 0)
- Frame rate bounds checking (1-30 FPS)
- Name length limits (1-100 characters)
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)

**Network Security:**
- RTSP connections support both basic auth and digest auth
- HTTPS/TLS for production API (self-signed cert acceptable for local)
- CORS configured to allow only frontend origin
- Rate limiting on test endpoint (10 requests/minute per IP)

### Reliability/Availability

**Fault Tolerance:**
- Automatic reconnection on stream dropout (30-second retry intervals)
- Infinite retry with exponential backoff (capped at 5 minutes)
- Graceful degradation: Continue other cameras if one fails
- Connection timeout: 10 seconds to prevent hanging threads
- Frame read timeout: 5 seconds before declaring disconnect

**Error Handling:**
- All exceptions caught and logged in capture loop (thread doesn't crash)
- Database connection errors trigger retry logic (3 attempts)
- Invalid RTSP credentials provide clear error message
- USB device not found shows user-friendly error

**Data Persistence:**
- Camera configuration persists across restarts (SQLite database)
- Capture threads resume automatically on app restart
- No data loss: Enabled cameras restart within 10 seconds of boot

**Monitoring:**
- Health check endpoint reports camera connection status
- WebSocket events broadcast connection state changes
- Structured logging for all errors (JSON format with context)
- Connection success/failure metrics logged per camera

### Observability

**Logging Requirements:**
- **DEBUG:** Frame capture details (timestamp, frame size, processing time)
- **INFO:** Camera started/stopped, connection state changes, reconnections
- **WARNING:** Slow frame capture (>200ms), reconnection attempts
- **ERROR:** Connection failures, invalid configurations, thread crashes
- **CRITICAL:** (Not applicable to this epic)

**Structured Log Format:**
```json
{
  "timestamp": "2025-11-15T10:30:00Z",
  "level": "INFO",
  "logger": "camera_service",
  "message": "Camera started successfully",
  "context": {
    "camera_id": "uuid",
    "camera_name": "Front Door",
    "camera_type": "rtsp",
    "frame_rate": 5
  }
}
```

**Metrics to Track:**
- Camera uptime percentage (connected time / total time)
- Reconnection count per camera
- Average frame capture latency
- Frame drop rate (frames skipped due to processing lag)
- API endpoint response times (percentiles)

**Dashboard Visibility:**
- Real-time connection status indicator (green/red dot)
- Last frame timestamp ("Last seen: 5 seconds ago")
- Connection uptime ("Connected for 2 hours")
- Reconnection history (log of disconnect/reconnect events)

## Dependencies and Integrations

**Backend Python Dependencies:**

```
# requirements.txt
fastapi[standard]==0.115.0      # Web framework with async support
opencv-python==4.8.1.78         # Camera capture and image processing
sqlalchemy==2.0.23              # ORM for database operations
alembic==1.12.1                 # Database migrations
pydantic==2.5.0                 # Data validation and serialization
python-jose[cryptography]==3.3.0 # JWT token handling (Phase 1.5)
passlib[bcrypt]==1.7.4          # Password hashing (Phase 1.5)
cryptography==41.0.7            # Fernet encryption for API keys
python-multipart==0.0.6         # Form data parsing
uvicorn[standard]==0.24.0       # ASGI server
```

**Frontend npm Dependencies:**

```json
{
  "dependencies": {
    "next": "15.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.294.0",
    "date-fns": "^3.0.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0"
  }
}
```

**System Dependencies:**
- Python 3.11+ (async/await, type hints)
- Node.js 20+ (Next.js 15 requirement)
- SQLite 3.x (bundled with Python)
- OpenCV native libraries (auto-installed with opencv-python)

**Integration Points:**

**Camera Service → Motion Detection (Epic F2):**
- Interface: `MotionDetectionService.detect_motion(frame: np.ndarray) -> bool`
- CameraService passes each captured frame to motion detector
- Motion detector returns True if significant motion detected
- Coupling: Loose (camera service doesn't know motion logic)

**Camera API → Database:**
- SQLAlchemy ORM handles all queries
- Async session management via dependency injection
- Transactions automatic per request (commit on success, rollback on error)

**Frontend → Backend API:**
- HTTP client: Built-in `fetch` with Next.js extensions
- Base URL: `http://localhost:8000/api/v1` (env variable)
- Error handling: Parse JSON error responses, show toast notifications
- Retry logic: 1 retry on network error (5-second timeout)

**No External Services:**
- All dependencies run locally (no cloud services)
- No third-party APIs required for camera functionality

## Acceptance Criteria (Authoritative)

**AC-1: RTSP Camera Support**
- [ ] System successfully connects to RTSP camera with valid URL and credentials
- [ ] Supports both basic auth and digest auth for RTSP
- [ ] Handles RTSP over TCP and UDP protocols
- [ ] Successfully captures frames at configured rate (tested at 1, 5, 15, 30 FPS)
- [ ] Supports H.264, H.265, and MJPEG video codecs (tested with 3 different camera brands)
- [ ] Connection timeout of 10 seconds prevents hanging indefinitely
- [ ] Invalid credentials return clear error message: "Authentication failed. Check username and password."

**AC-2: Automatic Reconnection**
- [ ] Detects stream dropout within 5 seconds (via failed frame read)
- [ ] Automatically attempts reconnection after 30-second delay
- [ ] Logs warning on disconnect: "Camera {name} disconnected"
- [ ] Logs info on successful reconnect: "Camera {name} reconnected"
- [ ] Emits WebSocket event on status change (CAMERA_STATUS_CHANGED)
- [ ] Maintains stable connection for 24+ hours continuous operation (soak test)
- [ ] Reconnects within 30-35 seconds of stream restoration

**AC-3: USB Camera Support**
- [ ] Auto-detects USB cameras connected to system
- [ ] Successfully captures frames from USB camera at configured FPS
- [ ] Works on Linux (V4L2) and macOS (AVFoundation) systems
- [ ] Handles camera disconnect gracefully (no crash, logs error)
- [ ] Reconnects automatically when USB camera plugged back in

**AC-4: Camera Configuration UI**
- [ ] Non-technical user can add camera in under 5 minutes (user testing)
- [ ] Form validates RTSP URL format before submission (must start with rtsp://)
- [ ] Username and password fields optional (some cameras don't require auth)
- [ ] Frame rate slider shows current value (1-30 FPS)
- [ ] "Test Connection" button provides feedback within 5 seconds
- [ ] Success feedback shows thumbnail preview of captured frame
- [ ] Error feedback shows actionable message (e.g., "Cannot reach camera. Check IP address and network.")
- [ ] Camera list shows connection status (green dot = connected, red = disconnected)
- [ ] Edit form pre-fills existing camera configuration
- [ ] Delete camera requires confirmation dialog: "Are you sure? This will delete all events from this camera."

**AC-5: Configuration Persistence**
- [ ] Camera configuration saved to database on form submission
- [ ] Changes take effect immediately (no restart required)
- [ ] Enabled cameras resume capture automatically after app restart
- [ ] Camera passwords stored encrypted in database (verified by DB inspection)
- [ ] Password never returned in API responses (masked or omitted)

**AC-6: API Endpoint Functionality**
- [ ] GET /cameras returns list of all cameras with accurate status
- [ ] POST /cameras creates new camera and returns 201 status
- [ ] PUT /cameras/{id} updates camera and reflects changes immediately
- [ ] DELETE /cameras/{id} removes camera and returns 200 status
- [ ] POST /cameras/{id}/test validates connection without saving to DB
- [ ] All endpoints return proper HTTP status codes (200, 201, 400, 404, 500)
- [ ] Error responses include clear "detail" message explaining what went wrong
- [ ] API responses match documented schemas (validated with OpenAPI spec)

**AC-7: Performance Requirements**
- [ ] Frame capture latency <100ms per frame (measured with DEBUG logging)
- [ ] Test connection responds within 5 seconds (p95)
- [ ] Camera CRUD API endpoints respond within 200ms (p95)
- [ ] Memory usage per camera thread <50MB (measured with memory profiler)
- [ ] System handles 1 camera running 24/7 without memory leaks

## Traceability Mapping

| AC # | Spec Section | Components | Test Approach |
|------|--------------|------------|---------------|
| AC-1 | Detailed Design → Services | `CameraService._capture_loop()`, OpenCV `VideoCapture` | Unit test with simulated RTSP streams, integration test with real IP camera (3 brands) |
| AC-2 | Workflows → Reconnection Logic | `CameraService._handle_disconnect()`, WebSocket manager | Integration test: Kill camera stream mid-capture, verify reconnection within 30s |
| AC-3 | Services → CameraService (USB) | `CameraService.start_camera()` with device_index | Manual test on Linux/Mac with USB webcam |
| AC-4 | APIs → POST /cameras, UI Components | `CameraForm.tsx`, `useCameras` hook | E2E test: Fill form, test connection, save, verify in list |
| AC-5 | Data Models → Camera model | SQLAlchemy `Camera.encrypt_password()`, database layer | Unit test: Create camera, query DB, verify password encrypted |
| AC-6 | APIs → All camera endpoints | `app/api/v1/cameras.py` route handlers | API integration tests with pytest + TestClient |
| AC-7 | Non-Functional → Performance | All camera service methods | Load test with realistic camera streams, measure latency/memory |

## Risks, Assumptions, Open Questions

**Risks:**

**R-1: Camera Compatibility (HIGH)**
- **Description:** OpenCV may not support all RTSP camera implementations
- **Impact:** Users unable to connect their specific camera brand
- **Mitigation:** 
  - Test with 3+ different camera brands during development
  - Document tested/compatible cameras in README
  - Provide troubleshooting guide for common connection issues
- **Contingency:** Add manual RTSP stream URL override for advanced users

**R-2: USB Camera Permissions (MEDIUM)**
- **Description:** Linux systems may require sudo for camera access
- **Impact:** App fails to capture from USB camera on some systems
- **Mitigation:**
  - Document udev rules for camera permissions
  - Add clear error message if permission denied
  - Recommend running with appropriate user group (video)
- **Contingency:** Fallback to RTSP-only mode if USB not accessible

**R-3: Reconnection Failures (MEDIUM)**
- **Description:** Some cameras may require power cycle, not just reconnect
- **Impact:** Infinite failed reconnection attempts, log spam
- **Mitigation:**
  - Cap reconnection attempts to 20 before requiring manual intervention
  - Exponential backoff to reduce log noise
  - Alert user after 10 failed attempts
- **Contingency:** Admin dashboard to manually trigger reconnection

**Assumptions:**

**A-1:** RTSP is the standard protocol for IP cameras (verified by market research)
**A-2:** Users have network connectivity between app and camera (local network)
**A-3:** Camera streams use common codecs (H.264, H.265, MJPEG) - 95% market coverage
**A-4:** Single camera sufficient for MVP (multi-camera deferred to Phase 2)
**A-5:** USB camera latency acceptable for motion detection (tested: <50ms)

**Open Questions:**

**Q-1:** Should we support ONVIF camera discovery?
- **Answer:** No (deferred to Phase 2). Manual URL entry sufficient for MVP.
- **Rationale:** ONVIF adds complexity, most users know their camera IP.

**Q-2:** How do we handle cameras behind firewall/NAT?
- **Answer:** MVP assumes local network access. Port forwarding user's responsibility.
- **Rationale:** VPN/tunneling out of scope for MVP security model.

**Q-3:** Should we store camera credentials in environment variables instead of DB?
- **Answer:** No. DB storage required for multi-camera future. Encrypted at rest.
- **Rationale:** Env vars don't scale to multiple cameras. Fernet encryption secure enough for MVP.

**Q-4:** Do we need to support audio from camera streams?
- **Answer:** No (out of scope). Video only for MVP.
- **Rationale:** Audio processing adds complexity, not required for visual AI analysis.

## Test Strategy Summary

**Unit Tests (pytest):**

**Camera Service:**
- `test_start_camera_rtsp()` - Verify RTSP connection with mock VideoCapture
- `test_start_camera_usb()` - Verify USB camera with device index
- `test_capture_frame()` - Verify frame captured at correct FPS
- `test_reconnection_logic()` - Simulate disconnect, verify reconnect attempt
- `test_stop_camera()` - Verify thread cleanup and resource release
- `test_password_encryption()` - Verify passwords encrypted/decrypted correctly

**Camera API:**
- `test_create_camera_valid()` - POST with valid data returns 201
- `test_create_camera_invalid_url()` - POST with bad RTSP URL returns 400
- `test_update_camera()` - PUT updates configuration
- `test_delete_camera()` - DELETE removes camera and cascades
- `test_test_connection_success()` - Test endpoint with valid camera
- `test_test_connection_failure()` - Test endpoint with invalid credentials

**Frontend Unit Tests (Jest + React Testing Library):**
- `CameraForm` renders with all fields
- `CameraForm` validates RTSP URL format
- `CameraForm` shows error for missing required fields
- `useCameras` hook fetches camera list
- `CameraPreview` shows connection status indicator

**Integration Tests:**

**Backend:**
- End-to-end camera lifecycle: Create → Start → Capture → Stop → Delete
- Reconnection flow with simulated network interruption
- Database persistence across service restarts
- API endpoint integration with real database

**Frontend:**
- E2E test: Add camera flow (form → test → save → list)
- E2E test: Edit camera (load form → change → save)
- E2E test: Delete camera (click delete → confirm → verify removed)

**Manual Testing:**

**Camera Compatibility:**
- Test with 3+ different camera brands (e.g., Hikvision, Dahua, Amcrest)
- Test USB webcam on Linux and macOS
- Test RTSP with basic auth and digest auth
- Test different video codecs (H.264, H.265, MJPEG)

**Network Conditions:**
- Disconnect camera mid-stream, verify reconnection
- Slow network (add latency), verify timeout handling
- Camera unreachable (wrong IP), verify error message
- Camera requires auth (wrong password), verify error message

**Performance:**
- 24-hour soak test with camera running continuously
- Memory usage profiling over time (check for leaks)
- Frame capture latency measurement at 1, 5, 15, 30 FPS
- Multiple API requests in parallel (load test)

**Test Coverage Targets:**
- Backend: 80% code coverage (critical paths 100%)
- Frontend: 70% code coverage (focus on user flows)
- API endpoints: 100% (all status codes tested)

**Test Automation:**
- CI/CD pipeline runs all unit tests on commit
- Integration tests run nightly (require camera hardware)
- E2E tests run pre-release (manual trigger)

---

**Epic F1 Status:** Draft - Ready for Review  
**Dependencies:** None (foundational epic)  
**Blocked By:** None  
**Blocks:** Epic F2 (Motion Detection) - requires frame capture infrastructure  
**Estimated Effort:** 3-4 developer-days (backend) + 2-3 developer-days (frontend)  
**Next Action:** Break into implementable stories (F1.1, F1.2, F1.3)
