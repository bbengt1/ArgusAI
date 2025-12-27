# ArgusAI Phase 12 - Epic Breakdown
## Mobile Backend Infrastructure & Entity-Based Alerts

**Author:** Brent
**Date:** 2025-12-26
**PRD:** docs/PRD-phase12.md
**Architecture:** docs/architecture/phase-12-additions.md

---

## Overview

This document provides the complete epic and story breakdown for ArgusAI Phase 12, decomposing the 47 functional requirements from the PRD into implementable stories organized across 4 epics.

**Epics:**
| Epic | Priority | Stories | Description |
|------|----------|---------|-------------|
| P12-1 | HIGH | 5 | Entity-Based Alert Rules |
| P12-2 | MEDIUM | 5 | Mobile Device Registration |
| P12-3 | MEDIUM | 6 | Mobile Authentication & Pairing |
| P12-4 | LOW | 5 | Query-Adaptive Optimization |

**Total Stories:** 21

---

## Functional Requirements Inventory

**Entity-Based Alert Rules (FR1-FR8):**
- FR1: Create alert rules for specific entities
- FR2: Entity dropdown in alert rule UI
- FR3: "Any unknown entity" stranger detection
- FR4: Combine entity filters with existing conditions
- FR5: Entity name in alert rule list
- FR6: Entity name in push notifications
- FR7: Entity info in webhook payloads
- FR8: View alert rules from entity detail page

**Mobile Device Registration (FR9-FR17):**
- FR9: Mobile app device registration
- FR10: Capture platform, name, device ID
- FR11: View registered devices in Settings
- FR12: Rename devices
- FR13: Revoke/delete device registrations
- FR14: Revocation invalidates all tokens
- FR15: Associate push tokens with devices
- FR16: Track last_seen timestamp
- FR17: Flag inactive devices (90+ days)

**Mobile Authentication & Pairing (FR18-FR28):**
- FR18: Request 6-digit pairing code
- FR19: Pairing codes expire after 5 minutes
- FR20: Confirm codes via web dashboard
- FR21: Exchange confirmed code for JWT
- FR22: JWT includes device_id claim
- FR23: Refresh expired tokens
- FR24: Sliding window token extension
- FR25: Refresh token rotation
- FR26: Password change invalidates all tokens
- FR27: Rate limiting for pairing attempts
- FR28: WebSocket notification for pairing requests

**Query-Adaptive Optimization (FR29-FR38):**
- FR29: Batch embedding generation
- FR30: Diversity filtering for frames
- FR31: Quality scores in selection
- FR32: Query matching metrics
- FR33: Multi-query OR logic
- FR34: Query suggestions
- FR35: A/B comparison mode
- FR36: Query result caching
- FR37: Relevance scores in re-analyze modal
- FR38: Auto-format single-word queries

**API Endpoints (FR39-FR47):**
- FR39-FR42: Device CRUD endpoints
- FR43-FR45: Mobile auth endpoints
- FR46-FR47: Alert rule entity endpoints

---

## FR Coverage Map

| Epic | FRs Covered |
|------|-------------|
| P12-1 | FR1-FR8, FR46-FR47 |
| P12-2 | FR9-FR17, FR39-FR42 |
| P12-3 | FR18-FR28, FR43-FR45 |
| P12-4 | FR29-FR38 |

**Coverage:** All 47 FRs mapped to epics and stories.

---

## Epic P12-1: Entity-Based Alert Rules

**Goal:** Enable users to create personalized alert rules that trigger for specific recognized entities (people/vehicles) or for unknown strangers, transforming generic detection alerts into context-aware notifications.

**Priority:** HIGH - Highest user value, independent of mobile infrastructure

**FRs Covered:** FR1-FR8, FR46-FR47

---

### Story P12-1.1: Add Entity Field to AlertRule Model

As a developer,
I want to extend the AlertRule model with entity filtering fields,
So that alert rules can target specific entities or stranger detection.

**Acceptance Criteria:**

