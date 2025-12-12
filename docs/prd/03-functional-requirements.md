# PRD: Functional Requirements

[← Back to PRD Index](./README.md) | [← Previous: Personas & Stories](./02-personas-stories.md) | [Next: Non-Functional Requirements →](./04-non-functional-requirements.md)

---

## Overview

This document details all functional requirements for the ArgusAI MVP, organized by major feature area. Each requirement includes priority, acceptance criteria, and dependencies.

**Priority Levels:**
- **MUST HAVE** - Required for MVP launch, blocking
- **SHOULD HAVE** - Important but can be deferred if needed
- **COULD HAVE** - Nice to have, implement if time permits

---

## F1: Camera Feed Integration

### F1.1: RTSP Camera Support

**Requirement:** System must connect to RTSP camera streams

**Details:**
- Support RTSP over TCP and UDP protocols
- Handle common authentication methods (basic auth, digest auth)
- Reconnect automatically if stream drops (30-second interval retries)
- Configurable frame rate capture (1-30 FPS, default 5 FPS)
- Handle various video codecs (H.264, H.265, MJPEG)
- Timeout handling for unresponsive streams

**Acceptance Criteria:**
- Successfully connect to 3+ different camera brands during testing
- Maintain stable connection for 24+ hours continuous operation
- Reconnect within 30 seconds of disconnection
- Clear error logging for connection failures
- Frame capture at configured rate with <100ms jitter

**Priority:** MUST HAVE  
**Dependencies:** None  
**Related US:** US-9

---

### F1.2: Camera Configuration UI

**Requirement:** Dashboard must provide camera setup interface

**Details:**
- Form input fields:
  - Camera name (text, required)
  - RTSP URL (text, required, format validation)
  - Username (text, optional)
  - Password (password field, optional, encrypted storage)
  - Frame rate (slider, 1-30 FPS)
  - Enabled toggle (boolean)
- Test connection button with real-time feedback
- Preview thumbnail to verify camera angle and quality
- Save/cancel buttons with confirmation
- Edit existing camera configurations
- Delete camera (with confirmation dialog)

**Acceptance Criteria:**
- Non-technical user can add camera in <5 minutes
- Test connection provides clear success/failure feedback
- Error messages actionable ("Check username/password" not "Auth failed 401")
- Preview thumbnail loads within 3 seconds of successful connection
- All configurations persist across system restarts
- URL format validation prevents malformed entries

**Priority:** MUST HAVE  
**Dependencies:** None  
**Related US:** US-9

---

### F1.3: Webcam/USB Camera Support

**Requirement:** System should support local USB cameras for testing

**Details:**
- Auto-detect USB cameras connected to system
- Dropdown selection of available cameras (by name/ID)
- Same configuration interface as RTSP cameras
- Preview functionality for USB cameras
- Handle camera disconnect/reconnect gracefully

**Acceptance Criteria:**
- Detect and list all connected USB cameras
- Successfully capture frames from USB cameras at configured rate
- Works on Linux, macOS (Windows lower priority)
- Same event processing pipeline as RTSP cameras

**Priority:** SHOULD HAVE  
**Dependencies:** F1.1 (shared pipeline)  
**Related US:** None (developer/testing convenience)

---

## F2: Motion Detection

### F2.1: Motion Detection Algorithm

**Requirement:** System must detect motion to trigger AI processing

**Details:**
- Implementation: OpenCV background subtraction or frame differencing
- Configurable sensitivity levels:
  - Low: Major movements only (person walking)
  - Medium: Normal movements (default)
  - High: Subtle movements (waving hand)
- Size threshold: Ignore movements affecting <5% of frame (leaves, shadows)
- Cooldown period between triggers (configurable 30-120 seconds, default 60)
- Region of interest support (motion zones)

**Acceptance Criteria:**
- Detect person entering frame >90% of the time
- False positive rate <20% (non-relevant motion like leaves, shadows)
- Process motion detection with <100ms latency per frame
- Configurable sensitivity changes behavior as expected
- Cooldown prevents event spam (no more than 1 event per cooldown period)

**Priority:** MUST HAVE  
**Dependencies:** F1.1 (camera feed)  
**Related US:** US-1, US-2

---

### F2.2: Motion Detection Zones

