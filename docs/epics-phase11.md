# ArgusAI Phase 11 - Epic & Story Breakdown

**Phase:** 11 - Mobile Platform & Remote Access
**PRD:** docs/PRD-phase11.md
**Date:** 2025-12-25

---

## Epic Overview

| Epic | Title | Stories | Priority | Effort |
|------|-------|---------|----------|--------|
| P11-1 | Remote Access via Cloudflare Tunnel | 4 | P1 | Medium |
| P11-2 | Mobile Push Notifications | 6 | P1 | Large |
| P11-3 | AI Context Enhancement (MCP) | 4 | P2 | Medium |
| P11-4 | Query-Adaptive Frame Selection | 3 | P3 | Medium |
| P11-5 | Platform Polish & Documentation | 4 | P3 | Small |

**Total: 5 Epics, 21 Stories**

---

## Epic P11-1: Remote Access via Cloudflare Tunnel

**Goal:** Enable secure remote access to ArgusAI without VPN or port forwarding

**Backlog Items:** IMP-029, FF-025

### Stories

#### P11-1.1: Implement Cloudflare Tunnel Integration

**As a** user
**I want** ArgusAI to connect through Cloudflare Tunnel
**So that** I can access my dashboard from anywhere without port forwarding

**Acceptance Criteria:**
- AC-1.1.1: Backend supports cloudflared tunnel connection
- AC-1.1.2: Tunnel token stored securely in system settings (encrypted)
- AC-1.1.3: Tunnel connects on application startup when enabled
- AC-1.1.4: Connection works for both backend API and frontend

**Tasks:**
- [ ] Add cloudflared integration documentation
- [ ] Create TunnelService class in backend/app/services/
- [ ] Add tunnel configuration to system settings model
- [ ] Implement secure token storage with Fernet encryption
- [ ] Add startup hook to initialize tunnel when enabled

**Effort:** 3 points

---

#### P11-1.2: Add Tunnel Status Monitoring and Auto-Reconnect

**As a** user
**I want** the tunnel to automatically reconnect if disconnected
**So that** remote access remains reliable

**Acceptance Criteria:**
- AC-1.2.1: System monitors tunnel connection health
- AC-1.2.2: Auto-reconnect triggers within 30 seconds of disconnect
- AC-1.2.3: Connection events logged for troubleshooting
- AC-1.2.4: API endpoint `/api/v1/system/tunnel-status` returns current state

**Tasks:**
- [ ] Implement health check loop in TunnelService
- [ ] Add reconnection logic with exponential backoff
- [ ] Create tunnel status API endpoint
- [ ] Add structured logging for tunnel events
- [ ] Write tests for reconnection scenarios

**Effort:** 2 points

---

#### P11-1.3: Create Settings UI for Tunnel Configuration

**As a** user
**I want** to configure Cloudflare Tunnel from the Settings page
**So that** I can enable remote access without editing config files

**Acceptance Criteria:**
- AC-1.3.1: Settings > System tab includes Tunnel section
- AC-1.3.2: Enable/disable toggle for tunnel
- AC-1.3.3: Secure input field for tunnel token
- AC-1.3.4: Status indicator shows connection state
- AC-1.3.5: Test connection button validates setup

**Tasks:**
- [ ] Create TunnelSettings component
- [ ] Add to Settings page System tab
- [ ] Implement tunnel status display with badge
- [ ] Add secure token input with show/hide toggle
- [ ] Create test connection flow with feedback

**Effort:** 2 points

---

#### P11-1.4: Document Tunnel Setup in User Guide

**As a** user
**I want** clear documentation for setting up Cloudflare Tunnel
**So that** I can configure remote access correctly

**Acceptance Criteria:**
- AC-1.4.1: Step-by-step guide for cloudflared installation
- AC-1.4.2: Instructions for creating tunnel in Cloudflare dashboard
- AC-1.4.3: Configuration guide for ArgusAI settings
- AC-1.4.4: Troubleshooting section for common issues
- AC-1.4.5: Security considerations documented

**Tasks:**
- [ ] Write cloudflared installation guide (Linux, macOS, Windows)
- [ ] Document Cloudflare Zero Trust dashboard setup
- [ ] Create ArgusAI configuration walkthrough with screenshots
- [ ] Add troubleshooting FAQ
- [ ] Document security best practices