**Given** the existing AlertRule model
**When** I add entity support
**Then** the model includes:
- `entity_id` (nullable FK to RecognizedEntity)
- `entity_match_mode` (enum: 'specific', 'unknown', 'any')

**And** database migration adds columns with proper indexes
**And** existing alert rules default to `entity_match_mode = 'any'` (no breaking changes)
**And** API schema includes entity_id and entity_match_mode fields

**Prerequisites:** None

**Technical Notes:**
- Extend AlertRule in `backend/app/models/alert_rule.py`
- Create Alembic migration for new columns
- Add index on entity_id for efficient lookups
- Update AlertRuleCreate/AlertRuleUpdate Pydantic schemas

---

### Story P12-1.2: Implement Entity Filter in Alert Evaluation

As the system,
I want to evaluate entity conditions when processing alert rules,
So that entity-based rules only trigger for matching entities.

**Acceptance Criteria:**

**Given** an alert rule with `entity_match_mode = 'specific'` and `entity_id = X`
**When** an event is detected with matched entity Y
**Then** the rule triggers only if X == Y

**Given** an alert rule with `entity_match_mode = 'unknown'`
**When** an event is detected with no matched entity (stranger)
**Then** the rule triggers

**Given** an alert rule with `entity_match_mode = 'any'`
**When** any event is detected
**Then** standard rule evaluation applies (entity not considered)

**And** entity evaluation adds <10ms overhead per rule
**And** evaluation fails-open (delivers alert if entity lookup fails)

**Prerequisites:** P12-1.1

**Technical Notes:**
- Extend `AlertRuleEngine.evaluate_rule()` in `backend/app/services/alert_engine.py`
- Add entity lookup during event processing
- Include entity match in rule evaluation logic
- Add performance logging for entity evaluation time

---

### Story P12-1.3: Add Entity Selector to Alert Rule UI

As a user,
I want to select an entity when creating/editing an alert rule,
So that I can create personalized alerts for specific people or vehicles.

**Acceptance Criteria:**

**Given** I am creating or editing an alert rule
**When** I want to target a specific entity
**Then** I see an "Entity Filter" section with:
- Radio buttons: "Any detection", "Specific entity", "Unknown (strangers)"
- Entity dropdown (appears when "Specific entity" selected)
- Dropdown shows entities grouped by type (People, Vehicles)
- Search/filter within dropdown for large entity lists

**And** selected entity name appears in rule summary
**And** form validates that entity exists before save
**And** 44x44px touch targets on mobile

**Prerequisites:** P12-1.1, P12-1.2

**Technical Notes:**
- Create `EntityRuleSelector.tsx` component
- Use TanStack Query to fetch entities
- Integrate with existing AlertRuleForm
- Add entity_id and entity_match_mode to form state

---

### Story P12-1.4: Include Entity in Notifications and Webhooks

As a user,
I want push notifications and webhooks to include entity information,
So that I know WHO triggered the alert without opening the app.

**Acceptance Criteria:**

**Given** an entity-based alert rule triggers
**When** a push notification is sent
**Then** the notification includes:
- Title: "{Entity Name} detected" (e.g., "John detected")
- Body includes entity name in description

**Given** an entity-based alert rule triggers for unknown entity
**When** a push notification is sent
**Then** the notification shows "Unknown person detected" or similar

**Given** an entity-based alert with webhook action
**When** webhook is dispatched
**Then** payload includes:
- `entity_id`: matched entity ID (or null)
- `entity_name`: matched entity name (or "Unknown")
- `entity_type`: "person", "vehicle", etc.

**Prerequisites:** P12-1.2

**Technical Notes:**
- Extend `AlertRuleEngine.format_notification()`
- Add entity fields to webhook payload schema
- Update push notification payload in dispatch service

---

### Story P12-1.5: Display Entity Alert Rules on Entity Detail Page

As a user,
I want to see which alert rules are associated with an entity,
So that I can manage personalized alerts from the entity page.

**Acceptance Criteria:**

