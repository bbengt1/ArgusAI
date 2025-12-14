# ArgusAI Phase 5 - Product Requirements Document
## Backlog Cleanup, HomeKit Integration & Quality

**Author:** Brent
**Date:** 2025-12-14
**Version:** 1.0
**Phase:** 5

---

## Executive Summary

Phase 5 focuses on three strategic pillars: **platform expansion** through native HomeKit integration, **setup experience** improvements via ONVIF camera discovery, and **quality hardening** through comprehensive testing infrastructure. This phase addresses accumulated backlog items while expanding ArgusAI's reach to Apple ecosystem users who don't use Home Assistant.

With Phase 4's MQTT/Home Assistant integration complete, Phase 5 ensures ArgusAI serves both major smart home ecosystems natively - users can choose Home Assistant, Apple HomeKit, or both without compromise.

### What Makes This Special

**Dual Ecosystem Independence** - ArgusAI becomes a true platform-agnostic AI vision system. HomeKit users get native integration without requiring Home Assistant as middleware. Home Assistant users continue with MQTT. Power users can run both simultaneously.

**Zero-Config Camera Discovery** - ONVIF auto-discovery transforms the setup experience from "find your camera's RTSP URL" to "select from discovered cameras." This removes the biggest friction point for non-technical users.

**Production-Ready Quality** - GitHub Actions CI/CD pipeline ensures every change is tested. Performance baselines document actual resource usage. Real-world camera testing validates detection accuracy claims.

---

## Project Classification

**Technical Type:** Web Application + Smart Home Integration (API/Backend + IoT)
**Domain:** Home Security / Smart Home (General - Low Complexity)
**Complexity:** Medium

**Phase 5 Classification:**
- **Primary Focus:** Platform Integration (HomeKit) + Developer Experience (Testing/CI)
- **Secondary Focus:** UX Improvements (ONVIF, presets, accessibility)
- **Technical Challenges:** HAP protocol implementation, camera streaming to HomeKit, CI/CD setup

---

## Success Criteria

### HomeKit Integration Success
- **Camera appears in Apple Home app** - Users can add ArgusAI cameras as HomeKit accessories and view live streams
- **Motion sensors trigger automations** - HomeKit automations fire when ArgusAI detects person/vehicle/animal/package
- **Doorbell rings appear in Home app** - Protect doorbell events surface as HomeKit doorbell notifications
- **Pairing works reliably** - QR code or manual pairing completes without troubleshooting

### Camera Discovery Success
- **ONVIF discovery finds cameras** - Cameras on local network auto-discovered within 10 seconds
- **One-click add** - Discovered cameras can be added without manually entering RTSP URLs
- **Test before save works** - Users can verify camera connection before committing configuration

### Quality & Testing Success
- **CI pipeline runs on every PR** - GitHub Actions executes backend tests, frontend tests, and linting
- **Frontend test coverage >60%** - React components have meaningful test coverage
- **Performance baselines documented** - CPU/memory usage documented for reference configurations
- **Real camera validation complete** - Detection rates validated against diverse footage (>90% person detection, <20% false positives)

### UX Polish Success
- **Accessibility audit passes** - WCAG 2.1 AA compliance for core workflows
- **Detection zone presets available** - Users can apply common zone templates with one click
- **Multiple schedules supported** - Users can define multiple active time ranges per day

---

## Product Scope

### Phase 5 MVP - Core Deliverables

**Epic 1: Native HomeKit Integration**
- HAP (HomeKit Accessory Protocol) bridge implementation using HAP-python
- Camera accessory with live RTSP-to-HLS streaming
- Motion sensor accessories (person, vehicle, animal, package detection types)
- Occupancy sensor for person presence
- Doorbell accessory for Protect doorbell ring events
- HomeKit pairing UI with QR code generation
- Settings page for HomeKit enable/disable and accessory management

**Epic 2: ONVIF Camera Discovery**
- Network scanner for ONVIF-compatible cameras
- Auto-populate camera details (name, RTSP URL, capabilities)
- Discovery UI showing found cameras with "Add" action
- Test connection endpoint (POST /api/v1/cameras/test)
- Graceful handling of non-ONVIF cameras (fall back to manual entry)