**Effort:** 1 point

---

## Epic P11-2: Mobile Push Notifications

**Goal:** Deliver push notifications to iOS and Android devices

**Backlog Items:** IMP-030, IMP-031, IMP-032, IMP-027, IMP-028

### Stories

#### P11-2.1: Implement APNS Provider for iOS Push

**As a** iOS user
**I want** to receive push notifications on my iPhone/iPad
**So that** I'm alerted to security events when away from home

**Acceptance Criteria:**
- AC-2.1.1: APNSProvider class connects via HTTP/2 to Apple's servers
- AC-2.1.2: Authentication uses p8 auth key file
- AC-2.1.3: Configuration stores key_id, team_id, key_file path
- AC-2.1.4: Payloads formatted per Apple's notification format
- AC-2.1.5: Error responses handled (invalid token, etc.)
- AC-2.1.6: Token invalidation removes stale device tokens

**Tasks:**
- [ ] Create APNSProvider class in backend/app/services/push/
- [ ] Implement HTTP/2 connection using httpx or aioh2
- [ ] Add APNS configuration to system settings
- [ ] Create iOS notification payload builder
- [ ] Implement error handling for APNS responses
- [ ] Add token cleanup for invalidated tokens
- [ ] Write unit tests with mocked APNS

**Effort:** 5 points

---

#### P11-2.2: Implement FCM Provider for Android Push

**As an** Android user
**I want** to receive push notifications on my phone
**So that** I'm alerted to security events when away from home

**Acceptance Criteria:**
- AC-2.2.1: FCMProvider class connects to FCM HTTP v1 API
- AC-2.2.2: Authentication uses service account JSON
- AC-2.2.3: Configuration stores service account path securely
- AC-2.2.4: Payloads formatted per FCM notification format
- AC-2.2.5: Data messages supported for background processing
- AC-2.2.6: Error responses handled (invalid token, quota exceeded)

**Tasks:**
- [ ] Create FCMProvider class in backend/app/services/push/
- [ ] Implement FCM HTTP v1 API client
- [ ] Add FCM configuration to system settings
- [ ] Create Android notification payload builder
- [ ] Support both notification and data message types
- [ ] Implement error handling and token refresh
- [ ] Write unit tests with mocked FCM

**Effort:** 4 points

---

#### P11-2.3: Create Unified Push Dispatch Service

**As a** system
**I want** a single service to route notifications to all push providers
**So that** event notifications reach all user devices regardless of platform

**Acceptance Criteria:**
- AC-2.3.1: PushDispatchService routes to WebPush, APNS, FCM
- AC-2.3.2: Service queries device tokens by user_id
- AC-2.3.3: Notifications sent to all devices in parallel
- AC-2.3.4: Retry logic with exponential backoff (max 3 retries)
- AC-2.3.5: Delivery status tracked per device
- AC-2.3.6: Notification preferences applied before dispatch

**Tasks:**
- [ ] Create PushDispatchService class
- [ ] Implement provider routing logic
- [ ] Add parallel dispatch using asyncio.gather
- [ ] Implement retry logic with backoff
- [ ] Create delivery tracking model and storage
- [ ] Integrate with existing notification preferences
- [ ] Write integration tests

**Effort:** 4 points

---

#### P11-2.4: Implement Device Registration and Token Management

**As a** mobile user
**I want** to register my device for push notifications
**So that** I receive alerts on this specific device

**Acceptance Criteria:**
- AC-2.4.1: Device model stores device_id, platform, name, push_token, user_id, last_seen
- AC-2.4.2: POST `/api/v1/devices` registers new device
- AC-2.4.3: GET `/api/v1/devices` lists user's devices
- AC-2.4.4: DELETE `/api/v1/devices/{id}` revokes device
- AC-2.4.5: Device tokens encrypted at rest
- AC-2.4.6: Duplicate device_id updates existing record

**Tasks:**
- [ ] Create Device model with migration
- [ ] Add DeviceSchema for API validation
- [ ] Create device CRUD endpoints in api/v1/devices.py
- [ ] Implement token encryption using Fernet
- [ ] Add upsert logic for device registration
- [ ] Write API tests

**Effort:** 3 points

---

#### P11-2.5: Add Mobile Push Preferences (Quiet Hours)