**Given** I am viewing an entity detail page
**When** there are alert rules targeting this entity
**Then** I see an "Alert Rules" section showing:
- List of alert rules with this entity
- Rule name, enabled status, last triggered
- Quick toggle to enable/disable each rule
- Link to edit rule

**Given** no alert rules target this entity
**When** I view the entity detail page
**Then** I see "No alert rules for this entity" with "Create Alert Rule" button

**And** GET `/api/v1/context/entities/{id}/alert-rules` endpoint returns associated rules

**Prerequisites:** P12-1.1, P12-1.3

**Technical Notes:**
- Create endpoint in `backend/app/api/v1/context.py`
- Add AlertRulesSection to EntityDetailPage
- Include quick actions for rule management

---

## Epic P12-2: Mobile Device Registration

**Goal:** Implement device management backend to track and manage mobile app registrations, enabling push token association and device lifecycle management.

**Priority:** MEDIUM - Foundation for Epic P12-3

**FRs Covered:** FR9-FR17, FR39-FR42

---

### Story P12-2.1: Extend Device Model for Mobile Registration

As a developer,
I want to enhance the Device model for mobile app registration,
So that mobile devices can be fully managed with proper lifecycle tracking.

**Acceptance Criteria:**

**Given** the existing Device model from Phase 11
**When** I extend it for mobile registration
**Then** the model includes:
- `pairing_confirmed` (boolean, default false)
- `device_model` (string, e.g., "iPhone 15 Pro")
- Relationship to RefreshToken for token management

**And** migration adds new columns
**And** API schema updated for new fields

**Prerequisites:** None

**Technical Notes:**
- Extend Device in `backend/app/models/device.py`
- Add device_model to capture hardware info
- pairing_confirmed tracks whether device completed pairing flow

---

### Story P12-2.2: Implement Device CRUD Endpoints

As a mobile app developer,
I want device management API endpoints,
So that mobile apps can register and manage their device registration.

**Acceptance Criteria:**

**Given** an authenticated user
**When** calling POST `/api/v1/devices`
**Then** device is registered with:
- device_id, platform, name, push_token
- Response includes created device object
- Response time <200ms

**Given** an authenticated user
**When** calling GET `/api/v1/devices`
**Then** returns list of user's registered devices with:
- All device fields
- `inactive_warning: true` if last_seen > 90 days

**Given** an authenticated user
**When** calling PUT `/api/v1/devices/{id}`
**Then** device name can be updated

**Given** an authenticated user
**When** calling DELETE `/api/v1/devices/{id}`
**Then** device is removed and all tokens revoked

**Prerequisites:** P12-2.1

**Technical Notes:**
- Create `backend/app/api/v1/devices.py` router
- Use DeviceService for business logic
- Ensure token revocation on delete

---

### Story P12-2.3: Build Device Management UI

As a user,
I want to view and manage registered devices in Settings,
So that I can see which devices are connected and revoke access if needed.

**Acceptance Criteria:**

**Given** I navigate to Settings > Devices
**When** I have registered devices
**Then** I see a list showing:
- Device name (editable)
- Platform icon (iOS/Android/Web)
- Last seen timestamp
- "Inactive" badge if >90 days
- Delete button with confirmation

**Given** I click delete on a device
**When** I confirm the action
**Then** device is removed and shows success toast

**And** empty state shows "No devices registered" message
**And** responsive layout for mobile viewing

**Prerequisites:** P12-2.2

**Technical Notes:**
- Create `DeviceManager.tsx` in `frontend/components/settings/`
- Use TanStack Query for device list
- Add to Settings page tabs

---

### Story P12-2.4: Associate Push Tokens with Devices

As the system,
I want push tokens linked to specific devices,
So that notifications route to the correct device and invalid tokens can be cleaned up.

**Acceptance Criteria:**

**Given** a device registers with a push token
**When** the token is stored
**Then** it's encrypted and associated with that device record

**Given** a device's push token changes (app reinstall)
**When** the device re-registers
**Then** the new token replaces the old one

**Given** a push notification fails with "token invalid"
**When** the push service processes the error
**Then** the device's push token is cleared (not deleted - device remains)

