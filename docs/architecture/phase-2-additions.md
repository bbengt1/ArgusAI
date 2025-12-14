# Phase 2 Additions

This section documents the architectural additions for Phase 2, which adds native UniFi Protect integration and xAI Grok as an additional AI provider.

## Phase 2 Executive Summary

Phase 2 transforms the system from "works with any camera via RTSP" to "works *optimally* with your camera system" by adding native UniFi Protect integration. This unlocks:

- **Real-time WebSocket events** - No polling delays, instant detection
- **Camera auto-discovery** - No manual RTSP URL configuration
- **Smart detection filtering** - Person/Vehicle/Package/Animal pre-classification from Protect
- **Doorbell integration** - Ring events with visitor AI analysis
- **Multi-camera correlation** - Link related events across cameras

Additionally, xAI Grok joins the AI provider roster, giving users more options for event descriptions.

**Key Architectural Principles (Phase 2):**
1. **Native over Generic** - Purpose-built integrations for camera systems
2. **Coexistence** - UniFi Protect and RTSP/USB cameras work side-by-side
3. **Real-time First** - WebSocket-driven event flow
4. **Unified Pipeline** - All camera sources feed the same event system

---

## Phase 2 Technology Stack Additions

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **UniFi Protect Client** | uiprotect | 4.x+ | Unofficial Python library for Protect API |
| **xAI Grok Client** | openai (OpenAI-compatible) | 1.x+ | xAI uses OpenAI-compatible API at api.x.ai |
| **WebSocket Client** | websockets | 12.x+ | Async WebSocket support for Protect |

**New Dependencies (backend/requirements.txt):**
```bash
# Phase 2: UniFi Protect
uiprotect>=4.0.0

# Phase 2: xAI Grok (uses OpenAI-compatible API)
# No new package needed - uses existing 'openai' package with custom base_url
# openai>=1.0.0  (already installed for GPT-4o support)

# WebSocket (if not already included)
websockets>=12.0
```

---

## Phase 2 Project Structure Additions

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── protect.py              # NEW: UniFi Protect controller endpoints
│   │   └── ...
│   ├── models/
│   │   ├── protect_controller.py   # NEW: Protect controller model
│   │   └── ...
│   ├── schemas/
│   │   ├── protect.py              # NEW: Protect request/response schemas
│   │   └── ...
│   ├── services/
│   │   ├── protect_service.py      # NEW: Protect connection, WebSocket, events
│   │   ├── protect_event_handler.py # NEW: Process Protect events
│   │   ├── correlation_service.py  # NEW: Multi-camera event correlation
│   │   └── ai_service.py           # MODIFIED: Add xAI Grok provider
│   └── utils/
│       └── encryption.py           # MODIFIED: Encrypt Protect credentials
└── ...