**As a** user
**I want** to set quiet hours for push notifications
**So that** I'm not disturbed during sleep or meetings

**Acceptance Criteria:**
- AC-2.5.1: User can set quiet hours start and end time
- AC-2.5.2: Quiet hours respect user's timezone
- AC-2.5.3: Notifications suppressed during quiet hours
- AC-2.5.4: Override option for critical alerts
- AC-2.5.5: Per-device quiet hours supported

**Tasks:**
- [ ] Add quiet_hours fields to notification preferences
- [ ] Implement timezone-aware quiet hours check
- [ ] Update PushDispatchService to check quiet hours
- [ ] Add UI controls for quiet hours in Settings
- [ ] Support per-device override settings
- [ ] Write tests for timezone edge cases

**Effort:** 2 points

---

#### P11-2.6: Support Notification Thumbnails/Attachments

**As a** mobile user
**I want** to see event thumbnails in notifications
**So that** I can quickly assess the situation without opening the app

**Acceptance Criteria:**
- AC-2.6.1: iOS notifications include image attachment
- AC-2.6.2: Android notifications include BigPicture style
- AC-2.6.3: Thumbnail URL accessible via signed temporary link
- AC-2.6.4: Images optimized for notification display (small size)
- AC-2.6.5: Fallback to text-only if image unavailable

**Tasks:**
- [ ] Create signed URL generator for thumbnails
- [ ] Add image attachment to APNS payload
- [ ] Add BigPicture to FCM payload
- [ ] Implement image optimization (resize, compress)
- [ ] Add fallback handling
- [ ] Test on real iOS and Android devices

**Effort:** 3 points

---

## Epic P11-3: AI Context Enhancement (MCP)

**Goal:** Improve AI description accuracy through accumulated context

**Backlog Items:** IMP-016, IMP-024, IMP-025

### Stories

#### P11-3.1: Implement MCPContextProvider MVP with Feedback Context

**As a** system
**I want** to include user feedback history in AI prompts
**So that** the AI learns from corrections and improves accuracy

**Acceptance Criteria:**
- AC-3.1.1: MCPContextProvider class created in backend/app/services/
- AC-3.1.2: Provider gathers recent feedback (last 50 items)
- AC-3.1.3: Camera-specific accuracy stats included
- AC-3.1.4: Common corrections summarized
- AC-3.1.5: Context formatted for AI prompt injection
- AC-3.1.6: Fail-open design - AI works if context fails

**Tasks:**
- [ ] Create MCPContextProvider class
- [ ] Implement feedback history query
- [ ] Calculate per-camera accuracy metrics
- [ ] Extract common correction patterns
- [ ] Create context formatting for prompts
- [ ] Add error handling with fail-open
- [ ] Write unit tests

**Effort:** 3 points

---

#### P11-3.2: Add Entity Match Context to Provider

**As a** system
**I want** to include known entity information in AI prompts
**So that** the AI can identify recognized people and vehicles

**Acceptance Criteria:**
- AC-3.2.1: Entity context includes matched entity details
- AC-3.2.2: Similar entities (by embedding) suggested
- AC-3.2.3: Entity names and attributes included in prompt
- AC-3.2.4: Recent entity sightings provide temporal context
- AC-3.2.5: Context size limited to prevent prompt overflow

**Tasks:**
- [ ] Add entity context gathering to MCPContextProvider
- [ ] Query matched entity by event similarity
- [ ] Include entity name, type, attributes
- [ ] Add recent sighting history
- [ ] Implement context size limiting
- [ ] Write tests for entity matching

**Effort:** 2 points

---

#### P11-3.3: Integrate Camera and Time Pattern Context

**As a** system
**I want** camera location and time patterns in AI prompts
**So that** the AI understands typical activity for context

**Acceptance Criteria:**
- AC-3.3.1: Camera context includes location hints
- AC-3.3.2: Typical activity patterns for camera included
- AC-3.3.3: Time-of-day activity levels provided
- AC-3.3.4: Unusual timing flagged in context
- AC-3.3.5: False positive patterns shared

**Tasks:**
- [ ] Add camera context gathering
- [ ] Query historical activity patterns by time
- [ ] Calculate typical vs unusual timing
- [ ] Include false positive patterns from feedback
- [ ] Integrate with existing prompt service
- [ ] Write pattern detection tests