**Requirement:** User should define active detection zones

**Details:**
- Interactive zone drawing on camera preview image
- Rectangle selection with mouse drag or touch
- Multiple zones per camera (up to 5)
- Enable/disable zones independently with checkboxes
- Motion outside all zones ignored completely
- Visual overlay showing active zones on preview
- Save zones per camera in configuration

**Acceptance Criteria:**
- UI allows drawing zones with mouse/touch (minimum 50x50px)
- Motion outside defined zones doesn't trigger events
- Zone configurations persist across system restarts
- Visual feedback shows active zones on live preview
- Can delete zones individually

**Priority:** SHOULD HAVE  
**Dependencies:** F2.1, F1.2 (camera preview)  
**Related US:** US-10

---

### F2.3: Detection Schedule

**Requirement:** User can schedule when motion detection is active

**Details:**
- Time-based schedule (e.g., "active 9pm-6am weekdays")
- Day-of-week selection (M-Su checkboxes)
- Multiple schedule rules per camera
- Quick toggle for "home mode" (disabled) vs "away mode" (enabled)
- Schedule rules saved and enforced automatically

**Acceptance Criteria:**
- Motion detection only active during scheduled times
- Schedule persists across system restarts
- Home/away toggle overrides schedule temporarily
- Clear UI shows current active state (scheduled on/off)

**Priority:** COULD HAVE  
**Dependencies:** F2.1  
**Related US:** None (user request)

---

## F3: AI-Powered Description Generation

### F3.1: Natural Language Processing

**Requirement:** System must generate rich natural language descriptions

**Details:**
- Integrate with AI vision model:
  - Primary: OpenAI GPT-4o mini (or Gemini Flash free tier)
  - Description format: WHO/WHAT + WHERE + ACTION + RELEVANT DETAILS
  - Example: "Adult male, approximately 30s, brown jacket, carrying Amazon package, approaching front door"
- Include confidence score (0-100%)
- Detect and label objects: person, vehicle, animal, package, unknown
- System prompt optimizes for security/accessibility use cases
- Timeout handling (10 second max)
- Error handling with retry logic (3 attempts)

**Acceptance Criteria:**
- Generate description within 5 seconds of motion trigger (p95)
- Description includes 3+ relevant details per event (person appearance, action, context)
- Confidence score accurately reflects quality (>80% for clear images)
- Object detection identifies person/vehicle/package correctly >90% of time
- Gracefully handles API failures (retry, fallback, error logging)

**Priority:** MUST HAVE  
**Dependencies:** F2.1 (motion trigger)  
**Related US:** US-1, US-2, US-3, US-7

---

### F3.2: Image Capture & Processing

**Requirement:** Capture optimal frame for AI analysis

**Details:**
- Capture strategy: Frame at motion peak (not first/last frame)
- Pre-processing:
  - Resize to optimal dimensions for AI model (e.g., 1024x768)
  - Brightness/contrast adjustment if needed
  - Format conversion (to JPEG or PNG)
- Send to AI model with optimized prompt
- Store thumbnail (max 200KB, resized to 640x480) with event
- Original frame discarded after processing (privacy)

**Acceptance Criteria:**
- Captured frame shows subject clearly (centered in frame, not motion-blurred)
- Image processing adds <1 second to total latency
- Thumbnail stored efficiently (<200KB average)
- Pre-processing improves description quality measurably
- No storage of full-resolution frames (privacy compliance)

**Priority:** MUST HAVE  
**Dependencies:** F2.1 (motion detection), F3.1  
**Related US:** US-1, US-7

---

### F3.3: AI Model Selection & Fallback

**Requirement:** System should support multiple AI model options

**Details:**
- Configurable AI model selection dropdown:
  - OpenAI GPT-4o mini
  - Google Gemini Flash
  - Anthropic Claude 3 Haiku
- API key configuration per model (encrypted storage)
- Primary/fallback model configuration
- Automatic fallback to secondary model if primary fails
- Track API usage and warn when approaching rate limits
- Display current model in system status

**Acceptance Criteria:**
- Switch between models via settings without code changes
- Fallback succeeds when primary model unavailable (3 failed attempts)
- Warning notification when 80% of rate limit reached
- API key test button validates before saving
- Each model produces usable descriptions (tested during development)

