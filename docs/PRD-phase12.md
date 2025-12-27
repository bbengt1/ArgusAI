# ArgusAI Phase 12 - Product Requirements Document
## Mobile Backend Infrastructure & Entity-Based Alerts

**Author:** Brent
**Date:** 2025-12-26
**Version:** 1.0
**Phase:** 12
**Status:** Complete

---

## Executive Summary

Phase 12 transforms ArgusAI from a web-first application into a mobile-ready platform with personalized, entity-aware alerting. Building on the entity recognition and mobile push infrastructure established in Phases 4 and 11, this phase delivers:

1. **Entity-Based Alert Rules** - Create alerts that trigger for specific recognized people or vehicles, enabling personalized notifications like "John arrived home" or "Unknown person at front door"

2. **Mobile Backend Infrastructure** - Complete the backend APIs required for native mobile apps: device registration, secure pairing flows, and token lifecycle management

3. **Advanced Query-Adaptive AI** - Enhance the intelligent frame selection system with batch processing, diversity filtering, and multi-query support for more accurate re-analysis

### What Makes This Special

**Personalization at Scale**: Instead of generic "person detected" alerts, users can create rules tied to specific recognized entities. The system learns who matters and alerts accordingly - welcoming family members while flagging strangers.

**Mobile-First Security**: The device pairing flow uses time-limited codes displayed on the trusted web dashboard, ensuring only authorized devices can connect to the ArgusAI instance without exposing credentials.

---

## Project Classification

**Technical Type:** API/Backend + Mobile Infrastructure
**Domain:** Home Security / Smart Home
**Complexity:** Medium (building on established Phase 4/11 foundations)

**Backlog Items Addressed:**
| ID | Priority | Description |
|----|----------|-------------|
| IMP-037 | P2 (elevated) | Entity-Based Alert Rules |
| IMP-027 | P3 | Mobile Device Registration |
| IMP-028 | P3 | Token Refresh Endpoint |
| IMP-036 | P2 | Mobile App Device Pairing Code Flow |
| IMP-034 | P3 | Query-Adaptive Phase 2: Optimization |
| IMP-035 | P3 | Query-Adaptive Phase 3: Advanced Features |

**Dependencies:**
- Phase 4: Entity recognition system (RecognizedEntity model, embeddings)
- Phase 11: Cloudflare Tunnel remote access, APNS/FCM push providers, basic query-adaptive frames

---

## Success Criteria

### Primary Success Metrics

**Entity-Based Alerts:**
- Users can create alert rules targeting specific entities (people/vehicles)
- Alert rules correctly match events to entities with >90% accuracy
- "Unknown entity" alerts function correctly for stranger detection
- Entity alerts integrate seamlessly with existing push notification infrastructure

**Mobile Backend Infrastructure:**
- Device pairing completes successfully via 6-digit code flow
- JWT tokens refresh correctly with sliding window expiration
- Multiple devices per user supported and manageable
- Device revocation immediately invalidates access

**Query-Adaptive Enhancements:**
- Batch embedding generation reduces per-frame overhead by 40%+
- Diversity filtering prevents near-duplicate frame selection
- Multi-query support enables complex re-analysis scenarios

### Quality Metrics

- API response times: <200ms for device operations, <100ms for token refresh
- Zero security vulnerabilities in pairing/authentication flows
- 100% backward compatibility with existing alert rules
- All new endpoints covered by automated tests

---

## Product Scope

### MVP - Phase 12 Core Deliverables

**Epic 1: Entity-Based Alert Rules (HIGH PRIORITY)**
- Add entity_id field to AlertRule model
- Extend alert rule UI with entity selector dropdown
- Implement entity filter condition in alert evaluation
- Support "any unknown entity" option for stranger detection
- Display entity name in alert notifications and rule lists

**Epic 2: Mobile Device Registration**
- Create Device model (device_id, platform, name, user_id, push_token, last_seen)
- Implement device CRUD endpoints (POST/GET/DELETE /api/v1/devices)
- Associate push tokens with registered devices
- Add device management UI in Settings

**Epic 3: Mobile Authentication & Pairing**
- Implement 6-digit pairing code generation with 5-minute expiry
- Create pairing verification endpoint (exchange code for JWT)
- Build "Confirm Pairing Code" UI in Settings > Devices
- Implement token refresh endpoint with sliding window expiration
- Add refresh token rotation for security

**Epic 4: Query-Adaptive Optimization**
- Implement batch embedding generation for efficiency
- Add diversity filtering to prevent near-duplicate frames
- Integrate quality scoring with frame selection
- Add metrics for query matching effectiveness