**Epic 3: CI/CD & Testing Infrastructure**
- GitHub Actions workflow for PR checks
- Backend pytest execution in CI
- Frontend Vitest + React Testing Library setup
- Frontend test execution in CI
- ESLint/TypeScript checks in CI
- FeedbackButtons component tests (TD-002)
- Test coverage reporting

**Epic 4: Quality & Performance Validation**
- Real camera integration testing with diverse footage
- Performance baseline documentation (CPU/memory/network)
- Motion detection accuracy validation (>90% person, <20% false positive)

**Epic 5: UX Polish & Accessibility**
- ARIA labels and keyboard navigation improvements
- Detection zone presets (Rectangle, Top Half, Bottom Half, Center)
- Multiple schedule time ranges per day
- README update with frontend setup instructions

### Growth Features (Post-Phase 5)

**MQTT Enhancements (from backlog)**
- MQTT 5.0 features (message expiry, shared subscriptions) - FF-012
- MQTT birth/will messages for connection monitoring - FF-013

**Advanced Features**
- Audio capture from cameras for future audio AI - FF-015
- Export motion events to CSV - FF-017
- Camera list performance optimizations (virtual scroll, memo) - IMP-005

### Vision (Future Phases)

**HomeKit Secure Video (HKSV)** - Full iCloud recording integration (significant complexity, requires Apple certification consideration)

**Cross-Platform Mobile App** - Native iOS/Android app for push notifications and remote viewing

**Edge AI Processing** - Local AI inference for reduced latency and privacy (CoreML on macOS, TensorRT on Linux)

---

## Functional Requirements

### HomeKit Integration

**FR1:** System can act as a HomeKit bridge exposing multiple accessories
**FR2:** Users can pair ArgusAI with Apple Home app via QR code or manual PIN
**FR3:** Each configured camera appears as a HomeKit Camera accessory with live streaming
**FR4:** Camera streams are transcoded from RTSP to HLS format for HomeKit compatibility
**FR5:** Motion detection events create HomeKit Motion Sensor trigger notifications
**FR6:** Person detection events create HomeKit Occupancy Sensor state changes
**FR7:** Vehicle, animal, and package detections create distinct HomeKit sensor accessories
**FR8:** Protect doorbell ring events trigger HomeKit Doorbell accessory notifications
**FR9:** Users can enable/disable HomeKit integration from Settings page
**FR10:** Users can view and manage HomeKit accessory pairings from Settings page
**FR11:** HomeKit accessories remain responsive when ArgusAI web UI is not in use
**FR12:** Multiple Apple Home users can access shared HomeKit accessories

### Camera Discovery & Setup

**FR13:** System can discover ONVIF-compatible cameras on the local network
**FR14:** Discovery scan completes within 10 seconds for typical home networks
**FR15:** Discovered cameras display name, IP address, and manufacturer
**FR16:** Users can add discovered cameras with one click (auto-populates RTSP URL)
**FR17:** Users can test camera connection before saving configuration
**FR18:** Test connection endpoint validates RTSP URL, credentials, and stream availability
**FR19:** Non-ONVIF cameras can still be added via manual RTSP URL entry

### Testing Infrastructure

**FR20:** GitHub Actions workflow executes on every pull request to main/development branches
**FR21:** CI pipeline runs backend pytest suite and fails PR if tests fail
**FR22:** CI pipeline runs frontend test suite and fails PR if tests fail
**FR23:** CI pipeline runs ESLint and TypeScript type checking
**FR24:** Test coverage reports are generated and visible in CI output
**FR25:** FeedbackButtons component has unit tests for all interaction states
**FR26:** Frontend testing framework (Vitest + React Testing Library) is configured and documented

### Quality Validation

**FR27:** Performance baselines document CPU usage for 1-4 cameras at various FPS settings
**FR28:** Performance baselines document memory usage under normal operation
**FR29:** Motion detection accuracy is validated against real-world test footage
**FR30:** Detection accuracy meets targets: >90% person detection, <20% false positive rate

### UX & Accessibility

**FR31:** All interactive elements have appropriate ARIA labels for screen readers
**FR32:** Core workflows are navigable via keyboard only (no mouse required)
**FR33:** Focus states are visible and logical throughout the application
**FR34:** Detection zone configuration offers preset templates (Rectangle, Top Half, Bottom Half, Center, L-shape)
**FR35:** Users can define multiple active time ranges per day for detection schedules
**FR36:** README includes comprehensive frontend setup and development instructions