frontend/
├── app/
│   └── settings/
│       └── page.tsx                # MODIFIED: Add UniFi Protect section
├── components/
│   ├── protect/                    # NEW: UniFi Protect components
│   │   ├── ControllerForm.tsx      # Add/edit controller connection
│   │   ├── ConnectionStatus.tsx    # Controller connection indicator
│   │   ├── DiscoveredCameraList.tsx # Auto-discovered cameras
│   │   ├── DiscoveredCameraCard.tsx # Single discovered camera
│   │   └── EventTypeFilter.tsx     # Smart detection filter selector
│   └── events/
│       ├── SourceTypeBadge.tsx     # NEW: Show camera source (Protect/RTSP/USB)
│       ├── SmartDetectionBadge.tsx # NEW: Show Protect detection type
│       └── CorrelationIndicator.tsx # NEW: Show correlated events
└── ...
```

---

## Phase 2 Database Schema Additions

**protect_controllers** table (NEW):
```sql
CREATE TABLE protect_controllers (
    id TEXT PRIMARY KEY,                    -- UUID
    name TEXT NOT NULL,                     -- User-friendly name (e.g., "Home UDM Pro")
    host TEXT NOT NULL,                     -- IP address or hostname
    port INTEGER DEFAULT 443,               -- HTTPS port (usually 443)
    username TEXT NOT NULL,                 -- Protect username
    password TEXT NOT NULL,                 -- Encrypted password (Fernet)
    verify_ssl BOOLEAN DEFAULT FALSE,       -- SSL certificate verification
    is_connected BOOLEAN DEFAULT FALSE,     -- Current connection status
    last_connected_at TIMESTAMP,            -- Last successful connection
    last_error TEXT,                        -- Last connection error message
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**cameras** table (EXTENDED):
```sql
-- Add new columns to existing cameras table
ALTER TABLE cameras ADD COLUMN source_type TEXT DEFAULT 'rtsp';  -- 'rtsp', 'usb', 'protect'
ALTER TABLE cameras ADD COLUMN protect_controller_id TEXT REFERENCES protect_controllers(id);
ALTER TABLE cameras ADD COLUMN protect_camera_id TEXT;           -- Native Protect camera ID
ALTER TABLE cameras ADD COLUMN protect_camera_type TEXT;         -- 'camera', 'doorbell'
ALTER TABLE cameras ADD COLUMN smart_detection_types TEXT;       -- JSON array: ["person", "vehicle", "package", "animal"]
ALTER TABLE cameras ADD COLUMN is_doorbell BOOLEAN DEFAULT FALSE;

-- Index for Protect camera lookups
CREATE INDEX idx_cameras_protect_camera_id ON cameras(protect_camera_id);
CREATE INDEX idx_cameras_source_type ON cameras(source_type);
```

**events** table (EXTENDED):
```sql
-- Add new columns to existing events table
ALTER TABLE events ADD COLUMN source_type TEXT DEFAULT 'rtsp';   -- 'rtsp', 'usb', 'protect'
ALTER TABLE events ADD COLUMN protect_event_id TEXT;             -- Native Protect event ID
ALTER TABLE events ADD COLUMN smart_detection_type TEXT;         -- 'person', 'vehicle', 'package', 'animal', 'motion'
ALTER TABLE events ADD COLUMN is_doorbell_ring BOOLEAN DEFAULT FALSE;
ALTER TABLE events ADD COLUMN correlated_event_ids TEXT;         -- JSON array of related event IDs
ALTER TABLE events ADD COLUMN correlation_group_id TEXT;         -- UUID for event groups

-- Index for correlation queries
CREATE INDEX idx_events_correlation_group ON events(correlation_group_id);
CREATE INDEX idx_events_protect_event_id ON events(protect_event_id);
```

---

## Phase 2 API Contracts

### UniFi Protect Controller Endpoints

**Base URL:** `http://localhost:8000/api/v1/protect`

**POST /protect/controllers**
- Add UniFi Protect controller
- Body:
```json
{
  "name": "Home UDM Pro",
  "host": "192.168.1.1",
  "port": 443,
  "username": "admin",
  "password": "secretpassword",
  "verify_ssl": false
}
```
- Response: `{ data: ProtectController, meta: {...} }`
- **Side effect:** Validates connection before saving

**GET /protect/controllers**
- List all Protect controllers
- Response: `{ data: ProtectController[], meta: {...} }`

**GET /protect/controllers/{id}**
- Get controller with connection status
- Response: `{ data: ProtectController, meta: {...} }`

**PUT /protect/controllers/{id}**
- Update controller settings
- Body: Partial `{ name?, host?, port?, username?, password?, verify_ssl? }`
- Response: `{ data: ProtectController, meta: {...} }`

**DELETE /protect/controllers/{id}**
- Remove controller (disconnects WebSocket, removes discovered cameras)
- Response: `{ data: { deleted: true }, meta: {...} }`

**POST /protect/controllers/{id}/test**
- Test controller connection
- Response: `{ data: { success: bool, message: string, firmware_version?: string }, meta: {...} }`

**POST /protect/controllers/{id}/connect**
- Establish WebSocket connection
- Response: `{ data: { connected: true }, meta: {...} }`

**POST /protect/controllers/{id}/disconnect**
- Disconnect WebSocket
- Response: `{ data: { disconnected: true }, meta: {...} }`

**GET /protect/controllers/{id}/cameras**
- Get discovered cameras from controller
- Response:
```json
{
  "data": [
    {
      "protect_camera_id": "abc123",
      "name": "Front Door",
      "type": "doorbell",
      "model": "G4 Doorbell Pro",
      "is_enabled_for_ai": false,
      "smart_detection_types": ["person", "vehicle", "package"]
    }
  ],
  "meta": {...}
}
```

**POST /protect/controllers/{id}/cameras/{protect_camera_id}/enable**
- Enable camera for AI analysis
- Body: `{ smart_detection_types: ["person", "vehicle"] }`
- Response: `{ data: Camera, meta: {...} }`
- **Side effect:** Creates camera record in cameras table

**POST /protect/controllers/{id}/cameras/{protect_camera_id}/disable**
- Disable camera for AI analysis
- Response: `{ data: { disabled: true }, meta: {...} }`

### xAI Grok Provider

**Settings key:** `ai_api_key_grok`

Uses existing `/api/v1/settings/{key}` endpoints for configuration.

**AI Provider order (configurable):**
```json
{
  "ai_provider_order": ["openai", "grok", "gemini", "anthropic"]
}
```

---

## Phase 2 Service Architecture

### ProtectService (NEW)

**File:** `backend/app/services/protect_service.py`

**Responsibilities:**
- Manage connection to UniFi Protect controller
- Maintain WebSocket connection with auto-reconnect
- Discover cameras from controller
- Receive real-time events via WebSocket
- Fetch snapshots on event trigger

**Key Methods:**
```python
class ProtectService:
    """Manages UniFi Protect controller connections and events."""

    async def connect(self, controller: ProtectController) -> bool:
        """Establish authenticated WebSocket connection to Protect controller."""

    async def disconnect(self, controller_id: str) -> None:
        """Gracefully disconnect from controller."""

    async def discover_cameras(self, controller_id: str) -> List[ProtectCamera]:
        """Fetch all cameras from connected controller."""

    async def get_snapshot(self, controller_id: str, camera_id: str) -> bytes:
        """Fetch current snapshot from Protect camera."""

    async def _websocket_listener(self, controller: ProtectController) -> None:
        """Background task: Listen for real-time events from Protect."""

    async def _handle_event(self, event: dict) -> None:
        """Process incoming Protect event, filter, and queue for AI analysis."""

    async def _reconnect_with_backoff(self, controller: ProtectController) -> None:
        """Reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s)."""
```

**WebSocket Event Flow:**
```
UniFi Protect Controller
         │
         │ WebSocket (wss://)
         ▼
   ProtectService._websocket_listener()
         │
         │ Filter by enabled cameras + smart detection types
         ▼
   ProtectEventHandler.process_event()
         │
         │ Fetch snapshot via Protect API
         │
         ▼
   EventProcessor (existing pipeline)
         │
         │ AI description, store, alert evaluation
         ▼
   WebSocket broadcast to frontend
```

### ProtectEventHandler (NEW)

**File:** `backend/app/services/protect_event_handler.py`

**Responsibilities:**
- Convert Protect events to internal event format
- Apply smart detection filtering
- Handle doorbell ring events differently
- Queue events for AI analysis

**Key Methods:**
```python
class ProtectEventHandler:
    """Converts UniFi Protect events into system events."""

    async def process_event(self, protect_event: dict, camera: Camera) -> Optional[Event]:
        """Convert Protect event to internal event, apply filters."""

    async def process_doorbell_ring(self, protect_event: dict, camera: Camera) -> Event:
        """Handle doorbell ring event (fetch snapshot, create event)."""

    def should_process_event(self, protect_event: dict, camera: Camera) -> bool:
        """Check if event passes camera's smart detection filters."""
```

### CorrelationService (NEW)

**File:** `backend/app/services/correlation_service.py`

**Responsibilities:**
- Detect when multiple cameras capture the same real-world event
- Group correlated events with a shared correlation_group_id
- Time-window based correlation (configurable, default 10 seconds)

**Key Methods:**
```python
class CorrelationService:
    """Correlates events across multiple cameras."""

    async def check_correlation(self, event: Event) -> Optional[str]:
        """Check if event correlates with recent events, return group_id if so."""

    async def get_correlated_events(self, event_id: str) -> List[Event]:
        """Get all events in the same correlation group."""

    def _is_correlated(self, event1: Event, event2: Event) -> bool:
        """Determine if two events are likely the same real-world event."""
```

**Correlation Logic:**
- Events within `CORRELATION_WINDOW` seconds (default 10s)
- From different cameras
- Same or similar smart detection type
- Optional: Same Protect controller (stricter correlation)

### AIService Extensions

**File:** `backend/app/services/ai_service.py` (MODIFIED)

**Add xAI Grok provider:**
```python
from openai import AsyncOpenAI

class AIService:
    PROVIDERS = ['openai', 'grok', 'gemini', 'anthropic']  # Updated

    def __init__(self):
        # ... existing initialization ...

        # xAI Grok uses OpenAI-compatible API with custom base_url
        self.grok_client = AsyncOpenAI(
            base_url="https://api.x.ai/v1",
            api_key=self._get_decrypted_key("ai_api_key_grok")
        )

    async def _call_grok(self, image_base64: str, prompt: str) -> str:
        """Call xAI Grok vision API for image description.

        Note: xAI provides an OpenAI-compatible API at api.x.ai/v1
        Uses the existing openai package with custom base_url.
        """
        response = await self.grok_client.chat.completions.create(
            model="grok-2-vision-1212",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        return response.choices[0].message.content
```

**Key Implementation Notes:**
- xAI Grok uses OpenAI-compatible API format
- No additional SDK required - reuses existing `openai` package
- Base URL: `https://api.x.ai/v1`
- Model: `grok-2-vision-1212` (vision-capable)

---

## Phase 2 WebSocket Protocol Additions

**New Message Types (Server → Client):**

```json
{
  "type": "PROTECT_CONNECTION_STATUS",
  "data": {
    "controller_id": "uuid",
    "status": "connected" | "disconnected" | "reconnecting",
    "error": null | "Connection refused"
  },
  "timestamp": "2025-11-30T10:30:00Z"
}
```

```json
{
  "type": "DOORBELL_RING",
  "data": {
    "event_id": "uuid",
    "camera_id": "uuid",
    "camera_name": "Front Door",
    "thumbnail_url": "/api/v1/events/uuid/thumbnail"
  },
  "timestamp": "2025-11-30T10:30:00Z"
}
```

```json
{
  "type": "EVENT_CREATED",
  "data": {
    "event": {
      "id": "uuid",
      "source_type": "protect",
      "smart_detection_type": "person",
      "correlated_event_ids": ["uuid2", "uuid3"],
      "...": "..."
    }
  },
  "timestamp": "2025-11-30T10:30:00Z"
}
```

---

## Phase 2 Security Considerations

**Credential Storage:**
- UniFi Protect passwords encrypted with Fernet (same as RTSP passwords)
- xAI Grok API key encrypted with Fernet (same as other AI keys)
- Never log credentials in plain text

**Network Security:**
- WebSocket connection uses WSS (TLS) when connecting to Protect
- `verify_ssl` option allows self-signed certificates (common in home setups)
- API keys transmitted only to respective provider APIs

**Authentication:**
- Protect API endpoints require same auth as other endpoints
- No credential caching in browser (server-side only)

---

## Phase 2 Performance Considerations

**WebSocket Connection:**
- Single persistent connection per Protect controller
- Automatic reconnection with exponential backoff
- Event buffering during brief disconnects (configurable buffer size)

**Snapshot Retrieval:**
- Target: < 1 second from Protect API
- Concurrent snapshot + AI analysis to minimize latency
- Cache controller authentication token (refresh on 401)

**Correlation Processing:**
- In-memory recent event buffer (last 60 seconds)
- O(n) scan for correlation candidates (acceptable for home-scale cameras)
- Async correlation check (doesn't block event storage)

**Scaling Limits (Phase 2):**
- Single Protect controller (multi-controller in future)
- Up to ~20 cameras per controller (Protect limit)
- ~100 events/day typical home usage

---

## Phase 2 Epic to Architecture Mapping

| Epic | Architecture Components | Key Files |
|------|------------------------|-----------|
| **Epic 1: Controller Integration** | ProtectService, controller model, WebSocket | `protect_service.py`, `protect.py` API, `ControllerForm.tsx` |
| **Epic 2: Camera Discovery** | ProtectService, camera model extensions | `protect_service.py`, `DiscoveredCameraList.tsx` |
| **Epic 3: Real-Time Events** | ProtectEventHandler, event pipeline | `protect_event_handler.py`, `event_processor.py` |
| **Epic 4: Doorbell & Correlation** | ProtectEventHandler, CorrelationService | `correlation_service.py`, `DoorbellEventCard.tsx` |
| **Epic 5: xAI Grok** | AIService extension | `ai_service.py`, Settings page |
| **Epic 6: Coexistence** | Event pipeline, unified frontend | `EventTimeline.tsx`, `SourceTypeBadge.tsx` |

---

## Phase 2 Architecture Decision Records

### ADR-008: Native Integration over RTSP Polling

**Decision:** Build native UniFi Protect integration using `uiprotect` library instead of relying solely on RTSP streams.

**Rationale:**
- **Real-time:** WebSocket events arrive instantly vs 1-5 second RTSP polling delay
- **Smart Detection:** Leverage Protect's built-in person/vehicle/package detection
- **Auto-discovery:** No manual RTSP URL configuration needed
- **Reliability:** Native API more stable than RTSP stream management

**Trade-offs:**
- `uiprotect` is unofficial/community-maintained
- Firmware updates may break compatibility (mitigated by active community)
- Adds Protect-specific code path alongside generic RTSP

**Status:** Accepted (core Phase 2 feature)

---

### ADR-009: Single Controller for Phase 2

**Decision:** Support only one UniFi Protect controller per system in Phase 2.

**Rationale:**
- **Simplicity:** Single controller covers 95%+ of home users
- **Complexity:** Multi-controller adds WebSocket management complexity
- **MVP Scope:** Get single-controller working well before expanding

**Trade-offs:**
- Users with multiple sites/controllers must choose one
- Multi-controller support deferred to Phase 3

**Status:** Accepted (revisit in Phase 3)

---

### ADR-010: Time-Window Based Correlation

**Decision:** Use time-based correlation (10-second window) for multi-camera event grouping.

**Rationale:**
- **Simple:** Easy to understand and implement
- **Effective:** Most multi-camera captures happen within seconds
- **Low false positives:** Conservative window reduces incorrect correlations

**Trade-offs:**
- May miss slow-moving subjects crossing camera boundaries
- No spatial/object-based correlation (could add in future)
- Time sync assumes cameras/system have synchronized clocks

**Status:** Accepted (simple first approach)

---

### ADR-011: xAI Grok as Additional Provider

**Decision:** Add xAI Grok to the AI provider fallback chain rather than replacing existing providers.

**Rationale:**
- **Choice:** Users can select preferred provider
- **Reliability:** More fallback options increase uptime
- **Comparison:** Users can compare description quality across providers

**Trade-offs:**
- More SDK dependencies
- More API keys to manage
- Testing complexity increases

**Status:** Accepted (aligns with multi-provider strategy)

---

## Phase 2 Integration Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Event Sources                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  UniFi Protect  │    │  RTSP Camera    │    │  USB Camera     │        │
│  │   Controller    │    │   (existing)    │    │   (existing)    │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                  │
│     WebSocket               OpenCV               OpenCV                    │
│     (real-time)             (polling)            (polling)                 │
│           │                      │                      │                  │
│  ┌────────▼────────┐    ┌────────▼────────────────────▼────────┐          │
│  │ ProtectService  │    │        CameraService (existing)       │          │
│  │  - WebSocket    │    │        - RTSP capture                 │          │
│  │  - Snapshots    │    │        - USB capture                  │          │
│  │  - Discovery    │    │        - Motion detection              │          │
│  └────────┬────────┘    └────────────────────┬─────────────────┘          │
│           │                                   │                            │
│  ┌────────▼────────┐                          │                            │
│  │ProtectEventHdlr │                          │                            │
│  │ - Filter events │                          │                            │
│  │ - Doorbell ring │                          │                            │
│  └────────┬────────┘                          │                            │
│           │                                   │                            │
└───────────┼───────────────────────────────────┼────────────────────────────┘
            │                                   │
            └─────────────┬─────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Unified Event Pipeline                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                     EventProcessor (existing)                      │      │
│  │   - Queue events from all sources                                 │      │
│  │   - Call AIService for descriptions                               │      │
│  │   - Store events in database                                      │      │
│  │   - Trigger alert evaluation                                      │      │
│  └────────────────────────────┬─────────────────────────────────────┘      │
│                               │                                             │
│  ┌────────────────────────────▼─────────────────────────────────────┐      │
│  │                   CorrelationService (NEW)                        │      │
│  │   - Check for multi-camera event correlation                      │      │
│  │   - Group related events                                          │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI Provider Chain                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │  OpenAI  │──▶│   Grok   │──▶│  Gemini  │──▶│  Claude  │                │
│  │ GPT-4o   │   │  (NEW)   │   │  Flash   │   │  Haiku   │                │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘                │
│        │              │              │              │                       │
│        └──────────────┴──────────────┴──────────────┘                       │
│                            │                                                │
│                     Fallback on failure                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frontend (Unified View)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                    EventTimeline (enhanced)                       │      │
│  │   - All events from all camera sources                           │      │
│  │   - Source type badges (Protect/RTSP/USB)                        │      │
│  │   - Smart detection badges (Person/Vehicle/Package)              │      │
│  │   - Correlated event indicators                                  │      │
│  │   - Doorbell ring notifications                                  │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                    Settings Page (enhanced)                       │      │
│  │   - UniFi Protect section                                        │      │
│  │     - Controller connection form                                 │      │
│  │     - Discovered cameras list                                    │      │
│  │     - Event type filters per camera                              │      │
│  │   - AI Providers section                                         │      │
│  │     - xAI Grok configuration (NEW)                               │      │
│  │     - Provider order configuration                               │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 2 Validation Checklist

- ✅ All PRD Phase 2 functional requirements (FR1-FR36) have architectural support
- ✅ All PRD Phase 2 non-functional requirements (NFR1-NFR16) addressed
- ✅ UniFi Protect integration architecture defined (service, WebSocket, API)
- ✅ Database schema extensions for Protect controllers and cameras
- ✅ xAI Grok provider integration path defined
- ✅ Multi-camera correlation service designed
- ✅ Coexistence architecture ensures RTSP/USB cameras unaffected
- ✅ WebSocket protocol extended for new event types
- ✅ Security considerations documented for credential storage
- ✅ Performance considerations documented for real-time events
- ✅ Phase 2 ADRs documented with rationale

---

**Phase 2 Architecture Update:**
- **Updated by:** BMad Architect Agent
- **Date:** 2025-11-30
- **PRD Reference:** `docs/PRD-phase2.md`
- **UX Reference:** `docs/ux-design-specification.md` (Section 10)

---