### Growth Features (Post Phase 12)

- Native iOS app using the mobile backend infrastructure
- Native Android app
- Apple Watch complications and notifications
- iPad dashboard with live camera previews
- macOS menu bar app

### Vision (Future)

- Full MCP protocol compliance for external AI tool integration
- Voice assistant queries ("What happened at the front door today?")
- Predictive alerts based on entity behavior patterns
- Cross-device notification sync and history

---

## Functional Requirements

### Entity-Based Alert Rules

- **FR1:** Users can create alert rules that trigger only for specific recognized entities
- **FR2:** Users can select an entity from a dropdown when creating/editing an alert rule
- **FR3:** Users can create alert rules that trigger for "any unknown entity" (stranger detection)
- **FR4:** Alert rules can combine entity filters with existing conditions (camera, time, detection type)
- **FR5:** Entity name displays in alert rule list for easy identification
- **FR6:** Push notifications include entity name when alert is entity-based
- **FR7:** Webhook payloads include entity information when alert is entity-triggered
- **FR8:** Users can view which alert rules are associated with a specific entity from the entity detail page

### Mobile Device Registration

- **FR9:** Mobile apps can register devices with the ArgusAI backend
- **FR10:** Each device registration captures platform (iOS/Android), device name, and unique device ID
- **FR11:** Users can view all registered devices in Settings
- **FR12:** Users can rename registered devices for easier identification
- **FR13:** Users can revoke/delete device registrations
- **FR14:** Device revocation immediately invalidates all tokens for that device
- **FR15:** Push tokens are associated with registered devices
- **FR16:** System tracks last_seen timestamp for each device
- **FR17:** Devices inactive for 90+ days are flagged for potential cleanup

### Mobile Authentication & Pairing

- **FR18:** Mobile apps can request a 6-digit pairing code
- **FR19:** Pairing codes expire after 5 minutes
- **FR20:** Users confirm pairing codes via the web dashboard Settings > Devices section
- **FR21:** Confirmed pairing codes can be exchanged for JWT access tokens
- **FR22:** JWT tokens include device_id claim for device-specific operations
- **FR23:** Mobile apps can refresh expired tokens within a grace period
- **FR24:** Token refresh extends expiration using sliding window (24-hour extension)
- **FR25:** Refresh tokens are rotated on each refresh for security
- **FR26:** Password changes invalidate all tokens across all devices
- **FR27:** Rate limiting prevents brute-force pairing attempts (5 attempts per minute)
- **FR28:** WebSocket notification alerts web dashboard when pairing code is generated

### Query-Adaptive Frame Selection Optimization

- **FR29:** Frame embeddings are generated in batches for improved efficiency
- **FR30:** Diversity filtering prevents selection of near-duplicate frames
- **FR31:** Frame quality scores (blur, exposure) factor into selection algorithm
- **FR32:** System tracks query matching effectiveness metrics
- **FR33:** Multi-query support allows complex queries with OR logic
- **FR34:** Query suggestions appear based on event type and smart detection
- **FR35:** A/B comparison mode available for uniform vs adaptive selection validation
- **FR36:** Query results are cached with TTL per event+query combination
- **FR37:** Re-analyze modal shows relevance scores for selected frames
- **FR38:** Single-word queries are auto-formatted with "a photo of {query}" template

### API Endpoints

- **FR39:** POST `/api/v1/devices` - Register a new device
- **FR40:** GET `/api/v1/devices` - List user's registered devices
- **FR41:** PUT `/api/v1/devices/{id}` - Update device (rename)
- **FR42:** DELETE `/api/v1/devices/{id}` - Revoke device registration
- **FR43:** POST `/api/v1/mobile/auth/pair` - Generate 6-digit pairing code
- **FR44:** POST `/api/v1/mobile/auth/verify` - Exchange confirmed code for JWT
- **FR45:** POST `/api/v1/auth/refresh` - Refresh expired JWT token
- **FR46:** PUT `/api/v1/alert-rules/{id}` - Updated to support entity_id field
- **FR47:** GET `/api/v1/context/entities/{id}/alert-rules` - List alert rules for an entity

---

## Non-Functional Requirements

### Security

- **NFR1:** Pairing codes must be cryptographically random (not sequential or predictable)
- **NFR2:** JWT tokens must be signed with strong algorithm (RS256 or ES256)
- **NFR3:** Refresh tokens must be stored hashed, not plaintext
- **NFR4:** Device revocation must propagate within 1 second
- **NFR5:** All mobile auth endpoints must use HTTPS (enforced by Cloudflare Tunnel)
- **NFR6:** Failed pairing attempts must be logged for security monitoring