### Backlog Items Addressed

**FR37:** MQTT 5.0 message expiry is supported for event messages (FF-012 partial)
**FR38:** MQTT birth message published on connect, will message on disconnect (FF-013)

---

## Non-Functional Requirements

### Performance

**NFR1:** HomeKit camera streaming adds <500ms latency to live view
**NFR2:** HomeKit sensor state updates propagate within 2 seconds of ArgusAI event detection
**NFR3:** ONVIF discovery scan completes within 10 seconds on networks with up to 50 devices
**NFR4:** HomeKit bridge startup completes within 30 seconds of ArgusAI backend start
**NFR5:** CI pipeline completes all checks within 10 minutes
**NFR6:** System maintains <50% average CPU usage with HomeKit streaming active (single camera)

### Security

**NFR7:** HomeKit pairing uses secure SRP (Secure Remote Password) protocol per HAP specification
**NFR8:** HomeKit communication is encrypted using ChaCha20-Poly1305 per HAP specification
**NFR9:** HomeKit pairing PIN/QR codes are not logged or persisted after initial pairing
**NFR10:** ONVIF discovery does not expose camera credentials in network traffic
**NFR11:** CI pipeline secrets (API keys, credentials) are stored in GitHub Secrets, never in code

### Reliability

**NFR12:** HomeKit bridge automatically reconnects after network interruptions
**NFR13:** HomeKit accessories remain paired across ArgusAI restarts
**NFR14:** CI pipeline has retry logic for transient failures (network timeouts)
**NFR15:** ONVIF discovery gracefully handles unresponsive cameras without blocking

### Compatibility

**NFR16:** HomeKit integration compatible with iOS 15+ and macOS 12+
**NFR17:** HomeKit integration works with Apple TV and HomePod as home hubs
**NFR18:** ONVIF discovery compatible with ONVIF Profile S and Profile T cameras
**NFR19:** CI pipeline runs on GitHub-hosted Ubuntu runners
**NFR20:** Frontend tests compatible with Node.js 18+ LTS

### Accessibility

**NFR21:** All new UI components meet WCAG 2.1 Level AA contrast requirements (4.5:1 minimum)
**NFR22:** Interactive elements have minimum 44x44px touch targets on mobile
**NFR23:** Form inputs have associated labels and error messages announced by screen readers

---

## Implementation Planning

### Epic Breakdown

**Epic P5-1: Native HomeKit Integration** (Priority: High)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-1.1 | Set up HAP-python bridge infrastructure | FR1, FR11 |
| P5-1.2 | Implement HomeKit pairing with QR code | FR2 |
| P5-1.3 | Create Camera accessory with RTSP-to-HLS streaming | FR3, FR4 |
| P5-1.4 | Implement Motion Sensor accessories | FR5 |
| P5-1.5 | Implement Occupancy Sensor for person detection | FR6 |
| P5-1.6 | Add Vehicle/Animal/Package sensor accessories | FR7 |
| P5-1.7 | Implement Doorbell accessory for Protect events | FR8 |
| P5-1.8 | Build HomeKit Settings UI (enable/disable, pairings) | FR9, FR10, FR12 |

**Epic P5-2: ONVIF Camera Discovery** (Priority: High)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-2.1 | Implement ONVIF WS-Discovery scanner | FR13, FR14 |
| P5-2.2 | Parse ONVIF device info and capabilities | FR15 |
| P5-2.3 | Build camera discovery UI with add action | FR16, FR19 |
| P5-2.4 | Implement test connection endpoint | FR17, FR18 |

**Epic P5-3: CI/CD & Testing Infrastructure** (Priority: High)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-3.1 | Create GitHub Actions workflow for PRs | FR20 |
| P5-3.2 | Add backend pytest execution to CI | FR21 |
| P5-3.3 | Set up Vitest + React Testing Library | FR26 |
| P5-3.4 | Add frontend test execution to CI | FR22 |
| P5-3.5 | Add ESLint and TypeScript checks to CI | FR23 |
| P5-3.6 | Configure test coverage reporting | FR24 |
| P5-3.7 | Write FeedbackButtons component tests | FR25, TD-002 |

