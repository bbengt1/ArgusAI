# Phase 5 Epics: Backlog Cleanup, HomeKit Integration & Quality

**PRD Reference:** docs/PRD-phase5.md
**Architecture Reference:** docs/architecture/ (Phase 5 Additions)
**Date:** 2025-12-14

---

## Epic P5-1: Native HomeKit Integration

**Priority:** High
**Goal:** Enable ArgusAI cameras and sensors to appear in Apple Home app for HomeKit users

### Story P5-1.1: Set up HAP-python Bridge Infrastructure
**Description:** Initialize HAP-python library, create bridge accessory, configure persistence directory
**FRs:** FR1, FR11
**Acceptance Criteria:**
- HAP-python installed and configured
- Bridge accessory starts on backend startup
- State persists across restarts in `backend/homekit/` directory
- Bridge runs independently of web UI

### Story P5-1.2: Implement HomeKit Pairing with QR Code
**Description:** Generate HomeKit setup code and QR code for pairing with Apple Home app
**FRs:** FR2
**Acceptance Criteria:**
- Setup code (XXX-XX-XXX format) generated securely
- QR code generated from setup URI
- Pairing completes successfully with Home app
- PIN not logged or persisted after pairing

### Story P5-1.3: Create Camera Accessory with RTSP-to-HLS Streaming
**Description:** Implement HomeKit Camera accessory that streams video from RTSP cameras
**FRs:** FR3, FR4
**Acceptance Criteria:**
- Each configured camera appears as HomeKit Camera accessory
- Live stream viewable in Apple Home app
- ffmpeg transcodes RTSP to SRTP format
- Stream latency under 500ms additional delay

### Story P5-1.4: Implement Motion Sensor Accessories
**Description:** Create HomeKit Motion Sensor accessories that trigger on ArgusAI motion detection
**FRs:** FR5
**Acceptance Criteria:**
- Motion sensor accessory created for each camera
- Sensor triggers when ArgusAI detects motion
- State resets after 3 seconds
- HomeKit automations can use motion triggers

### Story P5-1.5: Implement Occupancy Sensor for Person Detection
**Description:** Create HomeKit Occupancy Sensor that activates on person detection
**FRs:** FR6
**Acceptance Criteria:**
- Occupancy sensor accessory created for each camera
- Sensor activates only on person detection (not other motion)
- Occupancy state has 5-minute timeout
- Distinct from motion sensor in Home app

### Story P5-1.6: Add Vehicle/Animal/Package Sensor Accessories
**Description:** Create additional sensor accessories for vehicle, animal, and package detection types
**FRs:** FR7
**Acceptance Criteria:**
- Vehicle detection creates motion sensor trigger
- Animal detection creates motion sensor trigger
- Package detection creates motion sensor trigger
- Each detection type can trigger separate automations

### Story P5-1.7: Implement Doorbell Accessory for Protect Events
**Description:** Create HomeKit Doorbell accessory for Protect doorbell ring events
**FRs:** FR8
**Acceptance Criteria:**
- Doorbell accessory appears for Protect doorbell cameras
- Ring events trigger doorbell notification in Home app
- Notification appears on all paired devices
- Can trigger HomeKit automations

### Story P5-1.8: Build HomeKit Settings UI
**Description:** Create settings page for HomeKit enable/disable and pairing management
**FRs:** FR9, FR10, FR12
**Acceptance Criteria:**
- Toggle to enable/disable HomeKit bridge
- QR code displayed for pairing
- List of current pairings shown
- Ability to remove pairings
- Multiple iOS users can access shared accessories

---

## Epic P5-2: ONVIF Camera Discovery

**Priority:** High
**Goal:** Auto-discover ONVIF cameras on local network for simplified setup

### Story P5-2.1: Implement ONVIF WS-Discovery Scanner
**Description:** Create service to discover ONVIF-compatible cameras using WS-Discovery protocol
**FRs:** FR13, FR14
**Acceptance Criteria:**
- WS-Discovery probe sent to multicast address 239.255.255.250:3702
- Responses collected with 10-second timeout
- Works on typical home networks (up to 50 devices)
- Non-ONVIF devices gracefully ignored

