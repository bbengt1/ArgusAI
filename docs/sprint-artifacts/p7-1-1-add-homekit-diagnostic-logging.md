# Story P7-1.1: Add HomeKit Diagnostic Logging

Status: done

## Story

As a **system administrator**,
I want **comprehensive diagnostic logging for the HomeKit bridge including lifecycle events, pairing attempts, and characteristic updates**,
so that **I can troubleshoot HomeKit discovery and event delivery issues effectively**.

## Acceptance Criteria

1. Debug logging for HAP server lifecycle (start, stop, errors) is implemented
2. All pairing attempts are logged with success/failure status
3. Accessory characteristic updates (motion triggered, reset) are logged
4. Network binding (IP, port) information is logged
5. `/api/v1/homekit/diagnostics` endpoint returns recent logs
6. Diagnostic info is displayed in Settings UI

## Tasks / Subtasks

- [x] Task 1: Create HomeKit Diagnostic Service (AC: 1, 2, 3, 4)
  - [x] 1.1 Create `HomeKitDiagnosticEntry` Pydantic schema with timestamp, level, category, message, details
  - [x] 1.2 Create `HomeKitDiagnosticsResponse` Pydantic schema with bridge status and recent logs
  - [x] 1.3 Implement `HomekitDiagnosticHandler` class extending logging.Handler to capture HomeKit logs
  - [x] 1.4 Implement circular buffer for log retention (max 100 entries, configurable)
  - [x] 1.5 Add `diagnostic_log_size` field to `HomekitConfig` dataclass

- [x] Task 2: Add Lifecycle and Event Logging to HomeKit Service (AC: 1, 2, 3, 4)
  - [x] 2.1 Add structured logging to `start()` method with network binding info
  - [x] 2.2 Add structured logging to `stop()` method
  - [x] 2.3 Add structured logging to `_run_driver()` for HAP driver lifecycle
  - [x] 2.4 Log pairing events by monitoring state file changes or HAP callbacks
  - [x] 2.5 Add logging to `trigger_motion()`, `trigger_occupancy()`, and other trigger methods
  - [x] 2.6 Log characteristic update delivery with camera_id and sensor type

- [x] Task 3: Create Diagnostics API Endpoint (AC: 5)
  - [x] 3.1 Add `GET /api/v1/homekit/diagnostics` endpoint to `homekit.py` router
  - [x] 3.2 Add method to `HomekitService` to retrieve diagnostic data
  - [x] 3.3 Return `HomeKitDiagnosticsResponse` with bridge status, logs, warnings, errors

- [x] Task 4: Build Diagnostics UI Panel (AC: 6)
  - [x] 4.1 Create `HomeKitDiagnostics.tsx` component for displaying diagnostic info
  - [x] 4.2 Add React Query hook `useHomekitDiagnostics` with 5-second polling
  - [x] 4.3 Display mDNS advertising status, connected clients count
  - [x] 4.4 Display recent diagnostic logs with category filtering
  - [x] 4.5 Display warnings and errors prominently
  - [x] 4.6 Integrate diagnostics panel into `HomekitSettings.tsx`

- [x] Task 5: Write Unit Tests (AC: 1-6)
  - [x] 5.1 Test `HomekitDiagnosticHandler` captures log entries correctly
  - [x] 5.2 Test circular buffer behavior (max entries, FIFO)
  - [x] 5.3 Test `/api/v1/homekit/diagnostics` endpoint returns valid response
  - [x] 5.4 Test diagnostic log filtering by category and level

## Dev Notes

### Architecture Constraints

