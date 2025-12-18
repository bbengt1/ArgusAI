# Epic Technical Specification: HomeKit Troubleshooting & Fixes

Date: 2025-12-17
Author: Brent
Epic ID: P7-1
Status: Draft

---

## Overview

Epic P7-1 focuses on diagnosing and fixing HomeKit integration issues that prevent reliable pairing and event delivery to Apple Home app. The existing implementation uses HAP-python for the HomeKit Accessory Protocol but users report that the bridge is not discoverable or events are not delivered to paired devices. This epic adds comprehensive diagnostic logging, troubleshooting tools, and fixes for common issues including mDNS advertisement, network binding, and characteristic update propagation.

The implementation builds upon the existing HomeKit service (`backend/app/services/homekit_service.py`) and API endpoints (`backend/app/api/v1/homekit.py`) established in Phase 5, adding diagnostic capabilities and fixing reliability issues.

## Objectives and Scope

### In Scope
- Add comprehensive debug logging for HAP server lifecycle (start, stop, errors)
- Log all pairing attempts with success/failure status
- Log accessory characteristic updates (motion triggered, reset)
- Log network binding (IP, port) information
- Create diagnostic API endpoint returning recent HomeKit logs
- Display diagnostic info in Settings UI
- Investigate and fix mDNS/Bonjour advertisement issues
- Add network interface binding configuration
- Support binding to specific IP address (not just 0.0.0.0)
- Verify characteristic updates propagate to clients
- Add event delivery confirmation logging
- Add manual test trigger in UI
- Show real-time HomeKit connection health in UI

### Out of Scope
- HomeKit camera streaming fixes (covered in P7-3)
- Package delivery detection (covered in P7-2)
- Entity recognition and alerts (covered in P7-4)
- Adding new sensor types beyond existing motion/occupancy/vehicle/animal/package/doorbell

## System Architecture Alignment

This epic aligns with the Phase 5 HomeKit architecture:

**Components Modified:**
- `backend/app/services/homekit_service.py` - Add diagnostic logging, mDNS fixes
- `backend/app/config/homekit.py` - Add bind address configuration
- `backend/app/api/v1/homekit.py` - Add diagnostics endpoint
- `frontend/components/settings/HomeKitSettings.tsx` - Add diagnostics panel

**Architecture Constraints:**
- HAP-python 4.9+ required for proper mDNS advertisement
- Port 51826 (default) must be accessible on the network
- UDP port 5353 required for mDNS/Bonjour
- Bridge runs as separate background thread from main asyncio loop

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|----------------|----------------|--------|---------|
| `HomekitDiagnosticService` | Collect and manage diagnostic logs | Log events | Diagnostic log entries |
| `HomekitService.diagnostics` | Extension for diagnostic methods | Service state | Diagnostic data |
| `homekit.py` API | Expose diagnostics endpoint | HTTP request | JSON diagnostics |
| `HomeKitDiagnostics.tsx` | Display diagnostics in UI | API response | Rendered diagnostics |

### Data Models and Contracts

**HomeKitDiagnosticEntry (new Pydantic schema):**
```python
class HomeKitDiagnosticEntry(BaseModel):
    timestamp: datetime
    level: str  # 'debug', 'info', 'warning', 'error'
    category: str  # 'lifecycle', 'pairing', 'event', 'network', 'mdns'
    message: str
    details: Optional[dict] = None
```

**HomeKitDiagnosticsResponse (new Pydantic schema):**
```python
class HomeKitDiagnosticsResponse(BaseModel):
    bridge_running: bool
    mdns_advertising: bool
    network_binding: dict  # {ip: str, port: int, interface: Optional[str]}
    connected_clients: int
    last_event_delivery: Optional[dict]  # {camera_id, sensor_type, timestamp}
    recent_logs: List[HomeKitDiagnosticEntry]
    warnings: List[str]
    errors: List[str]
```

**HomeKitConfig additions:**
```python
@dataclass
class HomekitConfig:
    # Existing fields...
    bind_address: str = "0.0.0.0"  # New: specific IP or 0.0.0.0 for all
    mdns_interface: Optional[str] = None  # New: specific network interface
    diagnostic_log_size: int = 100  # New: max log entries to retain
```

### APIs and Interfaces

**New Endpoint: GET /api/v1/homekit/diagnostics**

Returns comprehensive diagnostic information for troubleshooting.