### Story P5-2.2: Parse ONVIF Device Info and Capabilities
**Description:** Query discovered devices for manufacturer, model, and stream capabilities
**FRs:** FR15
**Acceptance Criteria:**
- Device name extracted from GetDeviceInformation
- Manufacturer and model displayed
- Available stream profiles enumerated
- RTSP URL extracted from Media service

### Story P5-2.3: Build Camera Discovery UI with Add Action
**Description:** Create UI to display discovered cameras and enable one-click add
**FRs:** FR16, FR19
**Acceptance Criteria:**
- "Discover Cameras" button triggers scan
- Loading state shown during discovery
- Discovered cameras listed with name, IP, manufacturer
- "Add" button auto-populates camera form
- Manual RTSP entry still available for non-ONVIF cameras

### Story P5-2.4: Implement Test Connection Endpoint
**Description:** Create API endpoint to test RTSP connection before saving camera
**FRs:** FR17, FR18
**Acceptance Criteria:**
- POST /api/v1/cameras/test endpoint created
- Validates RTSP URL format
- Tests connection with provided credentials
- Returns stream info (resolution, FPS, codec) on success
- Returns diagnostic error on failure

---

## Epic P5-3: CI/CD & Testing Infrastructure

**Priority:** High
**Goal:** Establish automated testing pipeline for code quality assurance

### Story P5-3.1: Create GitHub Actions Workflow for PRs
**Description:** Set up GitHub Actions workflow that runs on pull requests
**FRs:** FR20
**Acceptance Criteria:**
- Workflow file created at .github/workflows/ci.yml
- Triggers on push to main/development and PRs
- Runs backend and frontend jobs in parallel
- PR blocked if checks fail

### Story P5-3.2: Add Backend Pytest Execution to CI
**Description:** Configure CI to run backend Python tests with pytest
**FRs:** FR21
**Acceptance Criteria:**
- pytest runs in CI environment
- Test database configured (SQLite)
- Environment variables set from GitHub Secrets
- Failure fails the PR check

### Story P5-3.3: Set up Vitest + React Testing Library
**Description:** Configure frontend testing framework with Vitest and React Testing Library
**FRs:** FR26
**Acceptance Criteria:**
- vitest.config.ts created with jsdom environment
- vitest.setup.ts configured with jest-dom matchers
- @testing-library/react installed
- Sample test runs successfully locally

### Story P5-3.4: Add Frontend Test Execution to CI
**Description:** Configure CI to run frontend tests
**FRs:** FR22
**Acceptance Criteria:**
- npm run test executes in CI
- Tests run in headless jsdom environment
- Failure fails the PR check
- Test output visible in CI logs

### Story P5-3.5: Add ESLint and TypeScript Checks to CI
**Description:** Configure CI to run linting and type checking
**FRs:** FR23
**Acceptance Criteria:**
- npm run lint executes ESLint
- npx tsc --noEmit runs type checking
- Both must pass for PR to succeed
- Errors displayed in CI output

### Story P5-3.6: Configure Test Coverage Reporting
**Description:** Add coverage collection and reporting to CI
**FRs:** FR24
**Acceptance Criteria:**
- Backend coverage generated with pytest-cov
- Frontend coverage generated with vitest
- Coverage reports uploaded (Codecov or similar)
- Coverage visible in PR comments or CI output

### Story P5-3.7: Write FeedbackButtons Component Tests
**Description:** Create comprehensive unit tests for FeedbackButtons component
**FRs:** FR25
**Backlog:** TD-002
**Acceptance Criteria:**
- Tests for all button states (thumbs up, thumbs down)
- Tests for loading state
- Tests for disabled state
- Tests for click handlers
- Tests for accessibility (ARIA labels)

---

## Epic P5-4: Quality & Performance Validation

**Priority:** Medium
**Goal:** Document performance baselines and validate detection accuracy

### Story P5-4.1: Document CPU/Memory Performance Baselines
**Description:** Measure and document resource usage for reference configurations
**FRs:** FR27, FR28
**Backlog:** TD-004
**Acceptance Criteria:**
- CPU usage documented for 1, 2, 4 cameras at 5, 15, 30 FPS
- Memory usage documented under normal operation
- Baseline measurements taken on reference hardware
- Results published in docs/performance-baselines.md