**Prerequisites:** P12-2.2

**Technical Notes:**
- Extend existing push_token handling in Device model
- Update PushDispatchService to query devices by token
- Add token cleanup on push failure

---

### Story P12-2.5: Implement Device Lifecycle Tracking

As an administrator,
I want to track device activity and flag inactive devices,
So that old registrations can be identified and cleaned up.

**Acceptance Criteria:**

**Given** a device makes any authenticated API request
**When** the request is processed
**Then** `last_seen_at` is updated to current timestamp

**Given** a device has `last_seen_at` > 90 days ago
**When** viewing the device list
**Then** the device shows "Inactive" badge

**Given** inactive devices exist
**When** viewing Settings > Devices
**Then** option to "Remove inactive devices" appears

**Prerequisites:** P12-2.2

**Technical Notes:**
- Add middleware to update last_seen_at on authenticated requests
- Add bulk delete endpoint for inactive devices
- Consider background job for automatic cleanup (optional)

---

## Epic P12-3: Mobile Authentication & Pairing

**Goal:** Implement secure device pairing flow using 6-digit codes and JWT token management with refresh rotation, enabling future native mobile apps to authenticate securely.

**Priority:** MEDIUM - Depends on P12-2, enables native apps

**FRs Covered:** FR18-FR28, FR43-FR45

---

### Story P12-3.1: Create PairingCode and RefreshToken Models

As a developer,
I want database models for pairing codes and refresh tokens,
So that mobile authentication flow can be implemented securely.

**Acceptance Criteria:**

**Given** the need for mobile pairing
**When** I create the PairingCode model
**Then** it includes:
- `code` (6-digit string, unique)
- `device_id` (requesting device)
- `user_id` (null until confirmed)
- `platform` (ios/android)
- `expires_at` (5-minute expiry)
- `confirmed_at` (when user confirmed)

**Given** the need for token rotation
**When** I create the RefreshToken model
**Then** it includes:
- `device_id` (FK to Device)
- `token_hash` (SHA-256 hash, not plaintext)
- `expires_at` (30-day expiry)
- `revoked_at` (null if valid)

**And** migrations create tables with proper indexes

**Prerequisites:** P12-2.1

**Technical Notes:**
- Create models in `backend/app/models/`
- Add indexes on code and token_hash for fast lookups
- Store token_hash, never plaintext refresh tokens

---

### Story P12-3.2: Implement Pairing Code Generation and Confirmation

As a mobile app,
I want to request a pairing code and have the user confirm it,
So that I can securely authenticate without exposing credentials.

**Acceptance Criteria:**

**Given** a mobile app requests pairing
**When** calling POST `/api/v1/mobile/auth/pair` with device_id, platform
**Then** response includes:
- 6-digit cryptographically random code
- expires_in: 300 (seconds)
- Response time <50ms

**Given** a pairing code exists
**When** user enters code in web dashboard Settings > Devices
**And** clicks "Confirm"
**Then** POST `/api/v1/mobile/auth/confirm` marks code as confirmed
**And** WebSocket broadcast notifies dashboard of pairing request

**Given** 5 pairing attempts in 1 minute from same IP
**When** another attempt is made
**Then** 429 Too Many Requests is returned

**Prerequisites:** P12-3.1

**Technical Notes:**
- Use `secrets.choice()` for code generation
- Add rate limiting with slowapi
- Broadcast pairing request via WebSocket for real-time UI update

---

### Story P12-3.3: Build Pairing Confirmation UI

As a user,
I want to confirm pairing codes from the web dashboard,
So that I can authorize mobile devices to access my ArgusAI.

**Acceptance Criteria:**

**Given** a pairing code is generated by a mobile app
**When** I'm on Settings > Devices
**Then** I see a notification: "New device wants to pair"

**Given** I click to view the pairing request
**When** I see the confirmation modal
**Then** it shows:
- 6-digit code input field
- Device name and platform
- "Confirm" and "Deny" buttons
- Countdown timer showing expiry

