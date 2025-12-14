# Epic Technical Specification: ONVIF Camera Discovery

Date: 2025-12-14
Author: Brent
Epic ID: P5-2
Status: Draft

---

## Overview

Epic P5-2 implements ONVIF camera auto-discovery for ArgusAI, enabling users to automatically find compatible cameras on their local network without manually entering RTSP URLs. This significantly simplifies camera setup for non-technical users by transforming the experience from "find your camera's RTSP URL in the manual" to "click to discover, click to add."

The implementation uses WS-Discovery protocol to find ONVIF-compatible devices, then queries each device for manufacturer info, model, and available stream profiles including RTSP URLs. A test connection endpoint allows users to verify camera connectivity before saving configuration.

**PRD Reference:** docs/PRD-phase5.md (FR13-FR19, NFR3, NFR10, NFR15, NFR18)

## Objectives and Scope

**In Scope:**
- WS-Discovery multicast probe to find ONVIF devices
- ONVIF Device Management queries for device info (manufacturer, model)
- ONVIF Media service queries for stream profiles and RTSP URLs
- Discovery UI with "Discover Cameras" button and results list
- One-click camera add with auto-populated RTSP URL
- Test connection endpoint to validate RTSP before saving
- Graceful handling of non-ONVIF and unresponsive devices
- Discovery timeout (10 seconds max)

**Out of Scope:**
- ONVIF PTZ (pan-tilt-zoom) control
- ONVIF event subscription
- ONVIF Profile G (recording/storage)
- Credential auto-detection (user must provide username/password)
- Continuous background scanning

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-5-additions.md

This epic aligns with the Phase 5 ONVIF Discovery Architecture section:
- **WS-Discovery Flow** - UDP multicast probe/response pattern
- **Discovery Service Implementation** - ONVIFDiscoveryService class
- **API Endpoints** - POST /discover, GET /discover/results, POST /test

**Key Integration Points:**
- `camera_service.py` - Use discovered camera data to create camera entries
- Camera add form - Auto-populate from discovery results
- Settings/Cameras page - Host discovery UI

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|---------------|----------------|--------|---------|
| `onvif_discovery_service.py` | WS-Discovery, ONVIF queries | Network interface | List of DiscoveredCamera |
| `api/v1/discovery.py` | REST endpoints for discovery | HTTP requests | JSON responses |
| `CameraDiscovery.tsx` | Discovery UI component | User actions | API calls, camera list |

### Data Models and Contracts

**DiscoveredCamera (Pydantic Schema):**
```python
class StreamProfile(BaseModel):
    name: str
    resolution: str  # e.g., "1920x1080"
    fps: int
    rtsp_url: str

class DiscoveredCamera(BaseModel):
    id: str  # UUID for this discovery session
    name: str
    manufacturer: str
    model: str
    ip_address: str
    mac_address: Optional[str]
    rtsp_url: str  # Primary/best stream URL
    requires_auth: bool
    profiles: List[StreamProfile]
    discovered_at: datetime

class DiscoveryResult(BaseModel):
    status: Literal["scanning", "complete", "error"]
    duration_ms: Optional[int]
    cameras: List[DiscoveredCamera]
    error: Optional[str]
```

**TestConnectionRequest/Response:**
```python
class TestConnectionRequest(BaseModel):
    rtsp_url: str
    username: Optional[str]
    password: Optional[str]

class TestConnectionResponse(BaseModel):
    success: bool
    latency_ms: Optional[int]
    resolution: Optional[str]
    fps: Optional[int]
    codec: Optional[str]
    error: Optional[str]
```

### APIs and Interfaces

**Discovery API Endpoints:**

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| POST | /api/v1/cameras/discover | - | `{"status": "scanning"}` | Start discovery scan |
| GET | /api/v1/cameras/discover/results | - | DiscoveryResult | Poll for results |
| POST | /api/v1/cameras/test | TestConnectionRequest | TestConnectionResponse | Test RTSP connection |