**Epic P5-4: Quality & Performance Validation** (Priority: Medium)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-4.1 | Document CPU/memory performance baselines | FR27, FR28, TD-004 |
| P5-4.2 | Acquire and organize real camera test footage | FR29, TD-003 |
| P5-4.3 | Validate motion detection accuracy metrics | FR30 |

**Epic P5-5: UX Polish & Accessibility** (Priority: Medium)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-5.1 | Add ARIA labels to all interactive elements | FR31 |
| P5-5.2 | Implement keyboard navigation for core workflows | FR32, FR33 |
| P5-5.3 | Create detection zone preset templates | FR34, FF-018 |
| P5-5.4 | Implement multiple schedule time ranges | FR35, FF-016 |
| P5-5.5 | Update README with frontend setup docs | FR36, TD-005 |

**Epic P5-6: MQTT Enhancements** (Priority: Low)
| Story | Description | FRs |
|-------|-------------|-----|
| P5-6.1 | Add MQTT 5.0 message expiry support | FR37, FF-012 |
| P5-6.2 | Implement MQTT birth/will messages | FR38, FF-013 |

### Backlog Items Addressed by Phase 5

| Backlog ID | Status After Phase 5 |
|------------|---------------------|
| TD-002 | Done (P5-3.7) |
| TD-003 | Done (P5-4.2) |
| TD-004 | Done (P5-4.1) |
| TD-005 | Done (P5-5.5) |
| IMP-004 | Done (P5-5.1, P5-5.2) |
| FF-011 | Done (P5-2.4) |
| FF-012 | Done (P5-6.1) |
| FF-013 | Done (P5-6.2) |
| FF-014 | Done (P5-2.1, P5-2.2, P5-2.3) |
| FF-016 | Done (P5-5.4) |
| FF-018 | Done (P5-5.3) |

### Backlog Items Deferred

| Backlog ID | Reason |
|------------|--------|
| FF-015 | Audio capture - future audio AI phase |
| FF-017 | Export motion CSV - low priority utility |
| IMP-005 | Camera list optimizations - premature for current scale |

---

## Technical Considerations

### HomeKit Implementation

**Library:** HAP-python (https://github.com/ikalchev/HAP-python)
- Mature Python implementation of HomeKit Accessory Protocol
- Supports camera streaming via ffmpeg transcoding
- Handles pairing, encryption, and accessory state management

**Camera Streaming Architecture:**
```
RTSP Camera → ffmpeg (transcode) → HLS segments → HomeKit Client
```
- ffmpeg transcodes RTSP to H.264 + AAC in HLS format
- Requires ffmpeg binary installed on system
- Streaming initiated on-demand when Home app requests

**Accessory Types:**
- `Camera` - Live streaming with snapshot support
- `MotionSensor` - Binary motion detected state
- `OccupancySensor` - Binary occupancy state (longer timeout than motion)
- `Doorbell` - Programmable switch with single press event

### ONVIF Implementation

**Library:** python-onvif-zeep or onvif2
- WS-Discovery for camera detection
- ONVIF Device Management for capabilities query
- ONVIF Media for RTSP URL extraction

**Discovery Flow:**
1. Send WS-Discovery probe to multicast address
2. Collect responses with device endpoints
3. Query each device for capabilities
4. Extract RTSP stream URLs from Media service
5. Present discovered cameras in UI

### CI/CD Architecture

**GitHub Actions Workflow:**
```yaml
name: CI
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run test
      - run: npm run lint
      - run: npx tsc --noEmit
```

---

## References

- Product Brief: docs/product-brief.md
- Phase 4 PRD: docs/PRD-phase4.md
- Architecture: docs/architecture.md
- Backlog: docs/backlog.md
- HAP-python: https://github.com/ikalchev/HAP-python
- ONVIF Specs: https://www.onvif.org/specs/core/ONVIF-Core-Specification.pdf

---

## Summary

**Phase 5 delivers:**
- Native HomeKit integration for Apple ecosystem users
- ONVIF camera auto-discovery for simplified setup
- CI/CD pipeline with automated testing
- Performance validation and documentation
- Accessibility and UX improvements
- Resolution of 11 backlog items

**Total Stories:** 25 across 6 epics
**New FRs:** 38
**New NFRs:** 23

---

_This PRD captures Phase 5 of ArgusAI - Backlog Cleanup, HomeKit Integration & Quality_

_Created through collaborative discovery between Brent and AI facilitator._