**Given** I enter the correct code and click Confirm
**When** the code is valid and not expired
**Then** device is paired and success message shown

**And** WebSocket updates in real-time (no page refresh needed)

**Prerequisites:** P12-3.2

**Technical Notes:**
- Create `PairingConfirmation.tsx` modal
- Listen for WebSocket PAIRING_REQUESTED events
- Show toast notification when pairing request arrives

---

### Story P12-3.4: Implement Token Exchange and JWT Generation

As a mobile app,
I want to exchange a confirmed pairing code for JWT tokens,
So that I can make authenticated API requests.

**Acceptance Criteria:**

**Given** a confirmed pairing code
**When** calling POST `/api/v1/mobile/auth/verify` with the code
**Then** response includes:
- access_token (15-minute expiry)
- refresh_token (30-day expiry)
- token_type: "bearer"
- expires_in: 900
- device_id

**And** access token includes device_id claim
**And** pairing code is deleted after successful exchange

**Given** an unconfirmed or expired code
**When** attempting to verify
**Then** 401 Unauthorized is returned

**Prerequisites:** P12-3.2, P12-3.3

**Technical Notes:**
- Create TokenService for JWT generation
- Use HS256 for access tokens (RS256 optional enhancement)
- Store refresh token hash, not plaintext

---

### Story P12-3.5: Implement Token Refresh with Rotation

As a mobile app,
I want to refresh my access token before it expires,
So that I can maintain a continuous session without re-pairing.

**Acceptance Criteria:**

**Given** a valid refresh token
**When** calling POST `/api/v1/auth/refresh` with refresh_token and device_id
**Then** response includes:
- New access_token
- New refresh_token (rotation)
- Old refresh token is revoked
- Response time <100ms

**And** 24-hour sliding window extends session

**Given** a revoked or expired refresh token
**When** attempting to refresh
**Then** 401 Unauthorized is returned

**Given** concurrent refresh requests with same token
**When** processed
**Then** only first succeeds, others get 401 (prevents replay)

**Prerequisites:** P12-3.4

**Technical Notes:**
- Revoke old token on rotation
- Add 5-second grace period for concurrent requests
- Log refresh attempts for security monitoring

---

### Story P12-3.6: Implement Token Revocation on Security Events

As a user,
I want all my tokens invalidated when I change my password,
So that compromised sessions are terminated.

**Acceptance Criteria:**

**Given** a user changes their password
**When** the password change is saved
**Then** all refresh tokens for all user's devices are revoked

**Given** a device is deleted
**When** the deletion completes
**Then** all refresh tokens for that device are revoked within 1 second

**And** access tokens become invalid on next API request (token validation checks revocation)

**Prerequisites:** P12-3.5, P12-2.2

**Technical Notes:**
- Add token revocation to password change flow
- Cascade delete on device removal
- Consider adding user-level "revoke all sessions" option

---

## Epic P12-4: Query-Adaptive Optimization

**Goal:** Enhance the Phase 11 query-adaptive frame selection with batch processing, diversity filtering, and improved UX for re-analysis workflows.

**Priority:** LOW - Independent enhancement, builds on P11 foundation

**FRs Covered:** FR29-FR38

---

### Story P12-4.1: Implement Batch Embedding Generation

As the system,
I want to generate frame embeddings in batches,
So that embedding overhead is reduced by 40%+ compared to sequential processing.

**Acceptance Criteria:**

**Given** a video with 10 frames to embed
**When** embeddings are generated
**Then** frames are processed in batches of 8
**And** total processing time is 40% less than sequential
**And** embedding quality is identical to sequential

**And** batch size is configurable
**And** performance metrics are logged

**Prerequisites:** None (builds on P11-4 infrastructure)

**Technical Notes:**
- Create `BatchEmbedder` service
- Use torch.stack() for batch tensor creation
- Measure and log per-frame overhead reduction

---

### Story P12-4.2: Add Diversity Filtering to Frame Selection