**Priority:** SHOULD HAVE  
**Dependencies:** F3.1  
**Related US:** None (system reliability)

---

### F3.4: Description Enhancement Prompt

**Requirement:** AI prompt optimized for security/accessibility use cases

**Details:**
- System prompt instructs AI on output format and detail level
- Prompt template:
  ```
  You are an AI describing video surveillance events for home security and accessibility.
  Describe what you see in this image with these details:
  - WHO: Person appearance (age estimate, gender, clothing colors/style)
  - WHAT: Objects carried (packages, bags, tools, weapons)
  - WHERE: Location in frame (near door, in driveway, etc.)
  - ACTION: What they're doing (walking toward, standing still, reaching for, etc.)
  - VEHICLES: Any vehicles visible (color, type, license if readable)
  
  Be specific and detailed. This description may be the only information available.
  If unsure, state uncertainty. Confidence in details matters for safety decisions.
  ```
- Prompt customizable per use case (security vs accessibility emphasis)
- Include timestamp and camera context in prompt

**Acceptance Criteria:**
- Descriptions consistently follow WHO/WHAT/WHERE/ACTION format
- Relevant details included 90%+ of the time
- Descriptions useful without seeing image (tested by vision-impaired users)
- Prompt customization changes description style appropriately
- Uncertainty stated when AI not confident

**Priority:** MUST HAVE  
**Dependencies:** F3.1  
**Related US:** US-7

---

## F4: Event Storage & Management

### F4.1: Event Data Structure

**Requirement:** Store semantic event records (not video)

