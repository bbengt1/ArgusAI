# Story P8-4.2: Design Cloud Relay Architecture

Status: done

## Story

As a **mobile app user**,
I want **a documented cloud relay architecture for secure remote access**,
So that **I can access my ArgusAI instance from anywhere without port forwarding**.

## Acceptance Criteria

1. **AC2.1:** Given design complete, when document reviewed, then connection flow (app -> relay -> local) diagrammed

2. **AC2.2:** Given design complete, when document reviewed, then authentication/pairing mechanism documented

3. **AC2.3:** Given design complete, when document reviewed, then Cloudflare Tunnel + Tailscale options compared

4. **AC2.4:** Given design complete, when document reviewed, then security considerations addressed

5. **AC2.5:** Given design complete, when document reviewed, then cost estimates per provider included

6. **AC2.6:** Given design complete, when document reviewed, then sequence diagrams for key flows included

7. **AC2.7:** Given design complete, then document saved to `docs/architecture/cloud-relay-design.md`

## Tasks / Subtasks

- [x] Task 1: Define connection requirements (AC: 1)
  - [x] Document no port forwarding requirement
  - [x] Document NAT traversal needs
  - [x] Document end-to-end encryption requirements
  - [x] Create connection flow diagram (app -> relay -> local)

- [x] Task 2: Evaluate relay providers (AC: 3, 5)
  - [x] Document Cloudflare Tunnel (Zero Trust) - features, setup, free tier limits
  - [x] Document Tailscale (mesh VPN) - features, setup, free tier limits
  - [x] Document AWS API Gateway option (for comparison)
  - [x] Document self-hosted relay option (for advanced users)
  - [x] Create comparison matrix with pros/cons
  - [x] Include cost estimates for each provider

- [x] Task 3: Design authentication flow (AC: 2)
  - [x] Document device pairing sequence (6-digit code, 5-min TTL)
  - [x] Document JWT token-based access (access + refresh tokens)
  - [x] Document token refresh mechanism
  - [x] Document certificate pinning approach

- [x] Task 4: Document security considerations (AC: 4)
  - [x] Document encryption approach (TLS 1.3)
  - [x] Document rate limiting strategy
  - [x] Document abuse prevention measures
  - [x] Document token security (single-use pairing, rotation)

- [x] Task 5: Create sequence diagrams (AC: 6)
  - [x] Pairing flow sequence diagram
  - [x] Remote access flow sequence diagram
  - [x] Token refresh sequence diagram
  - [x] Local network fallback sequence diagram

- [x] Task 6: Document recommendation and save (AC: 7)
  - [x] Clear recommendation (Cloudflare Tunnel primary, Tailscale fallback)
  - [x] Setup instructions summary
  - [x] Save to docs/architecture/cloud-relay-design.md

## Dev Notes

### Architecture Alignment

From architecture-phase8.md, the cloud relay decision has been made:
- **Cloud Relay**: Cloudflare Tunnel + Tailscale fallback
- **Mobile Auth**: Device pairing codes (6-digit, 5-min expiry)
- **Security**: TLS 1.3, certificate pinning, token rotation

This design story documents the detailed architecture for remote access, expanding on the high-level decisions already captured.

### Design Areas

1. **Connection Requirements:**
   - Zero port forwarding (user-friendly)
   - NAT traversal (works behind any router)
   - End-to-end encryption (TLS 1.3)
   - Local network fallback (when on same LAN)

2. **Provider Comparison:**
   - Cloudflare Tunnel: Free tier, easy setup, Cloudflare CDN benefits
   - Tailscale: Mesh VPN, no central relay, requires client on local network
   - AWS API Gateway: Enterprise option, cost-based
   - Self-hosted: For advanced users, full control

3. **Authentication Flow:**
   - Pairing: Web UI generates 6-digit code -> User enters in app -> App receives JWT tokens
   - Access: Bearer token on all mobile API requests
   - Refresh: Automatic refresh before expiry, rotate refresh token

4. **Security Measures:**
   - Single-use pairing codes (deleted after verification)
   - Short-lived access tokens (1 hour)
   - Long-lived refresh tokens (30 days, rotated on use)
   - Device ID binding (tokens tied to specific device)
   - Certificate pinning (prevent MITM)

### Learnings from Previous Story

**From Story p8-4-1-research-native-apple-app-technologies (Status: done)**

- **Research Document Created**: Technology research at `docs/research/apple-apps-technology.md`
- **SwiftUI Recommended**: iOS 17+ minimum, full Apple platform support
- **Architecture Context**: Research confirms mobile app approach aligns with cloud relay needs

[Source: docs/sprint-artifacts/p8-4-1-research-native-apple-app-technologies.md#Dev-Agent-Record]

### Output Format

The design document should include:
- Executive summary with recommendation
- Detailed connection flow diagrams (Mermaid or ASCII)
- Provider comparison table
- Authentication sequence diagrams
- Security considerations section
- Cost estimates table
- Setup instructions reference

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P8-4.md#P8-4.2] - Acceptance criteria
- [Source: docs/epics-phase8.md#Story-P8-4.2] - Story definition
- [Source: docs/architecture-phase8.md] - Architecture decisions

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p8-4-2-design-cloud-relay-architecture.context.xml

### Agent Model Used

Claude Opus 4.5

### Debug Log References

None - documentation story with no code execution

### Completion Notes List

- Created comprehensive cloud relay architecture document at docs/architecture/cloud-relay-design.md
- Document includes connection flow diagrams (app -> relay -> local, local network fallback)
- Compared Cloudflare Tunnel, Tailscale, AWS API Gateway, and self-hosted options
- Documented device pairing mechanism (6-digit codes, 5-min TTL, single-use)
- JWT token authentication with access (1h) and refresh (30d) tokens
- Security considerations: TLS 1.3, rate limiting, abuse prevention, certificate pinning
- Four sequence diagrams: pairing, remote access, token refresh, local fallback
- Cost estimates included for all providers
- Quick start appendices for Cloudflare and Tailscale setup
- All acceptance criteria satisfied

### File List

CREATED:
- docs/architecture/cloud-relay-design.md - Comprehensive cloud relay architecture design document (450+ lines)

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-24 | Story drafted from Epic P8-4 and tech spec |
| 2025-12-24 | Implementation complete - cloud relay design document created at docs/architecture/cloud-relay-design.md |
