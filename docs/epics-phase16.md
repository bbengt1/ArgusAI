# ArgusAI Phase 16 - Epic Breakdown

**Author:** Brent
**Date:** 2026-01-01
**Phase:** 16 - User Experience & Access Management
**Total Stories:** 28

---

## Overview

This document provides the complete epic and story breakdown for ArgusAI Phase 16, decomposing the requirements from [PRD-phase16.md](./PRD-phase16.md) into implementable stories.

**Epic Summary:**

| Epic | Title | Stories | Priority | GitHub Issue |
|------|-------|---------|----------|--------------|
| P16-1 | User Management & Invitations | 7 | P2 | #308 |
| P16-2 | Live Camera Streaming | 5 | P2 | #336 |
| P16-3 | Entity Metadata Editing | 4 | P2 | #338 |
| P16-4 | Entity Assignment UX | 3 | P2 | #337 |
| P16-5 | Active Sessions Management | 5 | P3 | #342 |
| P16-6 | Multi-Entity Events | 4 | P3 | #302 |

**MVP Epics:** P16-1 through P16-4 (19 stories)
**Growth Epics:** P16-5 and P16-6 (9 stories)

---

## Functional Requirements Inventory

### User Management & Authentication (FR1-FR9)
- FR1: Administrators can create new user accounts with email and role
- FR2: System generates secure temporary password for new users
- FR3: Administrators can optionally send email invitation
- FR4: New users required to change password on first login
- FR5: Administrators can assign roles (admin, operator, viewer)
- FR6: Administrators can enable/disable user accounts
- FR7: Administrators can delete user accounts
- FR8: Users can view their profile information
- FR9: System logs user management actions for audit

### Session Management (FR10-FR15)
- FR10: Users can view list of active sessions
- FR11: Users can identify current session
- FR12: Users can revoke individual sessions
- FR13: Users can revoke all sessions except current
- FR14: System enforces maximum concurrent sessions
- FR15: Sessions expire after inactivity period

### Live Camera Streaming (FR16-FR22)
- FR16: Users can view live video from Protect cameras
- FR17: Live stream displays with <3 second latency
- FR18: Users can select stream quality
- FR19: Users can view stream in fullscreen
- FR20: System falls back to snapshot if stream unavailable
- FR21: Multiple cameras can stream simultaneously
- FR22: Live view button on Protect camera cards

### Entity Management (FR23-FR29)
- FR23: Users can edit entity name
- FR24: Users can change entity type
- FR25: Users can toggle VIP status
- FR26: Users can toggle blocked status
- FR27: Users can add/edit notes
- FR28: Entity edits saved immediately with confirmation
- FR29: Entity views update immediately after edit

### Entity Assignment UX (FR30-FR35)
- FR30: Assignment displays confirmation dialog
- FR31: Dialog explains re-classification will occur
- FR32: Dialog shows estimated API cost
- FR33: User can proceed or cancel
- FR34: User can opt-out via "Don't show again"
- FR35: Preference stored in localStorage

### Multi-Entity Events (FR36-FR40)
- FR36: Events can be associated with multiple entities
- FR37: Event cards display multiple entity badges
- FR38: Entity detail shows co-occurring events
- FR39: Assignment UI supports multi-select
- FR40: Alert rules trigger on any matched entity

### Camera Connection Testing (FR41-FR43)
- FR41: Users can test RTSP connection before saving
- FR42: Test returns success/failure with details
- FR43: Test does not persist configuration

---

## FR Coverage Map

| FR Range | Epic | Coverage |
|----------|------|----------|
| FR1-FR9 | P16-1: User Management | Stories 1.1-1.7 |
| FR10-FR15 | P16-5: Active Sessions | Stories 5.1-5.5 |
| FR16-FR22 | P16-2: Live Streaming | Stories 2.1-2.5 |
| FR23-FR29 | P16-3: Entity Editing | Stories 3.1-3.4 |
| FR30-FR35 | P16-4: Entity Assignment UX | Stories 4.1-4.3 |
| FR36-FR40 | P16-6: Multi-Entity Events | Stories 6.1-6.4 |
| FR41-FR43 | Deferred | Not in Phase 16 scope |

---

## Epic P16-1: User Management & Invitations

**Goal:** Enable administrators to create and manage multiple user accounts with role-based permissions, transforming ArgusAI from single-user to multi-user.