**Details:**
- Event schema (database table):
  ```sql
  events (
    id UUID PRIMARY KEY,
    camera_id UUID REFERENCES cameras(id),
    timestamp TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    confidence INTEGER CHECK (confidence >= 0 AND confidence <= 100),
    objects_detected JSON NOT NULL, -- array: ["person", "package"]
    thumbnail_path TEXT, -- file path or base64 data
    alert_triggered BOOLEAN DEFAULT FALSE,
    alert_rule_id UUID REFERENCES alert_rules(id),
    user_feedback TEXT, -- for future learning system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
- Indexes: timestamp, camera_id, objects_detected (GIN index for JSON array)
- SQLite database for MVP (migrate to Postgres in Phase 2)
- Foreign key constraints enforced

**Acceptance Criteria:**
- Events stored reliably with no data loss
- Query performance <100ms for typical date range (1 week of events)
- Database size manageable (<10MB per 1000 events excluding thumbnails)
- Schema versioned with migrations (Alembic)
- Rollback capability for failed migrations

**Priority:** MUST HAVE  
**Dependencies:** F1.1 (camera_id FK)  
**Related US:** US-3

---

### F4.2: Event Retrieval API

**Requirement:** Backend API for querying events

**Details:**
- RESTful endpoints:
  ```
  GET /api/events
    Query params: start_date, end_date, camera_id, object_type, limit, offset, search
    Response: { events: [...], total: N, page: M, per_page: P }
  
  GET /api/events/:id
    Response: { event: {...} }
  
  GET /api/events/stats
    Response: { total_events, by_object_type: {...}, by_camera: {...}, by_hour: [...] }
  
  DELETE /api/events/:id
    Requires confirmation, soft delete
  ```
- Query parameter validation
- Pagination (default 50 per page, max 200)
- Full-text search on description field
- Filter by multiple object types (OR logic)
- Sort by timestamp (desc default) or relevance (search)

**Acceptance Criteria:**
- All endpoints return valid JSON
- Pagination works correctly for large result sets (1000+ events)
- Filtering works correctly for all parameters
- Search finds relevant events (fuzzy matching)
- API errors return proper status codes (400, 404, 500) with messages

**Priority:** MUST HAVE  
**Dependencies:** F4.1  
**Related US:** US-3, US-6

---

### F4.3: Data Retention Policy

**Requirement:** User can configure how long events are stored

**Details:**
- Retention period options:
  - 7 days
  - 30 days
  - 90 days
  - 1 year
  - Forever (manual deletion only)
- Automatic cleanup job runs daily at 2am
- Export events before deletion (optional, CSV/JSON)
- Warning notification 24 hours before auto-deletion
- Manual "delete all before date" option

**Acceptance Criteria:**
- Events older than retention period deleted automatically
- User notified 24 hours before first auto-deletion batch
- Export to CSV/JSON works and includes all event data
- Manual deletion requires confirmation
- Deletion is permanent (not soft delete for old events)

**Priority:** SHOULD HAVE  
**Dependencies:** F4.1, F4.2  
**Related US:** None (privacy/storage management)

---

### F4.4: Event Search

**Requirement:** Search events by description keywords

**Details:**
- Full-text search on description field (SQLite FTS5)
- Search features:
  - Partial word matching ("deliv" matches "delivery")
  - Multiple keywords (AND logic by default)
  - Quote for exact phrases ("brown jacket")
  - NOT operator to exclude terms
- Highlight search terms in results
- Sort by relevance score or timestamp
- Search combined with filters (date, camera, object type)

**Acceptance Criteria:**
- Search returns relevant results in <500ms
- Finds events even with partial keywords
- Results sortable by relevance or timestamp
- Highlighting shows matched terms in context
- Search combined with filters works correctly

**Priority:** SHOULD HAVE  
**Dependencies:** F4.1, F4.2  
**Related US:** US-3

---

## F5: Alert Rule Engine

### F5.1: Basic Alert Rules

**Requirement:** User can define when to receive alerts

**Details:**
- Rule data structure:
  ```json
  {
    "id": "uuid",
    "name": "Package Delivery Alert",
    "enabled": true,
    "conditions": {
      "object_types": ["package", "person"], // OR logic
      "time_range": {"start": "09:00", "end": "18:00"}, // optional
      "days_of_week": [1,2,3,4,5], // Mon-Fri, optional
      "cameras": ["camera-uuid"], // specific cameras or all
      "confidence_min": 70 // minimum confidence threshold
    },
    "actions": {
      "dashboard_notification": true,
      "webhook_url": "https://...", // optional
      "webhook_headers": {...} // optional
    },
    "cooldown_minutes": 30
  }
  ```
- Rule evaluation happens immediately after event storage
- Multiple rules can trigger from single event
- Rules evaluated in order of creation

**Acceptance Criteria:**
- Rules evaluate within 1 second of event storage
- Multiple rules trigger correctly from single event
- Rule condition logic works correctly (object, time, camera filters)
- Rule changes take effect immediately (no restart needed)
- Cooldown prevents spam (only 1 alert per rule per cooldown period)

**Priority:** MUST HAVE  
**Dependencies:** F4.1 (events)  
**Related US:** US-1, US-2, US-4

---

### F5.2: Alert Rule Configuration UI

**Requirement:** Dashboard interface for managing alert rules

**Details:**
- Rule list page:
  - Table showing: Name, Enabled toggle, Conditions summary, Last triggered
  - Edit/delete buttons per row
  - "+ Create Rule" prominent button
- Create/Edit modal:
  - Rule name input
  - Enabled toggle switch
  - Conditions builder:
    - Object type multi-select (person, vehicle, package, animal)
    - Time range picker (start/end hours)
    - Day of week checkboxes
    - Camera multi-select (or "all cameras")
    - Confidence threshold slider (0-100%)
  - Actions section:
    - Dashboard notification checkbox (default enabled)
    - Webhook URL input (optional)
    - Webhook custom headers (key-value pairs)
  - Cooldown period slider (0-120 minutes)
  - Test rule button (shows matching recent events)
  - Save/cancel buttons

**Acceptance Criteria:**
- Non-technical user can create rule in <2 minutes
- Test feature shows which past 10 events would match rule
- Clear validation messages for invalid configs (e.g., empty conditions)
- Rule list shows accurate "last triggered" timestamps
- Bulk actions: Enable/disable multiple rules, delete multiple rules

**Priority:** MUST HAVE  
**Dependencies:** F5.1  
**Related US:** US-5, US-9

---

### F5.3: Advanced Rule Logic

**Requirement:** Support complex rule conditions

**Details:**
- Boolean logic:
  - AND conditions (all must match)
  - OR conditions (any must match)
  - NOT conditions (exclude matching)
- Compound conditions:
  - "Person AND package" (both must be detected)
  - "Vehicle AND NOT daytime" (vehicle at night only)
- Threshold conditions:
  - "3+ vehicles in 10 minutes" (count threshold)
  - "Person present >2 minutes" (duration threshold)
- Condition groups with nested logic

**Acceptance Criteria:**
- Complex rules evaluate correctly (unit tested)
- UI supports building multi-condition rules (may be JSON editor for MVP)
- Rule evaluation adds <500ms latency per event
- Documentation explains rule syntax clearly
- Test feature validates complex rules against past events

**Priority:** COULD HAVE  
**Dependencies:** F5.1  
**Related US:** US-5

---

### F5.4: Alert Cooldown

**Requirement:** Prevent alert spam from repeated events

**Details:**
- Configurable cooldown period per rule (0-120 minutes)
- During cooldown:
  - Matching events still stored in database
  - No alert notification sent
  - No webhook triggered
- Cooldown timer per rule (not global)
- Cooldown resets after period expires
- Manual override: "Alert me now" button bypasses cooldown
- Cooldown status visible in dashboard

**Acceptance Criteria:**
- Only one alert per rule per cooldown period
- User can see cooldown status and time remaining
- Manual override works immediately
- Events during cooldown still visible in timeline (just no alert)
- Cooldown timer accurate to within 5 seconds

**Priority:** SHOULD HAVE  
**Dependencies:** F5.1  
**Related US:** US-2 (prevents alert fatigue)

---

## F6: Dashboard & User Interface

### F6.1: Event Timeline View

**Requirement:** Display events in chronological order

**Details:**
- Layout: Card-based timeline, newest first
- Each event card:
  - Thumbnail image (left, 200x150px)
  - Description text (main area, 2-3 lines visible)
  - Timestamp (top right, relative: "5 minutes ago")
  - Camera name (below timestamp)
  - Object tags (chips: "person", "package")
  - Confidence score (bottom right, color-coded)
  - Expand icon to see full details
- Infinite scroll or pagination (50 events per page)
- Filter controls (sidebar or top bar):
  - Date range picker (today, yesterday, last 7 days, custom)
  - Camera multi-select
  - Object type multi-select
  - Search bar
- Click card to expand modal with full details

**Acceptance Criteria:**
- Timeline loads within 2 seconds (50 events)
- Smooth scrolling with 100+ events loaded
- Filters update results immediately (<500ms)
- Mobile responsive (stacked layout on narrow screens)
- Expanded modal shows full-size thumbnail and complete description

**Priority:** MUST HAVE  
**Dependencies:** F4.2 (API)  
**Related US:** US-3

---

### F6.2: Live Camera View

**Requirement:** Preview camera feeds in dashboard

**Details:**
- Grid layout showing all configured cameras
- Each camera preview:
  - Camera name (top overlay)
  - Live thumbnail (updates every 1-2 seconds)
  - Connection status indicator (green dot = connected, red = disconnected)
  - Motion indicator (yellow pulse when motion detected)
  - "Analyze Now" button (appears on hover)
- Click camera to expand full-screen view
- Full-screen features:
  - Larger live preview (updates continuously)
  - Close button
  - "Analyze Now" button
  - Recent events from this camera (sidebar)
- Grid adjusts: 1 camera = full width, 2-4 = grid

**Acceptance Criteria:**
- Previews update every 1-2 seconds
- Full-screen view shows higher quality stream (higher FPS)
- Status indicators accurate (reflects actual connection state)
- Handles 1-4 cameras efficiently (no lag)
- Graceful degradation if camera disconnected (shows placeholder)

**Priority:** MUST HAVE  
**Dependencies:** F1.1 (camera feeds)  
**Related US:** US-9

---

### F6.3: System Settings Page

**Requirement:** Central configuration for all settings

**Details:**
- Tabbed interface:
  - **General Tab:**
    - System name input
    - Timezone selector (auto-detect default)
    - Data retention period dropdown
    - Language (English only for MVP)
  - **AI Models Tab:**
    - Model selection dropdown (GPT-4o mini, Gemini, Claude)
    - API key input (masked, show only last 4 chars)
    - Test API key button
    - Fallback model selection (optional)
    - Usage stats (requests today, this month)
  - **Motion Detection Tab:**
    - Global sensitivity slider (low/medium/high)
    - Cooldown period slider (30-120 seconds)
    - Zone configuration (per camera dropdown, then zone editor)
  - **Advanced Tab:**
    - Logging level dropdown (DEBUG, INFO, WARNING, ERROR)
    - Download logs button
    - Backup database button
    - Restore from backup (file upload)
    - Reset to defaults button (with confirmation)
- Save/cancel buttons (sticky footer)
- Form validation before save
- Confirmation toast on successful save

**Acceptance Criteria:**
- All settings persist correctly across restarts
- Validation prevents invalid configurations (shows clear errors)
- Settings take effect immediately where possible (no restart needed)
- Test buttons provide actionable feedback
- Backup/restore works without data loss

**Priority:** MUST HAVE  
**Dependencies:** F1.2 (cameras), F2.1 (motion), F3.3 (AI models)  
**Related US:** US-9

---

### F6.4: Manual Analysis Trigger

**Requirement:** User can manually analyze current camera frame

**Details:**
- "Analyze Now" button on each camera preview
- Button behavior:
  - Click → "Analyzing..." state (button disabled, spinner)
  - Processing happens same as motion-triggered
  - Result appears in event timeline
  - Success toast: "Analysis complete!"
- Bypasses motion detection (works even when motion disabled)
- No cooldown for manual triggers
- Result event marked as "manual" (icon/tag)

**Acceptance Criteria:**
- Analysis completes within 5 seconds
- Works even when motion detection disabled or scheduled off
- Clear feedback during processing (loading state)
- Result appears in timeline immediately
- Multiple manual analyses can be triggered (no artificial limits)

**Priority:** SHOULD HAVE  
**Dependencies:** F3.1 (AI processing), F6.2 (camera view)  
**Related US:** US-11

---

### F6.5: Dashboard Statistics

**Requirement:** Overview of system activity and performance

**Details:**
- Stats dashboard page or card:
  - **Summary metrics:**
    - Total events (today, this week, all time)
    - Active cameras count
    - Active alert rules count
    - System uptime (days)
  - **Charts:**
    - Events by object type (pie chart)
    - Events by camera (bar chart)
    - Events by hour of day (line chart, last 7 days)
    - Daily event trend (line chart, last 30 days)
  - **System health:**
    - Database size
    - AI API usage (requests today, remaining quota)
    - Last event timestamp
- Auto-refresh every 30 seconds
- Export stats to CSV

**Acceptance Criteria:**
- Statistics load within 1 second
- Charts render correctly on all screen sizes
- Data accurate to within 1 minute (due to caching)
- Export includes all raw data used for charts
- Responsive design (charts stack on mobile)

**Priority:** COULD HAVE  
**Dependencies:** F4.2 (events API)  
**Related US:** None (analytics feature)

---

### F6.6: Notification Center

**Requirement:** In-dashboard notifications for new events

**Details:**
- Notification bell icon (top right of header)
- Unread count badge (red circle with number)
- Click to open dropdown:
  - List of recent alerts (last 20)
  - Each shows: description preview, timestamp, camera
  - Click notification → navigate to event details
  - Mark as read/unread buttons
  - "Clear all" button
- Real-time updates via WebSocket
- Sound notification (optional, user setting)
- Desktop notification permission request (browser API)

**Acceptance Criteria:**
- Notifications appear within 2 seconds of alert trigger
- Unread count accurate
- Clicking notification navigates to correct event
- Real-time updates work without page refresh
- Desktop notifications work (if browser permission granted)

**Priority:** SHOULD HAVE  
**Dependencies:** F5.1 (alerts), WebSocket implementation  
**Related US:** US-1, US-2

---

## F7: Authentication & Security

### F7.1: User Authentication

**Requirement:** Secure login to protect system access

**Details:**
- Login page with username/email + password
- Password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one number
  - At least one special character
- Session management with JWT tokens
- Token expiration (24 hours)
- Remember me checkbox (30-day token)
- Logout functionality (invalidate token)
- Password reset flow (email-based, Phase 2)

**Acceptance Criteria:**
- Invalid credentials rejected with clear message ("Incorrect username or password")
- Sessions expire after 24 hours of inactivity
- Logout clears session immediately (can't use old token)
- Password requirements enforced on registration
- JWT tokens signed securely (HS256 minimum)

**Priority:** MUST HAVE (Phase 1.5 - after MVP core validated)  
**Dependencies:** None  
**Related US:** None (security requirement)

---

### F7.2: API Key Management

**Requirement:** Secure storage of AI model API keys

**Details:**
- Encrypted storage of API keys in database (AES-256)
- Settings UI:
  - Input field masks key (show only last 4 characters)
  - "Test API Key" button validates before saving
  - Different key per AI model
  - Edit/delete key functionality
- Key rotation: Change key without system downtime
- Keys never logged or displayed in full
- Environment variable override for deployment

**Acceptance Criteria:**
- Keys stored encrypted in database (verified with DB inspection)
- Test button succeeds with valid key, fails with invalid (clear message)
- Key rotation works without data loss or downtime
- Keys never appear in logs (search logs to verify)
- Environment variable config works for production deployment

**Priority:** MUST HAVE  
**Dependencies:** None  
**Related US:** None (security requirement)

---

### F7.3: HTTPS/TLS Support

**Requirement:** All communication encrypted in production

**Details:**
- Dashboard served over HTTPS
- WebSocket connections use WSS (WebSocket Secure)
- API endpoints require HTTPS in production
- Self-signed certificate support for local deployment
- Auto-redirect HTTP to HTTPS
- HSTS header for security

**Acceptance Criteria:**
- No mixed content warnings in browser
- Certificate validation works (valid cert or self-signed warning)
- HTTP requests redirect to HTTPS (301 status)
- WebSocket connections encrypted
- Local development can use HTTP (environment-based)

**Priority:** SHOULD HAVE (Phase 1.5)  
**Dependencies:** Deployment infrastructure  
**Related US:** None (security requirement)

---

### F7.4: Rate Limiting

**Requirement:** Protect API endpoints from abuse

**Details:**
- Rate limits per endpoint category:
  - Events API: 100 requests/minute
  - Manual analysis: 10 requests/minute
  - Settings changes: 20 requests/minute
- Return 429 status code when exceeded
- Response includes Retry-After header
- Configurable limits per deployment
- IP-based rate limiting (per-user in Phase 2)

**Acceptance Criteria:**
- Excessive requests blocked appropriately (verified with load testing)
- Normal usage unaffected (<90% of limit)
- Clear error message when rate limited
- Retry-After header accurate
- Rate limit resets after time window

**Priority:** COULD HAVE  
**Dependencies:** None  
**Related US:** None (security requirement)

---

## F8: System Administration

### F8.1: Health Check Endpoint

**Requirement:** Monitor system health programmatically

**Details:**
- Endpoint: `GET /api/health`
- Response JSON:
  ```json
  {
    "status": "healthy", // or "degraded" or "down"
    "timestamp": "2025-11-15T10:30:00Z",
    "components": {
      "database": "healthy",
      "cameras": {"camera-1": "connected", "camera-2": "disconnected"},
      "ai_model": "healthy",
      "event_queue": "healthy"
    },
    "metrics": {
      "uptime_seconds": 86400,
      "events_processed_today": 42,
      "queue_size": 0
    }
  }
  ```
- Response time <500ms
- No authentication required (for external monitoring)
- Overall status determined by component health

**Acceptance Criteria:**
- Health check returns accurate status for all components
- External monitoring tools can use endpoint
- Response time <500ms (p95)
- Status correctly reflects system state (tested by simulating failures)
- No sensitive information in response

**Priority:** SHOULD HAVE  
**Dependencies:** None  
**Related US:** None (ops requirement)

---

### F8.2: Logging & Debugging

**Requirement:** Comprehensive logging for troubleshooting

**Details:**
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log categories:
  - camera: Connection, frame capture issues
  - motion: Detection events, triggers
  - ai: API calls, responses, errors
  - events: Storage, retrieval
  - api: HTTP requests, responses
- Configurable log level per category (settings UI)
- Log rotation:
  - Max file size: 100MB
  - Keep last 7 days
  - Gzip old logs
- Structured logging (JSON format for parsing)
- Download logs from dashboard (ZIP file)

**Acceptance Criteria:**
- All errors logged with stack traces
- Logs help diagnose common issues (verified during testing)
- Log download works correctly (ZIP includes all relevant logs)
- Log rotation prevents disk space issues
- Sensitive data not logged (API keys, passwords)

**Priority:** SHOULD HAVE  
**Dependencies:** None  
**Related US:** None (ops requirement)

---

### F8.3: Backup & Restore

**Requirement:** Backup event data and configuration

**Details:**
- Manual backup trigger in settings:
  - Button: "Create Backup"
  - Exports to ZIP file:
    - SQLite database file
    - Configuration files
    - Thumbnails directory
    - System settings
- Restore from backup:
  - File upload form
  - Validation before restore
  - Confirmation dialog (destructive operation)
  - Progress indicator
- Automatic daily backups (optional):
  - Scheduled at 2am local time
  - Keep last 7 backups
  - Stored in configured backup directory

**Acceptance Criteria:**
- Backup includes all data (database, config, thumbnails)
- Restore works without data loss (tested with various backup states)
- Backup file size reasonable (<100MB for 1000 events)
- Automatic backups run reliably (verified over 7 days)
- Restore provides clear success/failure feedback

**Priority:** COULD HAVE  
**Dependencies:** F4.1 (database)  
**Related US:** None (data protection)

---

## F9: Webhook Integration

### F9.1: Webhook Configuration

**Requirement:** Send event data to external URLs

**Details:**
- Configure per alert rule:
  - Webhook URL (HTTPS recommended, HTTP allowed)
  - HTTP method: POST
  - Custom headers (for authentication tokens)
  - Payload template (default JSON)
- Payload format:
  ```json
  {
    "event_id": "uuid",
    "timestamp": "2025-11-15T10:30:00Z",
    "camera_name": "Front Door",
    "description": "...",
    "confidence": 85,
    "objects_detected": ["person", "package"],
    "thumbnail_url": "https://system/api/events/uuid/thumbnail",
    "alert_rule_name": "Package Delivery"
  }
  ```
- Retry logic:
  - 3 attempts total
  - Exponential backoff (1s, 2s, 4s)
  - Timeout: 5 seconds per attempt
- Error handling:
  - Log failures
  - Don't block event processing
  - Show webhook status in dashboard

**Acceptance Criteria:**
- Webhooks fire within 2 seconds of alert trigger
- Failed webhooks retry appropriately (3 attempts verified)
- Successful delivery logged with status code
- Timeout doesn't block event processing
- Custom headers included correctly (verified with test server)

**Priority:** SHOULD HAVE  
**Dependencies:** F5.1 (alert rules)  
**Related US:** US-4

---

### F9.2: Webhook Testing

**Requirement:** Test webhooks before deploying

**Details:**
- Test button in alert rule configuration
- Test process:
  - Sends most recent event payload (or sample if no events)
  - Displays HTTP status code
  - Shows response body (first 500 chars)
  - Shows request/response timing
  - Color-coded: Green (2xx), Yellow (3xx), Red (4xx/5xx)
- URL format validation before save
- Test logs saved (for debugging)

**Acceptance Criteria:**
- Test accurately simulates real webhook delivery
- Clear feedback on success/failure (status code + response)
- Invalid URLs rejected with message ("Must be valid URL")
- Test doesn't count against production rate limits
- Response timing accurate to within 100ms

**Priority:** SHOULD HAVE  
**Dependencies:** F9.1  
**Related US:** US-4

---

### F9.3: Webhook Logs

**Requirement:** Track webhook delivery history

**Details:**
- Webhook logs page (or tab in settings):
  - Table showing:
    - Timestamp
    - Alert rule name
    - Event ID (link to event)
    - URL (truncated)
    - Status code
    - Response time
    - Retry count
  - Filter by:
    - Success/failure
    - Alert rule
    - Date range
  - Search by URL or event ID
- Retain logs for 30 days
- Export logs to CSV

**Acceptance Criteria:**
- All webhook attempts logged (verified with test webhooks)
- Logs help diagnose delivery issues
- Filter and search work correctly
- Export includes all relevant data
- Old logs cleaned up after 30 days

**Priority:** COULD HAVE  
**Dependencies:** F9.1  
**Related US:** None (debugging feature)

---

[← Previous: Personas & Stories](./02-personas-stories.md) | [Next: Non-Functional Requirements →](./04-non-functional-requirements.md)