```
GET /api/v1/homekit/diagnostics

Response 200:
{
  "bridge_running": true,
  "mdns_advertising": true,
  "network_binding": {
    "ip": "192.168.1.100",
    "port": 51826,
    "interface": "en0"
  },
  "connected_clients": 2,
  "last_event_delivery": {
    "camera_id": "abc-123",
    "sensor_type": "motion",
    "timestamp": "2025-12-17T10:30:00Z",
    "delivered": true
  },
  "recent_logs": [
    {
      "timestamp": "2025-12-17T10:30:00Z",
      "level": "info",
      "category": "event",
      "message": "Motion triggered for Front Door",
      "details": {"camera_id": "abc-123", "reset_seconds": 30}
    }
  ],
  "warnings": [],
  "errors": []
}
```

**New Endpoint: POST /api/v1/homekit/test-event**

Manually trigger a motion event for testing.

```
POST /api/v1/homekit/test-event
{
  "camera_id": "abc-123",
  "event_type": "motion"  // "motion", "occupancy", "vehicle", "animal", "package", "doorbell"
}

Response 200:
{
  "success": true,
  "message": "Motion event triggered for Front Door",
  "delivered_to_clients": 2
}
```

**New Endpoint: POST /api/v1/homekit/test-connectivity**

Test mDNS discovery visibility.

```
POST /api/v1/homekit/test-connectivity

Response 200:
{
  "mdns_visible": true,
  "discovered_as": "ArgusAI._hap._tcp.local",
  "port_accessible": true,
  "firewall_issues": []
}
```

### Workflows and Sequencing

**Diagnostic Data Collection Flow:**
```
1. HomekitService logs event (logger with custom handler)
      ↓
2. HomekitDiagnosticHandler captures log entry
      ↓
3. Entry added to circular buffer (max 100 entries)
      ↓
4. API endpoint returns recent logs on request
      ↓
5. UI polls /diagnostics every 5 seconds when panel open
```

**mDNS Discovery Fix Flow:**
```
1. User enables HomeKit
      ↓
2. Service starts with configured bind_address
      ↓
3. HAP-python registers service with Avahi/mDNSResponder
      ↓
4. If bind_address != 0.0.0.0, pass specific interface
      ↓
5. Log mDNS registration success/failure
      ↓
6. UI shows advertising status
```

## Non-Functional Requirements

### Performance

- Diagnostic log retrieval: < 100ms response time
- Log buffer memory: < 1MB (100 entries max)
- Diagnostic polling: 5-second intervals (configurable)
- No performance impact on event processing when diagnostics disabled

### Security

- Diagnostic logs must NOT contain sensitive data (PIN codes, pairing keys)
- API endpoint requires authentication (same as other HomeKit endpoints)
- No exposure of internal network topology beyond what's needed

### Reliability/Availability

- Diagnostic collection must not crash the HomeKit service
- Log buffer uses circular buffer to prevent memory growth
- mDNS fixes should handle network interface changes gracefully
- Event delivery logging must not block characteristic updates

### Observability

- Structured logging with category tags for filtering
- Prometheus metrics for event delivery success/failure rate
- Log levels: DEBUG for verbose, INFO for normal operation
- Error logs for all failures with stack traces

## Dependencies and Integrations

| Dependency | Version | Purpose |
|------------|---------|---------|
| HAP-python | 4.9+ | HomeKit Accessory Protocol |
| zeroconf | 0.132+ | mDNS/Bonjour (via HAP-python) |
| qrcode | 7.0+ | QR code generation (existing) |

**Integration Points:**
- HomeKit service (existing)
- Camera service (for test events)
- Frontend Settings page (for UI)
- Logging infrastructure (python-json-logger)

## Acceptance Criteria (Authoritative)

### Story P7-1.1: Add HomeKit Diagnostic Logging
1. Debug logging for HAP server lifecycle (start, stop, errors) is implemented
2. All pairing attempts are logged with success/failure status
3. Accessory characteristic updates (motion triggered, reset) are logged
4. Network binding (IP, port) information is logged
5. `/api/v1/homekit/diagnostics` endpoint returns recent logs
6. Diagnostic info is displayed in Settings UI

### Story P7-1.2: Fix HomeKit Bridge Discovery Issues
1. HAP-python mDNS advertisement is verified working
2. Test with avahi-browse/dns-sd confirms service visibility
3. Network interface binding configuration is added
4. Support binding to specific IP address (not just 0.0.0.0)
5. Firewall requirements documented (UDP 5353 for mDNS)
6. Connectivity test button is added in UI

### Story P7-1.3: Fix HomeKit Event Delivery
1. Characteristic updates are verified to propagate to clients
2. Event delivery confirmation logging is added
3. Testing with multiple paired devices works
4. Auto-reset timers work correctly
5. Manual test button triggers motion in UI

### Story P7-1.4: Add HomeKit Connection Status Monitoring
1. mDNS advertisement status shown (advertising/not advertising)
2. Connected clients count displayed
3. Last event delivery timestamp shown per sensor
4. Errors and warnings are displayed
5. Auto-refresh status every 5 seconds when panel open

