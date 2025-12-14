# API Contracts

## REST API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

### Cameras

**GET /cameras**
- List all cameras
- Query params: `is_enabled` (bool filter)
- Response: `{ data: Camera[], meta: {...} }`

**POST /cameras**
- Create new camera
- Body: `{ name, type, rtsp_url?, username?, password?, device_index?, frame_rate? }`
- Response: `{ data: Camera, meta: {...} }`

**GET /cameras/{id}**
- Get camera by ID
- Response: `{ data: Camera, meta: {...} }`

**PUT /cameras/{id}**
- Update camera
- Body: Partial `{ name?, is_enabled?, ...}`
- Response: `{ data: Camera, meta: {...} }`

**DELETE /cameras/{id}**
- Delete camera (and cascade delete events)
- Response: `{ data: { deleted: true }, meta: {...} }`

**POST /cameras/{id}/test**
- Test camera connection
- Response: `{ data: { success: bool, message: string, thumbnail?: string }, meta: {...} }`

**POST /cameras/{id}/analyze**
- Manual analysis trigger
- Response: `{ data: { event_id: string, message: string }, meta: {...} }`

### Events

**GET /events**
- List events with pagination
- Query params:
  - `start_date` (ISO string)
  - `end_date` (ISO string)
  - `camera_id` (UUID)
  - `object_type` (string, can repeat for multiple)
  - `search` (full-text search)
  - `page` (default 1)
  - `per_page` (default 50, max 200)
- Response: `{ data: Event[], meta: { total, page, per_page, pages } }`

**GET /events/{id}**
- Get single event
- Response: `{ data: Event, meta: {...} }`

**GET /events/{id}/thumbnail**
- Get event thumbnail image
- Response: JPEG image (Content-Type: image/jpeg)

**DELETE /events/{id}**
- Delete event
- Response: `{ data: { deleted: true }, meta: {...} }`

**GET /events/stats**
- Event statistics
- Query params: `start_date`, `end_date`
- Response: `{ data: { total_events, by_object_type: {...}, by_camera: {...}, by_hour: [...] }, meta: {...} }`

### Alert Rules

**GET /alert-rules**
- List all alert rules
- Response: `{ data: AlertRule[], meta: {...} }`

**POST /alert-rules**
- Create alert rule
- Body: `{ name, is_enabled, conditions, actions, cooldown_minutes }`
- Response: `{ data: AlertRule, meta: {...} }`

**GET /alert-rules/{id}**
- Get alert rule
- Response: `{ data: AlertRule, meta: {...} }`

**PUT /alert-rules/{id}**
- Update alert rule
- Body: Partial rule object
- Response: `{ data: AlertRule, meta: {...} }`

**DELETE /alert-rules/{id}**
- Delete alert rule
- Response: `{ data: { deleted: true }, meta: {...} }`

**POST /alert-rules/{id}/test**
- Test rule against recent events
- Response: `{ data: { matching_events: Event[] }, meta: {...} }`

### Settings

**GET /settings**
- Get all system settings
- Response: `{ data: { [key]: value }, meta: {...} }`

**PUT /settings**
- Update settings (bulk update)
- Body: `{ [key]: value }`
- Response: `{ data: { updated: true }, meta: {...} }`

**GET /settings/{key}**
- Get single setting
- Response: `{ data: { key, value, description }, meta: {...} }`

**PUT /settings/{key}**
- Update single setting
- Body: `{ value }`
- Response: `{ data: { key, value }, meta: {...} }`

### Health

**GET /health**
- System health check (no auth required)
- Response: 
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T10:30:00Z",
  "components": {
    "database": "healthy",
    "cameras": {
      "camera-1": "connected",
      "camera-2": "disconnected"
    },
    "ai_model": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "events_processed_today": 42,
    "queue_size": 0
  }
}
```

### Authentication (Phase 1.5)

**POST /login**
- User login
- Body: `{ username, password }`
- Response: `{ data: { access_token, token_type: "bearer", user: {...} }, meta: {...} }`
- Sets HTTP-only cookie with JWT

**POST /logout**
- User logout
- Response: `{ data: { logged_out: true }, meta: {...} }`
- Clears session cookie

**GET /me**
- Get current user
- Requires: Bearer token or session cookie
- Response: `{ data: User, meta: {...} }`

## WebSocket Protocol

**Connection:** `ws://localhost:8000/ws`

**Authentication (Phase 1.5):**
- Query param: `?token={jwt_token}`
- Or send as first message: `{ "type": "AUTH", "data": { "token": "..." } }`

**Message Format (Server → Client):**
```json
{
  "type": "EVENT_CREATED",
  "data": {
    "event": { /* full Event object */ }
  },
  "timestamp": "2025-11-15T10:30:00Z"
}
```

**Message Types:**
- `EVENT_CREATED`: New event stored
- `ALERT_TRIGGERED`: Alert rule matched and action taken
- `CAMERA_STATUS_CHANGED`: Camera connected/disconnected
- `PROCESSING_STATUS`: Update on long-running operation
- `ERROR`: Server-side error notification

**Client → Server Messages:**
- `PING`: Keep-alive message
- Response: `PONG`

**Connection Management:**
- Auto-reconnect on disconnect (exponential backoff: 1s, 2s, 4s, 8s, max 30s)
- Heartbeat: Client sends PING every 30 seconds
- Server closes connection after 60 seconds without PING

---