As a user,
I want frame selection to avoid near-duplicate frames,
So that re-analysis uses diverse perspectives of the event.

**Acceptance Criteria:**

**Given** frame embeddings with similarity scores
**When** selecting top-k frames for query
**Then** diversity filter excludes frames with >92% similarity to already-selected frames

**Given** 10 frames where 3 are near-duplicates
**When** selecting 5 frames
**Then** only 1-2 of the duplicates are selected, leaving room for diverse frames

**And** diversity threshold is configurable
**And** filter adds <10ms overhead

**Prerequisites:** P12-4.1

**Technical Notes:**
- Create `DiversityFilter` class
- Use greedy selection: pick highest score, filter similar, repeat
- Log which frames were filtered for transparency

---

### Story P12-4.3: Integrate Quality Scoring in Frame Selection

As the system,
I want frame quality (blur, exposure) to factor into selection,
So that clearer frames are preferred for AI analysis.

**Acceptance Criteria:**

**Given** frames with quality scores from P9-2 implementation
**When** calculating frame selection scores
**Then** final score = (relevance_score * 0.7) + (quality_score * 0.3)

**Given** two frames with equal relevance
**When** one has higher quality score
**Then** higher quality frame is ranked higher

**And** quality weight is configurable
**And** frames with quality < 0.3 are deprioritized regardless of relevance

**Prerequisites:** P12-4.2

**Technical Notes:**
- Extend frame selection to combine relevance and quality
- Use existing quality scoring from P9-2
- Make weights configurable in settings

---

### Story P12-4.4: Add Query Caching and Suggestions

As a user,
I want query results cached and suggestions provided,
So that repeated queries are instant and I can discover useful questions.

**Acceptance Criteria:**

**Given** a query for event X
**When** the same query is made again within 5 minutes
**Then** cached result is returned in <5ms

**Given** an event with smart detection types
**When** I open re-analyze modal
**Then** I see suggested queries based on detection:
- Person detected → "Is this a delivery person?", "What are they carrying?"
- Vehicle detected → "What color is the vehicle?", "Is it parked or moving?"
- Package detected → "What company is the package from?"

**And** query history is shown for quick re-selection
**And** cache entries expire after 5 minutes

**Prerequisites:** P12-4.3

**Technical Notes:**
- Create QueryCache with TTL-based expiration
- Store query→result mappings per event
- Add query suggestions based on event.smart_detection_type

---

### Story P12-4.5: Enhance Re-Analyze Modal with Relevance Scores

As a user,
I want to see relevance scores when re-analyzing,
So that I understand which frames best match my query.

**Acceptance Criteria:**

**Given** I submit a query in re-analyze modal
**When** results are displayed
**Then** I see:
- Selected frames with thumbnails
- Relevance score (0-100) for each frame
- Visual indicator (color gradient based on score)
- Frame timestamp within clip

**Given** single-word query like "dog"
**When** submitted
**Then** query is auto-formatted to "a photo of a dog" for better CLIP matching

**And** A/B toggle: "Compare with uniform selection" shows side-by-side results
**And** selection time (ms) displayed for transparency

**Prerequisites:** P12-4.4

**Technical Notes:**
- Update ReanalyzeModal to display frame scores
- Add query preprocessing for short queries
- Optional: Add comparison mode for validation

---

## FR Coverage Matrix