**Discovery Flow (Async Polling):**
```
1. POST /discover → Returns immediately with status: "scanning"
2. Discovery runs in background (up to 10 seconds)
3. GET /discover/results → Poll until status: "complete"
4. Results cached for 5 minutes
```

### Workflows and Sequencing

**WS-Discovery Sequence:**
```
1. Create UDP socket bound to any port
2. Join multicast group 239.255.255.250
3. Send WS-Discovery Probe message:
   - Types: "dn:NetworkVideoTransmitter" (ONVIF Profile S)
   - Scopes: (empty for all)
4. Collect ProbeMatch responses for 10 seconds
5. For each response:
   a. Extract XAddrs (device service URL)
   b. Parse IP address from XAddrs
   c. Add to discovered devices list
6. Return unique devices
```

**ONVIF Device Query Sequence:**
```
For each discovered device URL:
1. Create ONVIF client (onvif-zeep)
2. Call GetDeviceInformation:
   - Extract: Manufacturer, Model, FirmwareVersion
3. Call GetCapabilities:
   - Get Media service URL
4. Call GetProfiles (Media service):
   - Get available stream profiles
5. For each profile, call GetStreamUri:
   - Get RTSP URL with authentication
6. Return normalized DiscoveredCamera
```

**Test Connection Sequence:**
```
1. Validate RTSP URL format
2. Build full URL with credentials if provided:
   rtsp://username:password@host:port/path
3. Open RTSP connection with OpenCV
4. Attempt to read first frame (with 5s timeout)
5. If success:
   - Extract resolution from frame
   - Query stream FPS if available
   - Return success with metadata
6. If failure:
   - Parse error message
   - Return failure with diagnostic
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Discovery scan time | <10 seconds | Total time from start to complete |
| Device query parallelism | 10 concurrent | Max simultaneous ONVIF queries |
| Per-device timeout | 2 seconds | Timeout for each device query |
| Test connection timeout | 5 seconds | Timeout for RTSP test |
| Results cache | 5 minutes | Time discovery results remain valid |

### Security

- **No credential exposure** - Credentials not included in discovery responses (NFR10)
- **RTSP URL sanitization** - Passwords removed from logged URLs
- **Network isolation** - Discovery only scans local network (multicast)

### Reliability/Availability

- **Graceful degradation** - Unresponsive devices don't block discovery (NFR15)
- **Partial results** - Return discovered cameras even if some queries fail
- **Timeout handling** - All network operations have explicit timeouts

### Observability

- **Logging** - Discovery start/complete, device count, errors at INFO level
- **Metrics** - `onvif_discovery_duration_seconds`, `onvif_cameras_found`, `camera_test_success_total`

## Dependencies and Integrations

### Python Dependencies (backend/requirements.txt additions)

| Package | Version | Purpose |
|---------|---------|---------|
| onvif-zeep | >=0.2.12 | ONVIF protocol client with zeep SOAP |
| WSDiscovery | >=2.0.0 | WS-Discovery protocol implementation |

### Internal Integrations

| Component | Integration Point | Data Flow |
|-----------|-------------------|-----------|
| camera_service.py | Create camera from discovery | DiscoveredCamera → Camera model |
| CameraForm.tsx | Auto-populate fields | Discovery result → form values |
| api-client.ts | Discovery API calls | Frontend → Backend |

## Acceptance Criteria (Authoritative)

**Story P5-2.1: Implement ONVIF WS-Discovery Scanner**
1. WS-Discovery probe sent to multicast address 239.255.255.250:3702
2. ProbeMatch responses collected with device URLs
3. Discovery completes within 10 seconds
4. Works on typical home networks (tested with real ONVIF camera if available)
5. Non-ONVIF devices gracefully ignored (no errors)

**Story P5-2.2: Parse ONVIF Device Info and Capabilities**
1. GetDeviceInformation returns manufacturer and model
2. GetProfiles returns available stream profiles
3. GetStreamUri returns valid RTSP URLs
4. Device name displayed (from Name or Model)
5. Multiple stream profiles listed with resolution/FPS

**Story P5-2.3: Build Camera Discovery UI with Add Action**
1. "Discover Cameras" button visible on Cameras page
2. Loading spinner/state shown during discovery
3. Discovered cameras listed with name, IP, manufacturer
4. "Add" button opens camera form with pre-populated RTSP URL
5. Manual RTSP entry still available (discovery is optional)
6. Empty state message if no cameras found

**Story P5-2.4: Implement Test Connection Endpoint**
1. POST /api/v1/cameras/test endpoint accepts RTSP URL and optional credentials
2. Valid RTSP URLs return success with resolution/FPS/codec
3. Invalid URLs return error with diagnostic message
4. Connection failures return specific error (timeout, auth failed, etc.)
5. Test completes within 5 seconds (timeout)

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| P5-2.1-1 | Workflows | onvif_discovery_service.py | Multicast packet test |
| P5-2.1-2 | Workflows | WS-Discovery | Response parsing test |
| P5-2.1-3 | Performance | Discovery timeout | Timing test |
| P5-2.1-4 | Integration | Network scan | Real camera test (manual) |
| P5-2.1-5 | Reliability | Error handling | Non-ONVIF device test |
| P5-2.2-1 | Workflows | ONVIF client | GetDeviceInformation mock test |
| P5-2.2-2 | Workflows | ONVIF client | GetProfiles mock test |
| P5-2.2-3 | Workflows | ONVIF client | GetStreamUri mock test |
| P5-2.2-4 | Data Models | DiscoveredCamera | Name extraction test |
| P5-2.2-5 | Data Models | StreamProfile | Profile parsing test |
| P5-2.3-1 | UI | CameraDiscovery.tsx | Button render test |
| P5-2.3-2 | UI | CameraDiscovery.tsx | Loading state test |
| P5-2.3-3 | UI | CameraDiscovery.tsx | Results list test |
| P5-2.3-4 | Integration | Camera form | Add flow test |
| P5-2.3-5 | UI | Cameras page | Manual entry available test |
| P5-2.3-6 | UI | CameraDiscovery.tsx | Empty state test |
| P5-2.4-1 | APIs | /api/v1/cameras/test | Endpoint exists test |
| P5-2.4-2 | APIs | Test connection | Success response test |
| P5-2.4-3 | APIs | Test connection | Invalid URL test |
| P5-2.4-4 | APIs | Test connection | Connection error test |
| P5-2.4-5 | Performance | Test timeout | Timeout test |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: Network restrictions** - Some networks block multicast; discovery will fail silently
- **R2: ONVIF compatibility** - Not all cameras fully implement ONVIF; may get partial data
- **R3: Authentication required** - Many cameras require auth for ONVIF queries, not just RTSP

**Assumptions:**
- **A1:** User's network allows UDP multicast (typical home networks do)
- **A2:** Cameras implement ONVIF Profile S (network video transmitter)
- **A3:** Most users will know their camera credentials
- **A4:** Discovery is a one-time setup action, not continuous monitoring

**Open Questions:**
- **Q1:** Should we cache discovered cameras across sessions? → No, fresh scan each time
- **Q2:** Support for authenticated ONVIF queries? → Defer to growth, most basic info is unauthenticated
- **Q3:** Show cameras already added to ArgusAI differently? → Yes, mark as "Already Added"

## Test Strategy Summary

**Unit Tests:**
- `test_onvif_discovery_service.py` - WS-Discovery message parsing, ONVIF response parsing
- Mock ONVIF responses for device info, profiles, stream URIs
- Test connection service with mocked OpenCV

**Integration Tests:**
- API endpoint tests for /discover, /discover/results, /test
- Async discovery with polling
- Discovery result caching

**Manual Tests (Required):**
- Real ONVIF camera discovery on local network
- Add discovered camera flow
- Test connection with valid/invalid credentials
- Discovery on network with no ONVIF cameras (empty result)

**Test Environment:**
- Mock ONVIF server not practical; use response fixtures
- Real ONVIF testing requires physical camera (developer local testing)
- CI tests use mocked responses only