**GitHub:** [#308](https://github.com/project-argusai/ArgusAI/issues/308)
**Covers:** FR1-FR9

---

### Story P16-1.1: Extend User Model for Multi-User Support

**As an** administrator,
**I want** the system to support multiple users with roles,
**So that** I can invite family members with appropriate access levels.

**Acceptance Criteria:**

**Given** the existing User model in the database
**When** the migration runs
**Then** the users table has new columns:
- `role` (TEXT, NOT NULL, default 'viewer')
- `email` (TEXT, UNIQUE, nullable)
- `must_change_password` (BOOLEAN, default FALSE)
- `invited_by` (TEXT, FK to users.id, nullable)
- `invited_at` (TIMESTAMP, nullable)
- `last_login_at` (TIMESTAMP, nullable)

**And** existing admin user is set to role='admin'
**And** role values are constrained to: 'admin', 'operator', 'viewer'

**Prerequisites:** None (foundational story)

**Technical Notes:**
- Create Alembic migration: `alembic revision --autogenerate -m "add_user_role_columns"`
- Update `backend/app/models/user.py` with new fields
- Add UserRole enum to `backend/app/schemas/user.py`
- Ensure backward compatibility - existing user retains access

---

### Story P16-1.2: Create User Management API Endpoints

**As an** administrator,
**I want** API endpoints to manage users,
**So that** the frontend can provide user management UI.

**Acceptance Criteria:**

**Given** I am authenticated as an admin user
**When** I call `GET /api/v1/users`
**Then** I receive a list of all users with fields: id, username, email, role, is_active, created_at, last_login_at

**Given** I am authenticated as an admin user
**When** I call `POST /api/v1/users` with `{"username": "newuser", "email": "new@example.com", "role": "viewer"}`
**Then** a new user is created with `must_change_password=true`
**And** a temporary password is generated (16 chars, cryptographically random)
**And** the response includes the temporary password (one-time display)

**Given** I am authenticated as a non-admin user
**When** I call any `/api/v1/users` endpoint
**Then** I receive 403 Forbidden

**And** `PUT /api/v1/users/{id}` allows updating: email, role, is_active
**And** `DELETE /api/v1/users/{id}` soft-deletes or hard-deletes the user
**And** `POST /api/v1/users/{id}/reset-password` generates new temp password

**Prerequisites:** P16-1.1

**Technical Notes:**
- Create `backend/app/api/v1/users.py` router
- Create `backend/app/services/user_service.py`
- Use `secrets.token_urlsafe(16)` for temp password generation
- Add to `backend/app/api/v1/__init__.py` router registration
- All endpoints require `@require_role(["admin"])` decorator

---

### Story P16-1.3: Implement Role-Based Authorization Middleware

**As a** developer,
**I want** a reusable role authorization decorator,
**So that** endpoints can easily enforce role requirements.

**Acceptance Criteria:**

**Given** a decorator `@require_role(["admin", "operator"])`
**When** applied to an endpoint
**Then** requests from users with matching role proceed normally
**And** requests from users without matching role receive 403 with `{"detail": "Insufficient permissions", "error_code": "INSUFFICIENT_PERMISSIONS"}`

**Given** a viewer user
**When** they access an operator-only endpoint
**Then** they receive 403 Forbidden

**And** the decorator works with FastAPI's dependency injection
**And** the decorator preserves function metadata (for OpenAPI docs)

**Prerequisites:** P16-1.1

**Technical Notes:**
- Create `backend/app/middleware/authorization.py`
- Implement as FastAPI dependency, not middleware (for per-route control)
- Pattern: `current_user: User = Depends(require_role(["admin"]))`
- Update existing endpoints as needed (most stay public or auth-only)

---

### Story P16-1.4: Create User Management UI Page

**As an** administrator,
**I want** a Settings page to manage users,
**So that** I can create, edit, and delete users through the UI.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to Settings > Security > Users
**Then** I see a table of all users with columns: Username, Email, Role, Status, Last Login, Actions

**Given** the user table
**When** I click "Add User" button
**Then** a modal opens with fields: Username (required), Email (optional), Role (dropdown: admin/operator/viewer)

**Given** I fill in the Add User form and click Create
**When** the user is created successfully
**Then** the modal shows the temporary password with a "Copy" button
**And** a warning: "This password will only be shown once"
**And** the user list refreshes to show the new user

**Given** I click the Edit action on a user row
**When** the edit modal opens
**Then** I can change: Email, Role, Active status
**And** I can click "Reset Password" to generate a new temp password

**Given** I click Delete on a user row
**When** I confirm the deletion
**Then** the user is removed from the list
**And** a toast confirms "User deleted successfully"

**And** the Users section only appears for admin users
**And** non-admin users don't see the Users menu item

**Prerequisites:** P16-1.2, P16-1.3

**Technical Notes:**
- Create `frontend/components/settings/UserManagement.tsx`
- Create `frontend/components/users/UserCreateModal.tsx`
- Create `frontend/components/users/UserEditModal.tsx`
- Add to Settings page under Security tab
- Use existing shadcn/ui Table, Dialog, Form components
- Create `frontend/hooks/useUsers.ts` with TanStack Query

---

### Story P16-1.5: Force Password Change on First Login

**As a** new user,
**I want** to be required to change my temporary password,
**So that** my account is secured with a password only I know.

**Acceptance Criteria:**

**Given** I log in with a temporary password
**When** my account has `must_change_password=true`
**Then** I am redirected to a "Change Password" page before accessing any other page

**Given** I am on the Change Password page
**When** I enter a new password meeting requirements (8+ chars, 1 upper, 1 lower, 1 number)
**Then** my password is updated
**And** `must_change_password` is set to false
**And** I am redirected to the dashboard

**Given** I try to navigate away from Change Password page
**When** `must_change_password=true`
**Then** I am redirected back to Change Password page

**And** the Change Password page shows password requirements
**And** a password strength indicator shows weak/medium/strong

**Prerequisites:** P16-1.1, P16-1.2

**Technical Notes:**
- Create `frontend/app/change-password/page.tsx`
- Add check in `frontend/components/layout/AuthGuard.tsx` or similar
- Update `backend/app/api/v1/auth.py` login endpoint to return `must_change_password` flag
- Create `PUT /api/v1/auth/change-password` endpoint

---

### Story P16-1.6: User Audit Logging

**As an** administrator,
**I want** user management actions logged,
**So that** I can review who made changes and when.

**Acceptance Criteria:**

**Given** an admin creates a new user
**When** the action completes
**Then** an audit log entry is created with: action='create_user', user_id (who did it), target_user_id (who was affected), details (JSON with username, role), ip_address, timestamp

**Given** an admin changes a user's role
**When** the action completes
**Then** an audit log entry records: action='change_role', details with old_role and new_role

**And** audit logs are created for: create_user, update_user, delete_user, change_role, reset_password, disable_user, enable_user

**And** audit logs cannot be modified or deleted via API

**Prerequisites:** P16-1.2

**Technical Notes:**
- Create `backend/app/models/user_audit_log.py`
- Create migration for user_audit_log table
- Add audit logging calls in UserService methods
- Consider: expose read-only endpoint `GET /api/v1/users/audit-log` for admin viewing (optional, can defer to future)

---

### Story P16-1.7: Email Invitation Flow (Optional)

**As an** administrator,
**I want** to optionally send email invitations,
**So that** new users receive their credentials automatically.

**Acceptance Criteria:**

**Given** SMTP is configured in settings
**When** I create a user with "Send invitation email" checked
**Then** an email is sent to the user's email address containing: username, temporary password, login URL

**Given** SMTP is not configured
**When** I try to check "Send invitation email"
**Then** the checkbox is disabled with tooltip "Configure SMTP in Settings > Email to enable"

**Given** SMTP is configured
**When** email sending fails
**Then** the user is still created
**And** an error toast shows "User created but email failed to send"
**And** the temporary password is still displayed in the modal

**And** invitation emails use a professional HTML template
**And** emails include ArgusAI branding

**Prerequisites:** P16-1.4

**Technical Notes:**
- Create `backend/app/services/email_service.py`
- Use `aiosmtplib` for async email sending
- Create email template in `backend/app/templates/invitation_email.html`
- Add SMTP settings to SystemSettings model
- Add SMTP config UI to Settings > Email section (can reuse existing notification settings pattern)
- This story is OPTIONAL - can be deferred if time-constrained

---

## Epic P16-2: Live Camera Streaming

**Goal:** Enable users to view live video feeds from UniFi Protect cameras directly in the ArgusAI dashboard without switching to the Protect app.

**GitHub:** [#336](https://github.com/project-argusai/ArgusAI/issues/336)
**Covers:** FR16-FR22

---

### Story P16-2.1: Research and Design Streaming Approach

**As a** developer,
**I want** to understand uiprotect streaming capabilities,
**So that** I can implement the best streaming approach.

**Acceptance Criteria:**

**Given** the uiprotect library documentation
**When** I research streaming options
**Then** I document findings for: WebSocket streaming, RTSP proxy, HLS conversion, MJPEG fallback

**Given** the research findings
**When** I evaluate options against requirements (<3s latency, browser compatibility)
**Then** I recommend an approach with rationale

**And** create a technical design document in `docs/sprint-artifacts/p16-2-1-streaming-design.md`
**And** document: chosen approach, libraries needed, bandwidth estimates, browser support matrix

**Prerequisites:** None

**Technical Notes:**
- Check uiprotect for `get_camera_video()`, WebRTC support, or RTSP URL access
- Evaluate: ffmpeg for transcoding, ws for WebSocket, hls.js for HLS playback
- Consider Cloudflare Stream or similar if direct streaming is complex
- Output: Design document with recommended approach

---

### Story P16-2.2: Implement Backend Stream Proxy Service

**As a** backend developer,
**I want** a service to proxy camera streams,
**So that** the frontend can display live video.

**Acceptance Criteria:**

**Given** a valid Protect controller and camera
**When** I call `StreamProxyService.get_stream_url(controller_id, camera_id)`
**Then** I receive stream connection info: url, type (websocket/hls/mjpeg), quality options

**Given** the chosen streaming approach (from P16-2.1)
**When** the proxy endpoint is called
**Then** video data is streamed to the client with <3 second latency

**And** `GET /api/v1/protect/controllers/{id}/cameras/{cam}/stream` returns stream info
**And** `GET /api/v1/protect/controllers/{id}/cameras/{cam}/stream/snapshot` returns current frame JPEG
**And** authentication is required for all stream endpoints
**And** concurrent stream limit is enforced (default 10, configurable)

**Prerequisites:** P16-2.1

**Technical Notes:**
- Create `backend/app/services/stream_proxy_service.py`
- Add routes to `backend/app/api/v1/protect.py`
- Implement based on design from P16-2.1
- Handle stream errors gracefully (camera offline, network issues)
- Add STREAM_MAX_CONCURRENT env var

---

### Story P16-2.3: Create LiveStreamPlayer Frontend Component

**As a** user,
**I want** a video player component for live streams,
**So that** I can watch camera feeds in the browser.

**Acceptance Criteria:**

**Given** the LiveStreamPlayer component with controllerId and cameraId props
**When** mounted
**Then** it connects to the stream endpoint and displays video

**Given** stream quality options are available
**When** I click the quality selector
**Then** I can choose between Low, Medium, High quality
**And** the stream reconnects at the new quality

**Given** the player is showing video
**When** I click the fullscreen button
**Then** the video expands to fullscreen mode
**And** pressing Escape exits fullscreen

**Given** the stream fails to connect
**When** after 5 seconds
**Then** a fallback message shows "Stream unavailable"
**And** a "Retry" button is available
**And** snapshot fallback shows latest frame with 2-second refresh

**And** player shows loading spinner while connecting
**And** player has mute/unmute toggle (muted by default)
**And** player displays camera name overlay

**Prerequisites:** P16-2.2

**Technical Notes:**
- Create `frontend/components/streaming/LiveStreamPlayer.tsx`
- Create `frontend/components/streaming/StreamQualitySelector.tsx`
- Use appropriate player library based on stream type (hls.js, native video, etc.)
- Handle WebSocket reconnection on disconnect
- Use shadcn/ui Popover for quality selector

---

### Story P16-2.4: Add Live View Button to Camera Cards

**As a** user,
**I want** a "Live View" button on Protect camera cards,
**So that** I can quickly access live streams.

**Acceptance Criteria:**

**Given** I am on the Cameras page viewing Protect cameras
**When** I see a Protect camera card
**Then** there is a "Live View" button with a video icon

**Given** I click the Live View button
**When** the action triggers
**Then** a modal opens with the LiveStreamPlayer component
**And** the modal shows the camera name in the header
**And** the modal can be closed with X button or Escape key

**Given** the camera is offline or stream unavailable
**When** I click Live View
**Then** the modal opens with the snapshot fallback view
**And** a message indicates "Live stream unavailable - showing snapshots"

**And** Live View button only appears on Protect cameras (not RTSP/USB)
**And** button is disabled if user is viewer role and live view requires operator+ (optional restriction)

**Prerequisites:** P16-2.3

**Technical Notes:**
- Update `frontend/components/cameras/CameraCard.tsx` (or Protect-specific card)
- Create `frontend/components/streaming/LiveStreamModal.tsx`
- Add video icon from lucide-react
- Check camera source_type === 'protect' before showing button

---

### Story P16-2.5: Implement Concurrent Stream Limiting

**As a** system administrator,
**I want** concurrent streams limited,
**So that** bandwidth is not exhausted.

**Acceptance Criteria:**

**Given** 10 streams are currently active (default limit)
**When** a user tries to open an 11th stream
**Then** they receive error "Maximum concurrent streams reached. Please close another stream first."

**Given** a stream is closed (modal closed or tab navigated away)
**When** the WebSocket disconnects
**Then** the stream count decrements
**And** another user can now open a stream

**Given** STREAM_MAX_CONCURRENT is set to 5
**When** the system starts
**Then** the limit is enforced at 5 concurrent streams

**And** admin can see current stream count in Settings > System (optional)

**Prerequisites:** P16-2.2

**Technical Notes:**
- Add stream counting in StreamProxyService
- Use Redis or in-memory counter for tracking
- Return 429 Too Many Requests when limit exceeded
- Clean up count on WebSocket disconnect

---

## Epic P16-3: Entity Metadata Editing

**Goal:** Allow users to edit entity properties (name, type, VIP status, blocked status, notes) after automatic creation.

**GitHub:** [#338](https://github.com/project-argusai/ArgusAI/issues/338)
**Covers:** FR23-FR29

---

### Story P16-3.1: Create Entity Update API Endpoint

**As a** backend developer,
**I want** an endpoint to update entity metadata,
**So that** users can edit entity properties.

**Acceptance Criteria:**

**Given** a valid entity ID
**When** I call `PUT /api/v1/context/entities/{id}` with `{"name": "Mail Carrier"}`
**Then** the entity name is updated
**And** the response returns the updated entity object

**Given** partial updates
**When** I only send `{"is_vip": true}`
**Then** only is_vip is updated, other fields unchanged

**Given** invalid entity_type value
**When** I send `{"entity_type": "invalid"}`
**Then** I receive 422 with validation error

**And** updatable fields: name, entity_type, is_vip, is_blocked, notes
**And** entity_type must be: person, vehicle, unknown
**And** name max length: 255 characters
**And** notes max length: 2000 characters
**And** updated_at timestamp is set automatically
**And** requires authenticated user (any role can edit)

**Prerequisites:** None

**Technical Notes:**
- Add PUT route to `backend/app/api/v1/context.py`
- Create `EntityUpdate` schema in `backend/app/schemas/entity.py`
- Update RecognizedEntity model's updated_at on save
- Return full entity object after update

---

### Story P16-3.2: Create EntityEditModal Component

**As a** user,
**I want** a modal to edit entity properties,
**So that** I can correct or enhance entity information.

**Acceptance Criteria:**

**Given** I open the EntityEditModal for an entity
**When** the modal renders
**Then** I see form fields for: Name (text), Type (select: Person/Vehicle/Unknown), VIP (toggle), Blocked (toggle), Notes (textarea)
**And** fields are pre-filled with current entity values

**Given** I change the Name field and click Save
**When** the save completes
**Then** a success toast shows "Entity updated"
**And** the modal closes
**And** the entity list/detail view refreshes

**Given** I click Cancel or press Escape
**When** the modal closes
**Then** no changes are saved

**And** the modal shows the entity thumbnail at the top
**And** form validation shows inline errors (e.g., name too long)
**And** Save button is disabled while saving (loading state)

**Prerequisites:** P16-3.1

**Technical Notes:**
- Create `frontend/components/entities/EntityEditModal.tsx`
- Use React Hook Form with Zod validation
- Use shadcn/ui Dialog, Input, Select, Switch, Textarea
- Create `frontend/hooks/useUpdateEntity.ts` mutation hook

---

### Story P16-3.3: Add Edit Button to Entity Card

**As a** user,
**I want** an Edit button on entity cards,
**So that** I can quickly access the edit modal.

**Acceptance Criteria:**

**Given** I am viewing the Entities page
**When** I see an entity card
**Then** there is an Edit button (pencil icon) in the card actions

**Given** I click the Edit button
**When** the click event fires
**Then** the EntityEditModal opens for that entity
**And** clicking Edit does NOT open the entity detail modal (stopPropagation)

**And** Edit button has tooltip "Edit entity"
**And** Edit button is visible on hover (or always visible on mobile)

**Prerequisites:** P16-3.2

**Technical Notes:**
- Update `frontend/components/entities/EntityCard.tsx`
- Add Edit button alongside existing "Add Alert" button
- Use Pencil icon from lucide-react
- Ensure stopPropagation prevents card click

---

### Story P16-3.4: Add Edit Button to Entity Detail Modal

**As a** user,
**I want** to edit an entity from its detail modal,
**So that** I can make changes while viewing entity details.

**Acceptance Criteria:**

**Given** I have the EntityDetailModal open
**When** I click the Edit button in the header
**Then** the EntityEditModal opens (as nested modal or replaces content)

**Given** I save changes in EntityEditModal from detail context
**When** the save completes
**Then** the EntityDetailModal refreshes to show updated values
**And** the entity remains selected

**And** Edit button is positioned in modal header next to close button
**And** works on both desktop and mobile layouts

**Prerequisites:** P16-3.2, P16-3.3

**Technical Notes:**
- Update `frontend/components/entities/EntityDetailModal.tsx`
- Add Edit button to modal header
- Handle modal stacking or content replacement
- Invalidate entity query on successful edit

---

## Epic P16-4: Entity Assignment UX

**Goal:** Add confirmation dialog when assigning events to entities, warning users about AI re-classification that will occur.

**GitHub:** [#337](https://github.com/project-argusai/ArgusAI/issues/337)
**Covers:** FR30-FR35

---

### Story P16-4.1: Create Entity Assignment Confirmation Dialog

**As a** user,
**I want** a confirmation dialog when assigning events to entities,
**So that** I understand the re-classification will occur.

**Acceptance Criteria:**

**Given** I select an entity to assign an event to
**When** I confirm the selection
**Then** a confirmation dialog appears before the assignment

**Given** the confirmation dialog is shown
**When** I read the content
**Then** I see: "Assigning this event to [Entity Name] will trigger AI re-classification"
**And** I see: "This will update the event description based on the entity context"
**And** I see estimated API cost (e.g., "~$0.002 for re-analysis")

**Given** I click "Confirm" in the dialog
**When** the action completes
**Then** the event is assigned to the entity
**And** re-classification is triggered (existing workflow)

**Given** I click "Cancel" in the dialog
**When** the dialog closes
**Then** no assignment occurs
**And** I return to entity selection

**Prerequisites:** None

**Technical Notes:**
- Create `frontend/components/entities/EntityAssignConfirmDialog.tsx`
- Use shadcn/ui AlertDialog component
- Calculate estimated cost from current AI provider settings
- Integrate into existing EntitySelectModal flow

---

### Story P16-4.2: Add "Don't Show Again" Preference

**As a** user,
**I want** to disable the confirmation dialog,
**So that** I can assign entities quickly without repeated warnings.

**Acceptance Criteria:**

**Given** the confirmation dialog is shown
**When** I check "Don't show this warning again"
**Then** a checkbox is checked

**Given** I confirm with checkbox checked
**When** assignment completes
**Then** the preference is saved to localStorage
**And** future assignments skip the confirmation dialog

**Given** I have previously checked "Don't show again"
**When** I assign an event to an entity
**Then** the confirmation dialog is skipped
**And** assignment proceeds directly

**And** the preference key is `argusai_skip_entity_assign_warning`
**And** preference persists across browser sessions

**Prerequisites:** P16-4.1

**Technical Notes:**
- Add checkbox to EntityAssignConfirmDialog
- Use localStorage for persistence
- Check localStorage before showing dialog
- Consider adding reset option in Settings (optional)

---

### Story P16-4.3: Display Re-classification Status

**As a** user,
**I want** to see when re-classification is in progress,
**So that** I know the event is being updated.

**Acceptance Criteria:**

**Given** I confirm entity assignment
**When** re-classification begins
**Then** a loading indicator shows on the event card
**And** text shows "Re-classifying..."

**Given** re-classification completes
**When** the event is updated
**Then** the loading indicator disappears
**And** the event description updates to new value
**And** a toast shows "Event re-classified successfully"

**Given** re-classification fails
**When** an error occurs
**Then** an error toast shows "Re-classification failed"
**And** the event retains its original description
**And** the entity assignment is still saved

**Prerequisites:** P16-4.1

**Technical Notes:**
- Add loading state to EventCard for re-classification
- Use existing event update subscription (WebSocket) or polling
- Ensure entity link is saved even if re-classification fails

---

## Epic P16-5: Active Sessions Management

**Goal:** Enable users to view and manage their active login sessions for security visibility.

**GitHub:** [#342](https://github.com/project-argusai/ArgusAI/issues/342)
**Covers:** FR10-FR15

---

### Story P16-5.1: Create Session Model and Tracking

**As a** backend developer,
**I want** sessions tracked in the database,
**So that** users can view and manage them.

**Acceptance Criteria:**

**Given** a user logs in successfully
**When** a JWT is issued
**Then** a Session record is created with: id, user_id, token_hash (SHA256), device_info (parsed User-Agent), ip_address, created_at, expires_at

**Given** an authenticated request is made
**When** the middleware processes it
**Then** the session's last_active_at is updated

**Given** a session expires (based on expires_at)
**When** cleanup runs
**Then** the session record is deleted

**And** token_hash is SHA256 of JWT (never store raw token)
**And** device_info is parsed from User-Agent (e.g., "Chrome on macOS")
**And** sessions table has indexes on user_id, token_hash, expires_at

**Prerequisites:** None

**Technical Notes:**
- Create `backend/app/models/session.py`
- Create migration for sessions table
- Create `backend/app/services/session_service.py`
- Update auth login to create session
- Add middleware to update last_active_at
- Use user-agents library for User-Agent parsing

---

### Story P16-5.2: Create Session API Endpoints

**As a** user,
**I want** API endpoints to view and manage sessions,
**So that** I can see where I'm logged in and revoke access.

**Acceptance Criteria:**

**Given** I am authenticated
**When** I call `GET /api/v1/auth/sessions`
**Then** I receive a list of my active sessions with: id, device_info, ip_address, created_at, last_active_at, is_current

**Given** I call `DELETE /api/v1/auth/sessions/{id}`
**When** the session belongs to me
**Then** that session is deleted
**And** any request using that session's token receives 401

**Given** I call `DELETE /api/v1/auth/sessions`
**When** the request completes
**Then** all my sessions EXCEPT current are deleted
**And** response shows count of revoked sessions

**And** is_current is true for the session matching current request's token
**And** cannot delete another user's sessions
**And** sessions ordered by last_active_at descending

**Prerequisites:** P16-5.1

**Technical Notes:**
- Add routes to `backend/app/api/v1/auth.py`
- Compare token_hash to identify current session
- Cascade invalidation: deleted session = invalid token

---

### Story P16-5.3: Create Active Sessions UI

**As a** user,
**I want** to see my active sessions in Settings,
**So that** I can review where I'm logged in.

**Acceptance Criteria:**

**Given** I navigate to Settings > Security > Active Sessions
**When** the page loads
**Then** I see a list of my sessions showing: Device/Browser, IP Address, Last Active (relative time), "Current" badge for current session

**Given** I see a session that isn't current
**When** I click "Sign Out" on that row
**Then** a confirmation dialog asks "Sign out this device?"
**And** confirming removes the session from the list
**And** a toast shows "Session revoked"

**Given** I have multiple sessions
**When** I click "Sign out all other devices"
**Then** a confirmation dialog asks "Sign out all other devices?"
**And** confirming removes all non-current sessions
**And** a toast shows "X sessions revoked"

**And** current session row is highlighted and cannot be revoked
**And** empty state shows "No other active sessions" when only current exists

**Prerequisites:** P16-5.2

**Technical Notes:**
- Create `frontend/components/settings/ActiveSessions.tsx`
- Create `frontend/components/sessions/SessionCard.tsx`
- Add to Settings page under Security tab
- Create `frontend/hooks/useSessions.ts`
- Use formatDistanceToNow for relative times

---

### Story P16-5.4: Enforce Maximum Concurrent Sessions

**As an** administrator,
**I want** concurrent sessions limited,
**So that** account sharing is controlled.

**Acceptance Criteria:**

**Given** a user has 10 active sessions (default limit)
**When** they try to log in on an 11th device
**Then** login succeeds
**And** the oldest session (by last_active_at) is automatically revoked
**And** a warning shows "Maximum sessions reached. Your oldest session was signed out."

**Given** SESSION_MAX_PER_USER is set to 5
**When** the system starts
**Then** the limit is enforced at 5 sessions

**And** admin accounts may have higher limits (optional)
**And** session limit is configurable in Settings > Security (optional)

**Prerequisites:** P16-5.1, P16-5.2

**Technical Notes:**
- Add limit check in login flow
- Revoke oldest session if limit exceeded
- Add SESSION_MAX_PER_USER env var (default 10)
- Return warning in login response

---

### Story P16-5.5: Invalidate Sessions on Password Change

**As a** security-conscious user,
**I want** all sessions invalidated when I change my password,
**So that** any compromised sessions are terminated.

**Acceptance Criteria:**

**Given** I change my password successfully
**When** the password change completes
**Then** all my sessions EXCEPT current are invalidated

**Given** I have another device logged in
**When** my password changes
**Then** that device receives 401 on next request
**And** they must re-authenticate with the new password

**And** current session remains valid (user stays logged in)
**And** audit log records "password_changed" with session_cleanup count

**Prerequisites:** P16-5.1, P16-1.5

**Technical Notes:**
- Update password change endpoint to call session cleanup
- SessionService.revoke_all_except_current()
- Include session count in response

---

## Epic P16-6: Multi-Entity Events

**Goal:** Support events being associated with multiple entities (e.g., two people walking together).

**GitHub:** [#302](https://github.com/project-argusai/ArgusAI/issues/302)
**Covers:** FR36-FR40

---

### Story P16-6.1: Research Multi-Entity Data Model

**As a** developer,
**I want** to understand the best approach for multi-entity events,
**So that** I can implement it correctly.

**Acceptance Criteria:**

**Given** the current data model (matched_entity_ids as JSON string)
**When** I evaluate options
**Then** I document pros/cons of: keeping JSON field vs junction table

**Given** the research findings
**When** I recommend an approach
**Then** I justify based on: query performance, backward compatibility, complexity

**And** create design document in `docs/sprint-artifacts/p16-6-1-multi-entity-design.md`
**And** include migration strategy if schema changes

**Prerequisites:** None

**Technical Notes:**
- Current: `events.matched_entity_ids` is JSON string `["uuid1", "uuid2"]`
- Option A: Keep JSON, update parsing logic
- Option B: Create event_entities junction table
- Consider: How are alerts triggered? How is entity detail page queried?

---

### Story P16-6.2: Update Backend for Multi-Entity Support

**As a** backend developer,
**I want** the API to support multiple entities per event,
**So that** the frontend can display them.

**Acceptance Criteria:**

**Given** the chosen data model (from P16-6.1)
**When** an event has multiple matched entities
**Then** `GET /api/v1/events/{id}` returns all matched entities

**Given** entity assignment
**When** I assign an event to an additional entity
**Then** it is added to the event's entity list (not replaced)

**Given** an event with entities ["A", "B"]
**When** I remove entity "A"
**Then** only entity "B" remains associated

**And** event list endpoint includes matched_entities array
**And** entity detail endpoint shows events where entity is one of multiple

**Prerequisites:** P16-6.1

**Technical Notes:**
- Update event schemas to return matched_entities as array of entity summaries
- Update entity assignment endpoint for add/remove semantics
- Ensure backward compatibility with existing single-entity events

---

### Story P16-6.3: Update Event Cards for Multiple Entities

**As a** user,
**I want** to see all matched entities on event cards,
**So that** I know who/what was detected.

**Acceptance Criteria:**

**Given** an event has multiple matched entities
**When** I view the event card
**Then** I see badges for each entity (max 3 visible, "+N more" if exceeded)

**Given** I click on an entity badge
**When** the click handler fires
**Then** the entity detail modal opens for that entity

**Given** an event has no matched entities
**When** I view the event card
**Then** no entity badges are shown (existing behavior)

**And** entity badges show entity name or type icon
**And** badges are styled consistently with existing entity UI

**Prerequisites:** P16-6.2

**Technical Notes:**
- Update `frontend/components/events/EventCard.tsx`
- Add EntityBadge component or reuse existing
- Handle overflow gracefully (3 + "+2 more")

---

### Story P16-6.4: Update Entity Assignment for Multi-Select

**As a** user,
**I want** to assign events to multiple entities,
**So that** I can correctly categorize group events.

**Acceptance Criteria:**

**Given** I open entity assignment for an event
**When** the EntitySelectModal shows
**Then** I can select multiple entities (checkboxes instead of radio)

**Given** I have selected 2 entities
**When** I click Confirm
**Then** the event is associated with both entities
**And** re-classification runs with context from both entities

**Given** an event already has entities assigned
**When** I open assignment
**Then** existing entities are pre-selected
**And** I can add or remove entities

**And** "Select All Visible" option for bulk selection (optional)
**And** confirmation dialog mentions all selected entities

**Prerequisites:** P16-6.2, P16-4.1

**Technical Notes:**
- Update EntitySelectModal for multi-select mode
- Pass array of entity IDs to assignment endpoint
- Update confirmation dialog text for multiple entities

---

## FR Coverage Matrix

| FR | Description | Epic | Story |
|----|-------------|------|-------|
| FR1 | Create user accounts | P16-1 | 1.2, 1.4 |
| FR2 | Generate temp password | P16-1 | 1.2 |
| FR3 | Send email invitation | P16-1 | 1.7 |
| FR4 | Force password change | P16-1 | 1.5 |
| FR5 | Assign roles | P16-1 | 1.1, 1.2, 1.4 |
| FR6 | Enable/disable users | P16-1 | 1.2, 1.4 |
| FR7 | Delete users | P16-1 | 1.2, 1.4 |
| FR8 | View profile | P16-1 | 1.4 |
| FR9 | Audit logging | P16-1 | 1.6 |
| FR10 | View sessions | P16-5 | 5.2, 5.3 |
| FR11 | Identify current session | P16-5 | 5.2, 5.3 |
| FR12 | Revoke individual session | P16-5 | 5.2, 5.3 |
| FR13 | Revoke all except current | P16-5 | 5.2, 5.3 |
| FR14 | Enforce session limit | P16-5 | 5.4 |
| FR15 | Session expiry | P16-5 | 5.1 |
| FR16 | View live video | P16-2 | 2.2, 2.3, 2.4 |
| FR17 | <3s latency | P16-2 | 2.1, 2.2 |
| FR18 | Quality selection | P16-2 | 2.3 |
| FR19 | Fullscreen mode | P16-2 | 2.3 |
| FR20 | Snapshot fallback | P16-2 | 2.3, 2.4 |
| FR21 | Multiple streams | P16-2 | 2.5 |
| FR22 | Live view button | P16-2 | 2.4 |
| FR23 | Edit entity name | P16-3 | 3.1, 3.2 |
| FR24 | Change entity type | P16-3 | 3.1, 3.2 |
| FR25 | Toggle VIP status | P16-3 | 3.1, 3.2 |
| FR26 | Toggle blocked status | P16-3 | 3.1, 3.2 |
| FR27 | Add/edit notes | P16-3 | 3.1, 3.2 |
| FR28 | Immediate save | P16-3 | 3.1, 3.2 |
| FR29 | Immediate UI update | P16-3 | 3.2, 3.3, 3.4 |
| FR30 | Confirmation dialog | P16-4 | 4.1 |
| FR31 | Re-classification warning | P16-4 | 4.1 |
| FR32 | Show API cost | P16-4 | 4.1 |
| FR33 | Proceed or cancel | P16-4 | 4.1 |
| FR34 | Don't show again | P16-4 | 4.2 |
| FR35 | localStorage preference | P16-4 | 4.2 |
| FR36 | Multiple entities per event | P16-6 | 6.2 |
| FR37 | Multiple entity badges | P16-6 | 6.3 |
| FR38 | Co-occurring events | P16-6 | 6.2 |
| FR39 | Multi-select assignment | P16-6 | 6.4 |
| FR40 | Alert on any entity | P16-6 | 6.2 |
| FR41-43 | Camera test | Deferred | - |

---

## Summary

**Phase 16 Epic Breakdown Complete**

| Metric | Value |
|--------|-------|
| Total Epics | 6 |
| Total Stories | 28 |
| MVP Stories (P16-1 to P16-4) | 19 |
| Growth Stories (P16-5 to P16-6) | 9 |
| FR Coverage | 40/43 (FR41-43 deferred) |

**Story Distribution:**
- P16-1 User Management: 7 stories
- P16-2 Live Streaming: 5 stories
- P16-3 Entity Editing: 4 stories
- P16-4 Entity Assignment UX: 3 stories
- P16-5 Active Sessions: 5 stories
- P16-6 Multi-Entity Events: 4 stories

**Implementation Order:**
1. P16-1 (foundational - user model changes)
2. P16-3 (independent, quick win)
3. P16-4 (independent, quick win)
4. P16-2 (requires research)
5. P16-5 (depends on P16-1 auth changes)
6. P16-6 (depends on research)

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans._

_This document will be referenced during Phase 4 implementation alongside PRD-phase16.md and architecture-phase16.md._