**Effort:** 3 points

---

#### P11-3.4: Add Context Caching and Performance Metrics

**As a** system
**I want** context gathering to be fast and monitored
**So that** it doesn't slow down event processing

**Acceptance Criteria:**
- AC-3.4.1: Context cached with 60-second TTL
- AC-3.4.2: Cache key based on camera + time window
- AC-3.4.3: Context queries complete within 50ms (p95)
- AC-3.4.4: Metrics track context gathering latency
- AC-3.4.5: Cache hit/miss ratios monitored

**Tasks:**
- [ ] Implement in-memory context cache
- [ ] Add TTL expiration logic
- [ ] Create cache key generation
- [ ] Add Prometheus metrics for latency
- [ ] Add cache hit/miss counters
- [ ] Write performance tests

**Effort:** 2 points

---

## Epic P11-4: Query-Adaptive Frame Selection

**Goal:** Select the most relevant frames for targeted re-analysis queries

**Backlog Items:** FF-022, IMP-033, IMP-034

### Stories

#### P11-4.1: Add Text Encoding to EmbeddingService

**As a** system
**I want** to encode text queries into embeddings
**So that** I can compare queries against frame content

**Acceptance Criteria:**
- AC-4.1.1: EmbeddingService.encode_text(query) method added
- AC-4.1.2: Uses same CLIP model as image encoding
- AC-4.1.3: Text embeddings compatible with image embeddings
- AC-4.1.4: Query preprocessing (lowercase, trim)
- AC-4.1.5: "a photo of {query}" formatting for single words

**Tasks:**
- [ ] Add encode_text method to EmbeddingService
- [ ] Implement query preprocessing
- [ ] Add "a photo of" formatting for short queries
- [ ] Ensure embedding dimension matches images
- [ ] Write unit tests

**Effort:** 2 points

---

#### P11-4.2: Implement Frame Embedding Storage and Generation

**As a** system
**I want** to store embeddings for extracted frames
**So that** I can score them against queries later

**Acceptance Criteria:**
- AC-4.2.1: FrameEmbedding model with event_id, frame_index, embedding, model_version
- AC-4.2.2: Migration creates frame_embeddings table
- AC-4.2.3: Embeddings generated during frame extraction
- AC-4.2.4: Batch generation for efficiency
- AC-4.2.5: Embeddings stored as JSON array

**Tasks:**
- [ ] Create FrameEmbedding SQLAlchemy model
- [ ] Write Alembic migration
- [ ] Integrate embedding generation into frame extraction
- [ ] Implement batch processing
- [ ] Add cleanup for old embeddings
- [ ] Write storage tests

**Effort:** 3 points

---

#### P11-4.3: Create Smart-Reanalyze Endpoint with Query Matching

**As a** user
**I want** to re-analyze an event with a specific question
**So that** the AI focuses on answering my query

**Acceptance Criteria:**
- AC-4.3.1: POST `/api/v1/events/{id}/smart-reanalyze?query=...` available
- AC-4.3.2: Query encoded and compared against frame embeddings
- AC-4.3.3: Cosine similarity scores all frames
- AC-4.3.4: Top-K frames (default 5) selected for analysis
- AC-4.3.5: Selection overhead under 60ms
- AC-4.3.6: Falls back to uniform selection if no embeddings

**Tasks:**
- [ ] Create smart-reanalyze API endpoint
- [ ] Implement cosine similarity scoring
- [ ] Add top-K selection logic
- [ ] Integrate with existing re-analysis flow
- [ ] Add fallback for missing embeddings
- [ ] Write API tests with timing assertions

**Effort:** 3 points

---

## Epic P11-5: Platform Polish & Documentation

**Goal:** Improve performance and create user documentation

**Backlog Items:** IMP-005, FF-011, FF-017, FF-026

### Stories

#### P11-5.1: Optimize Camera List Performance

**As a** user with many cameras
**I want** the camera list to scroll smoothly
**So that** the UI remains responsive

**Acceptance Criteria:**
- AC-5.1.1: CameraPreview uses React.memo to prevent re-renders
- AC-5.1.2: Virtual scrolling enabled for lists > 20 cameras
- AC-5.1.3: React Query provides caching and deduplication
- AC-5.1.4: 100 cameras render without UI lag
- AC-5.1.5: Preview images lazy-loaded on scroll