### Performance

- **NFR7:** Device registration endpoint: <200ms response time
- **NFR8:** Token refresh endpoint: <100ms response time
- **NFR9:** Pairing code generation: <50ms
- **NFR10:** Entity-based alert evaluation: <10ms additional overhead per rule
- **NFR11:** Batch embedding generation: 40% reduction in per-frame overhead vs sequential
- **NFR12:** Query result caching: 5-minute TTL, <5ms cache hit latency

### Scalability

- **NFR13:** Support up to 10 devices per user
- **NFR14:** Support up to 100 registered devices per ArgusAI instance
- **NFR15:** Entity-based alert rules scale to 50+ entities without performance degradation

### Reliability

- **NFR16:** Device token refresh must work during brief network interruptions (retry logic)
- **NFR17:** Pairing flow must handle concurrent code requests gracefully
- **NFR18:** Alert rule evaluation must fail-open (deliver alert if entity lookup fails)

### Compatibility

- **NFR19:** Mobile API must support iOS 15+ and Android 10+
- **NFR20:** All new features must maintain backward compatibility with existing web UI
- **NFR21:** Entity-based alerts must work with all existing notification channels (Web Push, APNS, FCM, webhooks)

---

## Epic Summary

| Epic | Priority | Stories Est. | Description |
|------|----------|--------------|-------------|
| P12-1 | HIGH | 4-5 | Entity-Based Alert Rules |
| P12-2 | MEDIUM | 4-5 | Mobile Device Registration |
| P12-3 | MEDIUM | 5-6 | Mobile Authentication & Pairing |
| P12-4 | LOW | 4-5 | Query-Adaptive Optimization |

**Total Estimated Stories:** 17-21

---

## Implementation Planning

### Recommended Epic Order

1. **Epic P12-1: Entity-Based Alert Rules** (HIGH PRIORITY)
   - Highest user value, builds on existing entity infrastructure
   - Independent of mobile infrastructure
   - Can be released standalone

2. **Epic P12-2: Mobile Device Registration**
   - Foundation for Epic P12-3
   - Creates Device model and CRUD APIs

3. **Epic P12-3: Mobile Authentication & Pairing**
   - Depends on P12-2 (needs Device model)
   - Enables future native app development

4. **Epic P12-4: Query-Adaptive Optimization**
   - Independent of other epics
   - Enhances existing Phase 11 query-adaptive foundation

### Architecture Considerations

- Extend existing `AlertRule` model with nullable `entity_id` foreign key
- Create new `Device` model with relationship to User
- Create new `PairingCode` model for temporary code storage
- Extend `PushDispatchService` to query by device
- Add device_id claim to JWT token structure

---

## References

- Product Brief: [docs/product-brief.md](product-brief.md)
- Phase 11 PRD: [docs/PRD-phase11.md](PRD-phase11.md)
- Backlog: [docs/backlog.md](backlog.md)
- Mobile Auth Design: [docs/api/mobile-auth-flow.md](api/mobile-auth-flow.md)
- Mobile Push Architecture: [docs/api/mobile-push-architecture.md](api/mobile-push-architecture.md)
- Query-Adaptive Research: [docs/research/query-adaptive-frames-research.md](research/query-adaptive-frames-research.md)

### Backlog Item Mapping

| Backlog ID | Epic | Description |
|------------|------|-------------|
| IMP-037 | P12-1 | Entity-Based Alert Rules |
| IMP-027 | P12-2 | Mobile Device Registration |
| IMP-028 | P12-3 | Token Refresh Endpoint |
| IMP-036 | P12-3 | Mobile App Device Pairing Code Flow |
| IMP-034 | P12-4 | Query-Adaptive Phase 2: Optimization |
| IMP-035 | P12-4 | Query-Adaptive Phase 3: Advanced Features |

---

## Next Steps

1. **Epic & Story Breakdown** - Run: `/bmad:bmm:workflows:create-epics-and-stories`
2. **Architecture Review** - Run: `/bmad:bmm:workflows:architecture` (optional - builds on existing)
3. **Sprint Planning** - Run: `/bmad:bmm:workflows:sprint-planning`

---

_This PRD captures Phase 12 of ArgusAI - Mobile Backend Infrastructure & Entity-Based Alerts_

_Created through collaborative discovery between Brent and AI facilitator on 2025-12-26._