| FR | Description | Epic | Story |
|----|-------------|------|-------|
| FR1 | Create rules for specific entities | P12-1 | P12-1.1, P12-1.2 |
| FR2 | Entity dropdown in rule UI | P12-1 | P12-1.3 |
| FR3 | Unknown entity (stranger) detection | P12-1 | P12-1.2 |
| FR4 | Combine entity with other conditions | P12-1 | P12-1.2 |
| FR5 | Entity name in rule list | P12-1 | P12-1.3 |
| FR6 | Entity name in push notifications | P12-1 | P12-1.4 |
| FR7 | Entity info in webhook payloads | P12-1 | P12-1.4 |
| FR8 | View rules from entity page | P12-1 | P12-1.5 |
| FR9 | Mobile device registration | P12-2 | P12-2.2 |
| FR10 | Capture platform, name, device ID | P12-2 | P12-2.1, P12-2.2 |
| FR11 | View devices in Settings | P12-2 | P12-2.3 |
| FR12 | Rename devices | P12-2 | P12-2.3 |
| FR13 | Revoke device registrations | P12-2 | P12-2.2, P12-2.3 |
| FR14 | Revocation invalidates tokens | P12-2 | P12-2.2 |
| FR15 | Associate push tokens with devices | P12-2 | P12-2.4 |
| FR16 | Track last_seen timestamp | P12-2 | P12-2.5 |
| FR17 | Flag inactive devices | P12-2 | P12-2.5 |
| FR18 | Request 6-digit pairing code | P12-3 | P12-3.2 |
| FR19 | Pairing codes expire (5 min) | P12-3 | P12-3.1, P12-3.2 |
| FR20 | Confirm codes via dashboard | P12-3 | P12-3.3 |
| FR21 | Exchange code for JWT | P12-3 | P12-3.4 |
| FR22 | JWT includes device_id | P12-3 | P12-3.4 |
| FR23 | Refresh expired tokens | P12-3 | P12-3.5 |
| FR24 | Sliding window extension | P12-3 | P12-3.5 |
| FR25 | Refresh token rotation | P12-3 | P12-3.5 |
| FR26 | Password change invalidates tokens | P12-3 | P12-3.6 |
| FR27 | Rate limiting for pairing | P12-3 | P12-3.2 |
| FR28 | WebSocket pairing notification | P12-3 | P12-3.2, P12-3.3 |
| FR29 | Batch embedding generation | P12-4 | P12-4.1 |
| FR30 | Diversity filtering | P12-4 | P12-4.2 |
| FR31 | Quality scores in selection | P12-4 | P12-4.3 |
| FR32 | Query matching metrics | P12-4 | P12-4.1, P12-4.5 |
| FR33 | Multi-query OR logic | P12-4 | P12-4.4 |
| FR34 | Query suggestions | P12-4 | P12-4.4 |
| FR35 | A/B comparison mode | P12-4 | P12-4.5 |
| FR36 | Query result caching | P12-4 | P12-4.4 |
| FR37 | Relevance scores in modal | P12-4 | P12-4.5 |
| FR38 | Auto-format single-word queries | P12-4 | P12-4.5 |
| FR39 | POST /api/v1/devices | P12-2 | P12-2.2 |
| FR40 | GET /api/v1/devices | P12-2 | P12-2.2 |
| FR41 | PUT /api/v1/devices/{id} | P12-2 | P12-2.2 |
| FR42 | DELETE /api/v1/devices/{id} | P12-2 | P12-2.2 |
| FR43 | POST /mobile/auth/pair | P12-3 | P12-3.2 |
| FR44 | POST /mobile/auth/verify | P12-3 | P12-3.4 |
| FR45 | POST /auth/refresh | P12-3 | P12-3.5 |
| FR46 | PUT /alert-rules/{id} with entity | P12-1 | P12-1.1 |
| FR47 | GET /entities/{id}/alert-rules | P12-1 | P12-1.5 |

**Coverage:** 47/47 FRs mapped (100%)

---

## Summary

Phase 12 is broken down into 4 epics with 21 total stories:

| Epic | Stories | Priority | Dependencies |
|------|---------|----------|--------------|
| P12-1: Entity-Based Alert Rules | 5 | HIGH | None |
| P12-2: Mobile Device Registration | 5 | MEDIUM | None |
| P12-3: Mobile Authentication & Pairing | 6 | MEDIUM | P12-2 |
| P12-4: Query-Adaptive Optimization | 5 | LOW | None (builds on P11) |

**Recommended Execution Order:**
1. P12-1 (independent, highest value)
2. P12-2 → P12-3 (sequential dependency)
3. P12-4 (independent, can parallel with P12-2/P12-3)

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans._

_Created: 2025-12-26_