### Story P5-4.2: Acquire and Organize Real Camera Test Footage
**Description:** Collect diverse video footage for testing detection accuracy
**FRs:** FR29
**Backlog:** TD-003
**Acceptance Criteria:**
- Test footage includes: person, vehicle, animal, package scenarios
- Day and night footage included
- Various camera angles represented
- Footage organized with ground truth labels

### Story P5-4.3: Validate Motion Detection Accuracy Metrics
**Description:** Run detection tests and measure accuracy against targets
**FRs:** FR30
**Acceptance Criteria:**
- Person detection rate measured (target: >90%)
- False positive rate measured (target: <20%)
- Results documented with methodology
- Areas for improvement identified

---

## Epic P5-5: UX Polish & Accessibility

**Priority:** Medium
**Goal:** Improve accessibility and add user-requested UX enhancements

### Story P5-5.1: Add ARIA Labels to All Interactive Elements
**Description:** Audit and add ARIA labels for screen reader compatibility
**FRs:** FR31
**Backlog:** IMP-004 (partial)
**Acceptance Criteria:**
- All buttons have aria-label
- Form inputs have associated labels
- Icons have aria-hidden or descriptive labels
- Dialogs have proper ARIA roles

### Story P5-5.2: Implement Keyboard Navigation for Core Workflows
**Description:** Ensure core workflows are fully keyboard navigable
**FRs:** FR32, FR33
**Backlog:** IMP-004 (partial)
**Acceptance Criteria:**
- Tab order is logical throughout app
- Focus states are visible (focus:ring-2)
- Modal dialogs trap focus
- Escape closes dialogs
- Enter activates buttons

### Story P5-5.3: Create Detection Zone Preset Templates
**Description:** Add preset zone templates for common detection configurations
**FRs:** FR34
**Backlog:** FF-018
**Acceptance Criteria:**
- Presets available: Full Frame, Top Half, Bottom Half, Center, L-Shape
- One-click application to zone editor
- Presets use normalized coordinates (0-1 range)
- Custom zones still supported

### Story P5-5.4: Implement Multiple Schedule Time Ranges
**Description:** Allow multiple active time ranges per day for detection schedules
**FRs:** FR35
**Backlog:** FF-016
**Acceptance Criteria:**
- Multiple time ranges per day supported
- UI allows adding/removing time ranges
- Database schema supports multiple ranges
- Schedule evaluation handles overlapping ranges

### Story P5-5.5: Update README with Frontend Setup Docs
**Description:** Add comprehensive frontend development documentation to README
**FRs:** FR36
**Backlog:** TD-005
**Acceptance Criteria:**
- Prerequisites documented (Node.js version)
- npm install and npm run dev commands
- Environment variable setup
- Common troubleshooting tips

---

## Epic P5-6: MQTT Enhancements

**Priority:** Low
**Goal:** Improve MQTT integration with 5.0 features

### Story P5-6.1: Add MQTT 5.0 Message Expiry Support
**Description:** Configure message expiry for MQTT event messages
**FRs:** FR37
**Backlog:** FF-012
**Acceptance Criteria:**
- Message expiry interval set on publish
- Expired messages not delivered
- Configurable expiry time in settings
- Works with MQTT 5.0 brokers

### Story P5-6.2: Implement MQTT Birth/Will Messages
**Description:** Add birth message on connect and will message for disconnection
**FRs:** FR38
**Backlog:** FF-013
**Acceptance Criteria:**
- Birth message published on successful connection
- Will message configured for unexpected disconnect
- Home Assistant shows online/offline status
- Messages use standard availability topic

---

## Summary

| Epic | Stories | Priority | Key Deliverable |
|------|---------|----------|-----------------|
| P5-1 | 8 | High | Native HomeKit integration |
| P5-2 | 4 | High | ONVIF camera auto-discovery |
| P5-3 | 7 | High | CI/CD pipeline with testing |
| P5-4 | 3 | Medium | Performance baselines |
| P5-5 | 5 | Medium | Accessibility & UX polish |
| P5-6 | 2 | Low | MQTT 5.0 enhancements |

**Total:** 6 epics, 29 stories
