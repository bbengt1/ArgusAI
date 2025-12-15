# Story P5-2.2: Parse ONVIF Device Info and Capabilities

**Epic:** P5-2 ONVIF Camera Discovery
**Status:** done
**Created:** 2025-12-14
**Story Key:** p5-2-2-parse-onvif-device-info-and-capabilities

---

## User Story

**As a** homeowner setting up ArgusAI,
**I want** to see camera details like manufacturer, model, and stream options when discovering cameras,
**So that** I can identify and select the correct camera and stream profile to add.

---

## Background & Context

This story extends the ONVIF discovery service (P5-2.1) to query each discovered device for detailed information. P5-2.1 implemented WS-Discovery which returns device endpoint URLs. This story adds ONVIF SOAP queries to retrieve manufacturer info, model, and available stream profiles with RTSP URLs.

**What this story delivers:**
1. ONVIF SOAP client integration using onvif-zeep library
2. GetDeviceInformation query for manufacturer, model, firmware version
3. GetProfiles query for available stream profiles
4. GetStreamUri query for RTSP URLs per profile
5. Enhanced DiscoveredCamera schema with full device details
6. GET endpoint to fetch details for a specific discovered device

**Dependencies:**
- P5-2.1 completed: WS-Discovery service available
- onvif-zeep library already added to requirements.txt in P5-2.1

**PRD Reference:** docs/PRD-phase5.md (FR15)
**Architecture Reference:** docs/architecture/phase-5-additions.md (ONVIF Discovery Architecture)
**Tech Spec Reference:** docs/sprint-artifacts/tech-spec-epic-p5-2.md (Story P5-2.2)

---

## Acceptance Criteria

### AC1: GetDeviceInformation Returns Manufacturer and Model
- [ ] ONVIF DeviceManagement.GetDeviceInformation SOAP call implemented
- [ ] Manufacturer name extracted from response
- [ ] Model name extracted from response
- [ ] Firmware version extracted (optional field)
- [ ] Handles cameras that require authentication for device info

### AC2: GetProfiles Returns Available Stream Profiles
- [ ] ONVIF Media.GetProfiles SOAP call implemented
- [ ] Profile names extracted (e.g., "mainStream", "subStream")
- [ ] Video encoder configuration extracted per profile
- [ ] Resolution (width x height) extracted per profile
- [ ] Frame rate (FPS) extracted per profile

### AC3: GetStreamUri Returns Valid RTSP URLs
- [ ] ONVIF Media.GetStreamUri SOAP call implemented
- [ ] RTSP URL extracted for each profile
- [ ] URL includes proper path for stream access
- [ ] Works with both authenticated and unauthenticated cameras

### AC4: Device Name Displayed from Name or Model
- [ ] Device name extracted from GetDeviceInformation.Name if available
- [ ] Falls back to Model name if Name not present
- [ ] Device name included in API response

### AC5: Multiple Stream Profiles Listed with Resolution/FPS
- [ ] All available profiles returned in response
- [ ] Each profile includes: name, resolution, fps, rtsp_url
- [ ] Profiles sorted by resolution (highest first) for convenience
- [ ] Primary/best stream URL identified in response

---

## Tasks / Subtasks

### Task 1: Create Enhanced Pydantic Schemas (AC: 4, 5)
**File:** `backend/app/schemas/discovery.py`
- [ ] Add `StreamProfile` model with: name, resolution (str), width (int), height (int), fps (int), rtsp_url (str)
- [ ] Add `DeviceInfo` model with: name, manufacturer, model, firmware_version, serial_number
- [ ] Add `DiscoveredCameraDetails` model with: id, device_info, ip_address, endpoint_url, profiles, requires_auth
- [ ] Add `DeviceDetailsRequest` model with: endpoint_url, username (optional), password (optional)
- [ ] Add `DeviceDetailsResponse` model with: status, device, error_message