**Tasks:**
- [ ] Wrap CameraPreview with React.memo
- [ ] Add react-window for virtual scrolling
- [ ] Implement lazy loading for previews
- [ ] Profile and optimize re-renders
- [ ] Write performance tests

**Effort:** 2 points

---

#### P11-5.2: Add Test Connection Before Camera Save

**As a** user adding a camera
**I want** to test the connection before saving
**So that** I know the camera is configured correctly

**Acceptance Criteria:**
- AC-5.2.1: POST `/api/v1/cameras/test` accepts camera config without saving
- AC-5.2.2: Returns specific error messages for connection issues
- AC-5.2.3: UI shows "Test Connection" button
- AC-5.2.4: Test results displayed before save enabled
- AC-5.2.5: Timeout after 10 seconds with appropriate message

**Tasks:**
- [ ] Create test connection API endpoint
- [ ] Implement RTSP connection test logic
- [ ] Add descriptive error messages
- [ ] Create UI test button and feedback display
- [ ] Add timeout handling
- [ ] Write integration tests

**Effort:** 2 points

---

#### P11-5.3: Create GitHub Pages Documentation Site

**As a** user or contributor
**I want** professional documentation online
**So that** I can learn how to use and contribute to ArgusAI

**Acceptance Criteria:**
- AC-5.3.1: GitHub Pages site live at project URL
- AC-5.3.2: Landing page with project overview
- AC-5.3.3: Installation guide with copy-paste commands
- AC-5.3.4: Configuration reference
- AC-5.3.5: API documentation
- AC-5.3.6: Auto-deploys on push to main

**Tasks:**
- [ ] Choose and set up static site generator (Docusaurus recommended)
- [ ] Create landing page with features
- [ ] Write installation documentation
- [ ] Add configuration reference
- [ ] Generate API docs from OpenAPI spec
- [ ] Set up GitHub Actions deployment
- [ ] Configure custom domain (optional)

**Effort:** 3 points

---

#### P11-5.4: Add Export Motion Events to CSV

**As a** user
**I want** to export my events to CSV
**So that** I can analyze them externally

**Acceptance Criteria:**
- AC-5.4.1: GET `/api/v1/events/export?format=csv` returns CSV file
- AC-5.4.2: Export includes timestamp, camera, description, confidence, objects
- AC-5.4.3: Date range filtering supported
- AC-5.4.4: UI button triggers download
- AC-5.4.5: Large exports streamed to prevent memory issues

**Tasks:**
- [ ] Create CSV export endpoint
- [ ] Implement streaming CSV generation
- [ ] Add date range query parameters
- [ ] Add export button to Events page
- [ ] Write export tests

**Effort:** 2 points

---

## Story Point Summary

| Epic | Stories | Points |
|------|---------|--------|
| P11-1 | 4 | 8 |
| P11-2 | 6 | 21 |
| P11-3 | 4 | 10 |
| P11-4 | 3 | 8 |
| P11-5 | 4 | 9 |
| **Total** | **21** | **56** |

---

## Implementation Order

### Sprint 1: Foundation (P1 items)
1. P11-1.1: Cloudflare Tunnel integration
2. P11-1.2: Tunnel monitoring/reconnect
3. P11-2.4: Device registration
4. P11-2.1: APNS provider

### Sprint 2: Mobile Push Complete (P1 items)
5. P11-2.2: FCM provider
6. P11-2.3: Unified dispatch
7. P11-2.5: Quiet hours
8. P11-2.6: Thumbnails
9. P11-1.3: Tunnel UI
10. P11-1.4: Tunnel docs

### Sprint 3: AI Enhancement (P2 items)
11. P11-3.1: MCP feedback context
12. P11-3.2: Entity context
13. P11-3.3: Camera/time patterns
14. P11-3.4: Caching/metrics

### Sprint 4: Polish (P3 items)
15. P11-4.1: Text encoding
16. P11-4.2: Frame embeddings
17. P11-4.3: Smart reanalyze
18. P11-5.1: Camera list perf
19. P11-5.2: Test connection
20. P11-5.3: GitHub Pages
21. P11-5.4: CSV export

---

_Phase 11 epics derived from PRD-phase11.md and open backlog items._