## Traceability Mapping

| AC# | Spec Section | Component/API | Test Idea |
|-----|--------------|---------------|-----------|
| P7-1.1-1 | Detailed Design / Services | HomekitService logging | Unit: verify log entries created on start/stop |
| P7-1.1-2 | Detailed Design / Services | HomekitService pairing | Unit: mock pairing flow, check logs |
| P7-1.1-3 | Detailed Design / Services | trigger_motion() | Unit: verify log entry on motion |
| P7-1.1-4 | Detailed Design / Services | _run_driver() | Unit: verify network info logged |
| P7-1.1-5 | APIs / GET diagnostics | homekit.py | Integration: call endpoint, verify response |
| P7-1.1-6 | Workflows | HomeKitDiagnostics.tsx | E2E: open settings, verify panel displays |
| P7-1.2-1 | NFRs / Reliability | HAP-python start() | Manual: use avahi-browse to verify |
| P7-1.2-2 | NFRs / Reliability | AccessoryDriver | Manual: dns-sd -B _hap._tcp |
| P7-1.2-3 | Data Models / HomekitConfig | bind_address field | Unit: config parsing |
| P7-1.2-4 | Data Models / HomekitConfig | bind_address | Integration: bind to specific IP |
| P7-1.2-5 | NFRs / Security | Documentation | Doc review |
| P7-1.2-6 | APIs / POST test-connectivity | homekit.py | Integration: test endpoint response |
| P7-1.3-1 | Workflows / Event Delivery | HomekitService | Integration: trigger motion, verify propagation |
| P7-1.3-2 | NFRs / Observability | trigger_motion() | Unit: verify delivery logged |
| P7-1.3-3 | NFRs / Reliability | Multiple devices | Manual: pair 2+ devices, verify both receive |
| P7-1.3-4 | Workflows / Timer Reset | _motion_reset_coroutine | Unit: verify timer behavior |
| P7-1.3-5 | APIs / POST test-event | homekit.py | Integration: call endpoint, verify motion |
| P7-1.4-1 | APIs / GET diagnostics | mdns_advertising field | Unit: verify field populated |
| P7-1.4-2 | APIs / GET diagnostics | connected_clients field | Unit: mock clients, verify count |
| P7-1.4-3 | APIs / GET diagnostics | last_event_delivery field | Unit: trigger event, check timestamp |
| P7-1.4-4 | APIs / GET diagnostics | warnings/errors lists | Unit: inject error, verify in response |
| P7-1.4-5 | Workflows / UI Polling | HomeKitDiagnostics.tsx | E2E: verify 5s polling with React Query |

## Risks, Assumptions, Open Questions

### Risks
- **R1:** HAP-python mDNS issues may be upstream bugs requiring library updates
  - *Mitigation:* Test with latest HAP-python, document workarounds
- **R2:** Network environment variations (Docker, VMs) may affect mDNS
  - *Mitigation:* Document network requirements, add diagnostic output
- **R3:** Apple Home app behavior is not fully documented
  - *Mitigation:* Test with real devices, gather user feedback

### Assumptions
- **A1:** User has network access on ports 51826 (TCP) and 5353 (UDP)
- **A2:** HAP-python 4.9+ provides reliable mDNS through zeroconf
- **A3:** macOS/iOS Home app follows HAP specification for discovery

### Open Questions
- **Q1:** Should we support multiple network interfaces simultaneously?
  - *Recommendation:* Start with single interface binding, add multi-interface in future if needed
- **Q2:** How long should diagnostic logs be retained?
  - *Recommendation:* 100 entries (configurable), cleared on service restart

## Test Strategy Summary

### Unit Tests
- HomeKit diagnostic service log capture and retrieval
- Config parsing for new bind_address and interface fields
- Event delivery logging in trigger_motion(), trigger_occupancy(), etc.
- Circular buffer behavior for log retention

### Integration Tests
- `/api/v1/homekit/diagnostics` endpoint returns valid response
- `/api/v1/homekit/test-event` triggers motion on correct sensor
- `/api/v1/homekit/test-connectivity` returns mDNS status
- HomeKit service starts with custom bind address

### Manual/E2E Tests
- Verify mDNS discovery with avahi-browse (Linux) or dns-sd (macOS)
- Pair with Apple Home app, verify bridge appears
- Trigger motion, verify notification in Home app
- Open Settings > HomeKit, verify diagnostics panel updates every 5s
- Test with 2+ paired iOS devices simultaneously

### Tools
- pytest for backend tests
- Vitest + React Testing Library for frontend
- avahi-browse / dns-sd for mDNS verification
- Apple Home app for real-world testing