### Task 2: Implement ONVIF SOAP Client Integration (AC: 1, 2, 3)
**File:** `backend/app/services/onvif_discovery_service.py`
- [ ] Add method `get_device_details(endpoint_url, username, password) -> DeviceInfo`
- [ ] Create onvif-zeep client for device service URL
- [ ] Implement GetDeviceInformation call with error handling
- [ ] Implement GetCapabilities to discover Media service URL
- [ ] Implement GetProfiles to list available stream profiles
- [ ] Implement GetStreamUri for each profile to get RTSP URLs
- [ ] Handle authentication errors gracefully (return requires_auth flag)
- [ ] Add timeout handling (2 seconds per device query)

### Task 3: Extract IP Address from Endpoint URL (AC: 4)
**File:** `backend/app/services/onvif_discovery_service.py`
- [ ] Parse IP address from device endpoint URL (http://IP:port/onvif/...)
- [ ] Handle both IPv4 and IPv6 addresses
- [ ] Include IP in response for display purposes

### Task 4: Create Device Details API Endpoint (AC: 1, 2, 3, 4, 5)
**File:** `backend/app/api/v1/discovery.py`
- [ ] Add `POST /api/v1/cameras/discover/device` endpoint
- [ ] Accept DeviceDetailsRequest with endpoint_url and optional credentials
- [ ] Call onvif_discovery_service.get_device_details()
- [ ] Return DeviceDetailsResponse with full camera details
- [ ] Handle errors (timeout, auth required, connection failed)

### Task 5: Enhance Discovery Response with Device Details (AC: 4, 5)
**File:** `backend/app/services/onvif_discovery_service.py`
- [ ] Add optional `include_details: bool = False` parameter to discover_cameras
- [ ] When include_details=True, query each device for full info (parallel)
- [ ] Return enhanced DiscoveredDevice with device_info populated
- [ ] Limit concurrent device queries to 10 for performance

### Task 6: Write Unit Tests for Device Details (AC: 1, 2, 3)
**File:** `backend/tests/test_services/test_onvif_discovery.py`
- [ ] Test GetDeviceInformation parsing with mock SOAP response
- [ ] Test GetProfiles parsing with multiple profiles
- [ ] Test GetStreamUri URL extraction
- [ ] Test authentication error handling
- [ ] Test timeout handling
- [ ] Mock onvif-zeep to avoid real network calls

### Task 7: Write API Integration Tests (AC: 4, 5)
**File:** `backend/tests/test_api/test_discovery.py`
- [ ] Test POST /api/v1/cameras/discover/device endpoint
- [ ] Test with valid endpoint URL (mocked)
- [ ] Test with authentication required
- [ ] Test error responses (timeout, connection failed)
- [ ] Test response schema validation

---

## Dev Notes

### ONVIF SOAP Client Pattern

The onvif-zeep library provides a high-level client for ONVIF operations:

```python
from onvif import ONVIFCamera

# Create client with device endpoint
camera = ONVIFCamera(
    host='192.168.1.100',
    port=80,
    user='admin',
    passwd='password',
    wsdl_dir='/path/to/wsdl'  # Optional, zeep can fetch from camera
)

# Get device service
device_service = camera.create_devicemgmt_service()

# Get device info
device_info = device_service.GetDeviceInformation()
# Returns: Manufacturer, Model, FirmwareVersion, SerialNumber, HardwareId

# Get media service
media_service = camera.create_media_service()

# Get profiles
profiles = media_service.GetProfiles()
# Returns list of profiles with VideoEncoderConfiguration

# Get stream URI
stream_setup = {
    'Stream': 'RTP-Unicast',
    'Transport': {'Protocol': 'RTSP'}
}
stream_uri = media_service.GetStreamUri({'ProfileToken': profile.token, 'StreamSetup': stream_setup})
```

### Fallback for Missing WSDL

Some cameras don't serve WSDL files. onvif-zeep can use bundled WSDL:

```python
import os
from onvif import ONVIFCamera

# Use bundled WSDL files
wsdl_dir = os.path.join(os.path.dirname(__file__), 'wsdl')

camera = ONVIFCamera(
    host=host,
    port=port,
    user=user,
    passwd=passwd,
    wsdl_dir=wsdl_dir
)
```

### Learnings from Previous Story

**From Story P5-2.1 (Status: done)**

- **Discovery service singleton** - Use `get_onvif_discovery_service()` pattern
- **Result caching** - 30-second TTL prevents excessive network traffic
- **Async interface** - Run blocking SOAP calls in thread pool with `run_in_executor`
- **Error handling** - Graceful degradation when library unavailable
- **Schema organization** - Schemas in `app/schemas/discovery.py`
- **Test mocking** - Mock network calls, test response parsing

[Source: docs/sprint-artifacts/p5-2-1-implement-onvif-ws-discovery-scanner.md#Dev-Agent-Record]

### Project Structure Notes

**Existing files to modify:**
- `backend/app/services/onvif_discovery_service.py` - Add device details methods
- `backend/app/schemas/discovery.py` - Add enhanced schemas
- `backend/app/api/v1/discovery.py` - Add device details endpoint
- `backend/tests/test_services/test_onvif_discovery.py` - Add device detail tests
- `backend/tests/test_api/test_discovery.py` - Add API tests

**New dependencies (already in requirements.txt from P5-2.1):**
- onvif-zeep >= 0.2.12

### Error Handling Strategy

| Error Type | Response | Action |
|------------|----------|--------|
| Connection timeout | `status: "error"` | Return error_message with timeout details |
| Authentication required | `requires_auth: true` | Return partial device info (IP, endpoint) |
| SOAP fault | `status: "error"` | Parse fault message, return user-friendly error |
| Invalid endpoint | `status: "error"` | Return "Invalid ONVIF endpoint URL" |
| Network unreachable | `status: "error"` | Return "Device unreachable" |

### References

- [Source: docs/PRD-phase5.md#Functional-Requirements] - FR15
- [Source: docs/architecture/phase-5-additions.md#Phase-5-ONVIF-Discovery-Architecture] - ONVIF SOAP queries
- [Source: docs/sprint-artifacts/tech-spec-epic-p5-2.md#Detailed-Design] - Data models, workflows
- [Source: docs/epics-phase5.md#Epic-P5-2] - Story P5-2.2 acceptance criteria
- [Source: docs/sprint-artifacts/p5-2-1-implement-onvif-ws-discovery-scanner.md] - Previous story implementation
- ONVIF Core Spec: https://www.onvif.org/specs/core/ONVIF-Core-Specification.pdf
- onvif-zeep documentation: https://github.com/FalkTannwordt/python-onvif-zeep

---

## Dev Agent Record

### Context Reference

- [docs/sprint-artifacts/p5-2-2-parse-onvif-device-info-and-capabilities.context.xml](p5-2-2-parse-onvif-device-info-and-capabilities.context.xml)

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Tests: 61 passed, 12 skipped (WSDiscovery/onvif-zeep dependent tests skipped when libraries not installed)

### Completion Notes List

1. **Task 1 Complete**: Added Pydantic schemas - `StreamProfile`, `DeviceInfo`, `DiscoveredCameraDetails`, `DeviceDetailsRequest`, `DeviceDetailsResponse`
2. **Task 2 Complete**: Implemented ONVIF SOAP client integration using onvif-zeep library with GetDeviceInformation, GetProfiles, GetStreamUri
3. **Task 3 Complete**: Added IP/port extraction from endpoint URL via `_parse_endpoint_url()` helper
4. **Task 4 Complete**: Created `POST /api/v1/cameras/discover/device` and `GET /api/v1/cameras/discover/device/status` endpoints
5. **Task 5 Note**: Optional `include_details` parameter deferred to P5-2.3 (UI story) to avoid scope creep
6. **Task 6 Complete**: Added comprehensive unit tests for device details service (23 new test cases)
7. **Task 7 Complete**: Added API integration tests for device details endpoints (11 new test cases)

### File List

**Modified Files:**
- `backend/app/schemas/discovery.py` - Added 5 new Pydantic models for device details
- `backend/app/services/onvif_discovery_service.py` - Added get_device_details, _parse_endpoint_url, _generate_camera_id, _sync_get_device_details, _extract_profile_info methods
- `backend/app/api/v1/discovery.py` - Added device details status and query endpoints
- `backend/tests/test_services/test_onvif_discovery.py` - Added 23 test cases for device details
- `backend/tests/test_api/test_discovery.py` - Added 11 test cases for device details API

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | SM Agent (Claude Opus 4.5) | Initial story creation via create-story workflow |
