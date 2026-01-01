# ArgusAI - Product Requirements Document

**Author:** Brent
**Date:** 2026-01-01
**Version:** 1.0
**Phase:** 16 - User Experience & Access Management

---

## Executive Summary

Phase 16 enhances ArgusAI's **user experience and access management** capabilities. After Phase 14's technical debt cleanup and Phase 15's UX consolidation, this phase adds meaningful new features that users have requested: multi-user support with invitations, live camera streaming, improved entity management, and enhanced accessibility.

This phase addresses **8 high-priority backlog items** from GitHub issues, focusing on features that expand ArgusAI from a single-user tool to a **multi-user household security platform**.

### What Makes This Special

Phase 16 transforms ArgusAI from a personal monitoring tool to a **collaborative household security system**:

1. **Multi-user access** - Invite family members with role-based permissions
2. **Live streaming** - View camera feeds directly in the dashboard without switching apps
3. **Smarter entities** - Edit entity metadata and handle multi-person events intelligently
4. **Session security** - View and manage active login sessions for peace of mind

This is the first phase focused on **collaborative use** - enabling households to share security monitoring responsibility

---

## Project Classification

**Technical Type:** Full-Stack Web Application (Python/FastAPI + Next.js)
**Domain:** Home Security / IoT / AI Vision
**Complexity:** Medium (user-facing features with security considerations)

Phase 16 is a **feature phase** building on the solid foundation from Phase 14 (technical debt) and Phase 15 (UX polish). The focus shifts from internal improvements to user-requested functionality.

---

## Success Criteria

### Primary Success Metrics

1. **Multi-user adoption** - At least 2 users can access the same ArgusAI instance with different permissions
2. **Live streaming functional** - Protect camera feeds viewable in dashboard with <3 second latency
3. **Entity UX improved** - Users can edit entity names/metadata without workarounds
4. **Session visibility** - Users can view and revoke active sessions from Settings

### Quality Gates

- All new API endpoints have unit tests with 80%+ coverage
- Live streaming works on Chrome, Safari, and Firefox
- User invitation flow tested end-to-end
- No regressions in existing entity functionality
- Security review passed for authentication changes

---

## Product Scope

### MVP - Minimum Viable Product

Phase 16 MVP focuses on **4 high-priority (P2) items**:

| ID | GitHub | Feature | Priority |
|----|--------|---------|----------|
| FF-036 | [#308](https://github.com/project-argusai/ArgusAI/issues/308) | User Management with Email Invitations | P2 |
| FF-039 | [#336](https://github.com/project-argusai/ArgusAI/issues/336) | Live Camera Feeds via Protect API | P2 |
| IMP-070 | [#337](https://github.com/project-argusai/ArgusAI/issues/337) | Entity Assignment Re-classification Warning | P2 |
| IMP-071 | [#338](https://github.com/project-argusai/ArgusAI/issues/338) | Edit Entity Metadata | P2 |

**User Management (FF-036):** Enable creating additional users with email invitations, temporary passwords, and role-based permissions (admin, viewer, operator).

**Live Camera Feeds (FF-039):** Stream live video from UniFi Protect cameras directly in the ArgusAI dashboard without opening the Protect app.

**Entity Re-classification Warning (IMP-070):** Show confirmation dialog when assigning events to entities, warning that AI re-classification will occur.

**Edit Entity Metadata (IMP-071):** Allow editing entity properties (name, type, VIP status, blocked status, notes) after creation.

### Growth Features (Post-MVP)

These **P3 items** will follow MVP completion:

| ID | GitHub | Feature | Priority |
|----|--------|---------|----------|
| FF-037 | [#342](https://github.com/project-argusai/ArgusAI/issues/342) | Active User Sessions List | P3 |
| IMP-069 | [#302](https://github.com/project-argusai/ArgusAI/issues/302) | Multi-Entity Event Assignment | P3 |
| FF-011 | [#36](https://github.com/project-argusai/ArgusAI/issues/36) | Test Connection Before Save (Camera) | P3 |

**Active Sessions (FF-037):** View and manage active login sessions with ability to revoke compromised sessions.

**Multi-Entity Events (IMP-069):** Allow events to be assigned to multiple entities (e.g., two people walking together).

**Test Connection (FF-011):** Test RTSP camera connection before saving configuration.

### Vision (Future)

Deferred to future phases (P4 items):

| ID | GitHub | Feature | Priority |
|----|--------|---------|----------|
| FF-038 | [#335](https://github.com/project-argusai/ArgusAI/issues/335) | Google Coral TPU Integration | P3/Research |
| IMP-063 | [#339](https://github.com/project-argusai/ArgusAI/issues/339) | MCP Context A/B Testing | P4 |
| IMP-064 | [#340](https://github.com/project-argusai/ArgusAI/issues/340) | MCP False Positive Frequency | P4 |
| IMP-065 | [#341](https://github.com/project-argusai/ArgusAI/issues/341) | MCP External Client Support | P4 |
| IMP-004 | [#34](https://github.com/project-argusai/ArgusAI/issues/34) | Accessibility Enhancements | P4 |
| IMP-005 | [#35](https://github.com/project-argusai/ArgusAI/issues/35) | Camera List Optimizations | P4 |
| FF-015 | [#40](https://github.com/project-argusai/ArgusAI/issues/40) | Audio Capture from Cameras | P4 |
| FF-017 | [#42](https://github.com/project-argusai/ArgusAI/issues/42) | Export Motion Events to CSV | P4 |

---

## Functional Requirements

### User Management & Authentication

- **FR1:** Administrators can create new user accounts with email address and assigned role
- **FR2:** System generates secure temporary password for new users
- **FR3:** Administrators can optionally send email invitation with login credentials
- **FR4:** New users are required to change password on first login
- **FR5:** Administrators can assign roles to users (admin, operator, viewer)
- **FR6:** Administrators can enable/disable user accounts
- **FR7:** Administrators can delete user accounts
- **FR8:** Users can view their profile information
- **FR9:** System logs all user management actions for audit trail

### Session Management

- **FR10:** Users can view list of their active sessions (device, IP, last active time)
- **FR11:** Users can identify which session is their current session
- **FR12:** Users can revoke individual sessions (force logout on that device)
- **FR13:** Users can revoke all sessions except current ("Sign out everywhere else")
- **FR14:** System enforces maximum concurrent sessions per user (configurable)
- **FR15:** Sessions expire after configurable inactivity period

### Live Camera Streaming

- **FR16:** Users can view live video feed from UniFi Protect cameras in dashboard
- **FR17:** Live stream displays with less than 3 second latency
- **FR18:** Users can select stream quality (low/medium/high)
- **FR19:** Users can view stream in fullscreen mode
- **FR20:** System falls back to snapshot refresh if live stream unavailable
- **FR21:** Multiple cameras can stream simultaneously
- **FR22:** Live view button appears on Protect camera cards

### Entity Management

- **FR23:** Users can edit entity name after creation
- **FR24:** Users can change entity type (person, vehicle, unknown)
- **FR25:** Users can toggle VIP status on entities
- **FR26:** Users can toggle blocked status on entities
- **FR27:** Users can add/edit notes on entities
- **FR28:** Entity edits are saved immediately with success confirmation
- **FR29:** Entity list and detail views update immediately after edit

### Entity Assignment UX

- **FR30:** When assigning event to entity, system displays confirmation dialog
- **FR31:** Confirmation dialog explains that AI re-classification will occur
- **FR32:** Confirmation dialog shows estimated API cost impact
- **FR33:** User can proceed with assignment or cancel
- **FR34:** User can opt-out of future warnings via "Don't show again" checkbox
- **FR35:** Preference for warning dismissal stored in browser localStorage

### Multi-Entity Events (Growth)

- **FR36:** Events can be associated with multiple entities
- **FR37:** Event cards display multiple entity badges when applicable
- **FR38:** Entity detail shows events where entity appears with others
- **FR39:** Assignment UI supports selecting multiple entities
- **FR40:** Alert rules can trigger on any matched entity in multi-entity events

### Camera Connection Testing (Growth)

- **FR41:** Users can test RTSP camera connection before saving
- **FR42:** Test returns success/failure status with error details
- **FR43:** Test does not persist camera configuration

---

## Non-Functional Requirements

### Security

- **NFR1:** User passwords must be hashed using bcrypt with cost factor ≥12
- **NFR2:** Temporary passwords must be cryptographically random (min 16 chars)
- **NFR3:** Session tokens must be invalidated on password change
- **NFR4:** User management endpoints require admin role
- **NFR5:** Rate limiting on login attempts (5/minute per IP)
- **NFR6:** Email invitation links expire after 72 hours
- **NFR7:** Live stream access requires authenticated session
- **NFR8:** Audit log entries cannot be modified or deleted

### Performance

- **NFR9:** Live stream startup latency < 3 seconds
- **NFR10:** User list loads in < 500ms for up to 100 users
- **NFR11:** Session list loads in < 200ms
- **NFR12:** Entity edit saves in < 300ms
- **NFR13:** Concurrent streams limited to prevent bandwidth saturation (configurable)

### Scalability

- **NFR14:** Support up to 50 user accounts per instance
- **NFR15:** Support up to 10 concurrent live streams
- **NFR16:** Session storage handles 500+ sessions without degradation

---

## Epic Breakdown

### Epic P16-1: User Management & Invitations (FF-036)
**Stories:** 5-7 | **Priority:** P2 | **GitHub:** [#308](https://github.com/project-argusai/ArgusAI/issues/308)

Implement multi-user support with email-based invitations and role-based access control.

**Key Deliverables:**
- User model extensions (email, must_change_password, role)
- User CRUD API endpoints
- Settings > Security > User Management UI
- Email invitation flow (optional SMTP)
- Force password change on first login

### Epic P16-2: Live Camera Streaming (FF-039)
**Stories:** 5-6 | **Priority:** P2 | **GitHub:** [#336](https://github.com/project-argusai/ArgusAI/issues/336)

Enable live video streaming from UniFi Protect cameras directly in the ArgusAI dashboard.

**Key Deliverables:**
- Research uiprotect streaming capabilities
- Backend stream proxy endpoint
- LiveStreamPlayer component (HLS/WebRTC)
- "Live View" button on camera cards
- Quality selection and fullscreen mode

### Epic P16-3: Entity Metadata Editing (IMP-071)
**Stories:** 3-4 | **Priority:** P2 | **GitHub:** [#338](https://github.com/project-argusai/ArgusAI/issues/338)

Allow users to edit entity properties after automatic creation.

**Key Deliverables:**
- EntityEditModal component
- PUT /api/v1/entities/{id} endpoint
- Edit button on entity cards and detail modal
- Form validation and success feedback

### Epic P16-4: Entity Assignment UX (IMP-070)
**Stories:** 2-3 | **Priority:** P2 | **GitHub:** [#337](https://github.com/project-argusai/ArgusAI/issues/337)

Add confirmation dialog when assigning events to entities to warn about re-classification.

**Key Deliverables:**
- Confirmation dialog component
- Re-classification warning text
- "Don't show again" preference
- localStorage persistence

### Epic P16-5: Active Sessions Management (FF-037)
**Stories:** 4-5 | **Priority:** P3 | **GitHub:** [#342](https://github.com/project-argusai/ArgusAI/issues/342)

Enable users to view and manage their active login sessions.

**Key Deliverables:**
- Session model and tracking
- Session API endpoints
- Settings > Security > Active Sessions UI
- Session revocation functionality

### Epic P16-6: Multi-Entity Events (IMP-069)
**Stories:** 4-5 | **Priority:** P3 | **GitHub:** [#302](https://github.com/project-argusai/ArgusAI/issues/302)

Support events being associated with multiple entities.

**Key Deliverables:**
- Backend multi-entity support
- UI for multiple entity badges
- Multi-select in assignment modal
- Alert rule updates

---

## Estimated Effort

| Epic | Stories | Complexity |
|------|---------|------------|
| P16-1: User Management | 5-7 | High |
| P16-2: Live Streaming | 5-6 | High |
| P16-3: Entity Editing | 3-4 | Medium |
| P16-4: Assignment UX | 2-3 | Low |
| P16-5: Active Sessions | 4-5 | Medium |
| P16-6: Multi-Entity | 4-5 | Medium |
| **Total** | **23-30** | |

**MVP (Epics 1-4):** ~15-20 stories
**Growth (Epics 5-6):** ~8-10 stories

---

## References

- Open Backlog Items: [docs/backlog.md](backlog.md)
- GitHub Issues: #302, #308, #335-342

---

## Next Steps

1. **Epic & Story Breakdown** - Run: `workflow create-epics-and-stories`
2. **Architecture Review** - Review existing architecture for new endpoints
3. **Sprint Planning** - Run: `workflow sprint-planning`

---

_This PRD captures Phase 16 of ArgusAI - transforming it from a personal monitoring tool to a collaborative household security platform with multi-user support, live streaming, and enhanced entity management._

_Created through collaborative discovery between Brent and AI facilitator._