- HAP-python runs in a background thread, separate from the main asyncio loop [Source: backend/app/services/homekit_service.py:478-483]
- Diagnostic logging must be thread-safe due to HAP driver running in separate thread
- Use Python's logging module with a custom handler to capture HomeKit-related logs
- Circular buffer prevents memory growth from retained logs [Source: docs/sprint-artifacts/tech-spec-epic-P7-1.md#NFRs]

### Existing Components to Modify

- `backend/app/services/homekit_service.py` - Add diagnostic methods and structured logging
- `backend/app/config/homekit.py` - Add `diagnostic_log_size` configuration
- `backend/app/api/v1/homekit.py` - Add diagnostics endpoint
- `frontend/components/settings/HomekitSettings.tsx` - Integrate diagnostics panel
- `frontend/hooks/useHomekitStatus.ts` - Add `useHomekitDiagnostics` hook

### New Files to Create

- `backend/app/schemas/homekit_diagnostics.py` - Pydantic schemas for diagnostic data
- `backend/app/services/homekit_diagnostics.py` - Diagnostic handler and buffer management
- `frontend/components/settings/HomeKitDiagnostics.tsx` - Diagnostics UI component

### Data Model Reference

From tech spec [Source: docs/sprint-artifacts/tech-spec-epic-P7-1.md#Data-Models]:

```python
class HomeKitDiagnosticEntry(BaseModel):
    timestamp: datetime
    level: str  # 'debug', 'info', 'warning', 'error'
    category: str  # 'lifecycle', 'pairing', 'event', 'network', 'mdns'
    message: str
    details: Optional[dict] = None

class HomeKitDiagnosticsResponse(BaseModel):
    bridge_running: bool
    mdns_advertising: bool
    network_binding: dict  # {ip: str, port: int, interface: Optional[str]}
    connected_clients: int
    last_event_delivery: Optional[dict]
    recent_logs: List[HomeKitDiagnosticEntry]
    warnings: List[str]
    errors: List[str]
```

### API Endpoint Reference

```
GET /api/v1/homekit/diagnostics

Response 200:
{
  "bridge_running": true,
  "mdns_advertising": true,
  "network_binding": {"ip": "192.168.1.100", "port": 51826},
  "connected_clients": 2,
  "last_event_delivery": {...},
  "recent_logs": [...],
  "warnings": [],
  "errors": []
}
```

### Testing Standards

- Backend: pytest with fixtures for HomeKit service mocking
- Frontend: Vitest + React Testing Library for component tests
- Follow existing patterns in `backend/tests/test_api/` and `frontend/__tests__/`

### Project Structure Notes

- Backend schemas go in `backend/app/schemas/` (new file)
- Services in `backend/app/services/` (new file + modify existing)
- Frontend components in `frontend/components/settings/`
- Hooks in `frontend/hooks/`

### Performance Requirements

- Diagnostic log retrieval: < 100ms response time
- Log buffer memory: < 1MB (100 entries max)
- Diagnostic polling: 5-second intervals when panel is open
- No performance impact on event processing when diagnostics disabled

### Security Considerations

- Diagnostic logs must NOT contain sensitive data (PIN codes, pairing keys)
- API endpoint requires same authentication as other HomeKit endpoints

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P7-1.md] - Epic technical specification
- [Source: backend/app/services/homekit_service.py] - Existing HomeKit service
- [Source: backend/app/api/v1/homekit.py] - Existing HomeKit API endpoints
- [Source: backend/app/config/homekit.py] - HomeKit configuration
- [Source: frontend/components/settings/HomekitSettings.tsx] - Existing HomeKit UI

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p7-1-1-add-homekit-diagnostic-logging.context.xml

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

- Implemented thread-safe diagnostic logging using Python's logging module with a custom handler
- Circular buffer uses collections.deque with maxlen for memory-efficient FIFO behavior
- Added 5-second polling in frontend diagnostics panel when HomeKit is enabled
- All 25 backend diagnostic tests pass
- Frontend build and lint pass

### File List

**New Files:**
- backend/app/schemas/homekit_diagnostics.py - Pydantic schemas for diagnostic data
- backend/app/services/homekit_diagnostics.py - Diagnostic handler and buffer management
- backend/tests/test_api/test_homekit_diagnostics.py - Unit tests (25 tests)
- frontend/components/settings/HomeKitDiagnostics.tsx - Diagnostics UI component

**Modified Files:**
- backend/app/services/homekit_service.py - Added diagnostic methods, structured logging with categories
- backend/app/config/homekit.py - Added diagnostic_log_size configuration
- backend/app/api/v1/homekit.py - Added GET /api/v1/homekit/diagnostics endpoint
- frontend/components/settings/HomekitSettings.tsx - Integrated diagnostics panel
- frontend/hooks/useHomekitStatus.ts - Added useHomekitDiagnostics hook and types
- frontend/lib/api-client.ts - Added getDiagnostics method to homekit client

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-17 | Initial draft | SM Agent |
| 2025-12-17 | Implementation complete | Dev Agent (Claude Opus 4.5) |
| 2025-12-17 | Code review APPROVED | Claude Opus 4.5 |

## Code Review

### Outcome: APPROVED

### AC Validation

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| 1 | HAP server lifecycle logging | PASS | `homekit_service.py:432-447` lifecycle category in start(), `homekit_service.py:468-478` in stop() |
| 2 | Pairing attempt logging | PASS | `homekit_service.py:1486-1490` logs pairing count, `homekit_service.py:1551-1555` logs pairing removal |
| 3 | Characteristic updates logging | PASS | `homekit_service.py:809,831,850,940` event category for trigger methods |
| 4 | Network binding logged | PASS | `homekit_service.py:447` network category with IP/port |
| 5 | /api/v1/homekit/diagnostics endpoint | PASS | `homekit.py:672-683` GET endpoint returning HomeKitDiagnosticsResponse |
| 6 | Settings UI diagnostics | PASS | `HomeKitDiagnostics.tsx` component integrated in `HomekitSettings.tsx:425` |

### Test Validation

- All 25 backend diagnostic tests pass
- Frontend build succeeds
- Frontend lint shows only pre-existing warnings (no new issues introduced)

### Code Quality Notes

- Thread-safe implementation using `threading.Lock` with `collections.deque(maxlen)`
- Proper separation of concerns: schemas, handler service, API endpoint
- Type-safe TypeScript with proper casting for enum-like string unions
- 5-second polling interval appropriate for diagnostics panel
- Memory-bounded with configurable max entries (default 100)
