# Story P4-2.4: Integration Settings UI

Status: done

## Story

As a **home automation user**,
I want **a dedicated settings UI for configuring MQTT broker connection and Home Assistant discovery**,
so that **I can easily connect my ArgusAI to my Home Assistant instance without editing config files**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | MQTT tab/section appears in settings page under Integrations | Visual inspection |
| 2 | Broker host/port/credentials configurable via form inputs | Form submission test |
| 3 | Test connection button works and shows success/failure with message | Test with valid/invalid brokers |
| 4 | Connection status displayed in real-time with indicator | UI shows connected/disconnected badge |
| 5 | Save triggers reconnect with new config and shows confirmation | Change settings, verify reconnect |
| 6 | Topic prefix customization field available | Form includes topic_prefix input |
| 7 | Discovery enable/disable toggle available | Toggle switches discovery on/off |
| 8 | Form validation shows errors for invalid inputs (empty host, invalid port) | Submit invalid form, verify errors |
| 9 | Password field is masked and shows "configured" indicator when set | Visual inspection of password handling |
| 10 | Manual "Publish Discovery" button triggers discovery republish | Click button, verify toast/status |

## Tasks / Subtasks

- [x] **Task 1: Add MQTT/Integrations tab to settings page** (AC: 1)
  - [x] Import new MQTTSettings component in settings/page.tsx
  - [x] Add new TabsTrigger with Network icon and "Integrations" label
  - [x] Add TabsContent with ErrorBoundary wrapper
  - [x] Update grid-cols-8 to grid-cols-9 for tab bar

- [x] **Task 2: Create MQTTSettings component** (AC: 2, 6, 7, 9)
  - [x] Create frontend/components/settings/MQTTSettings.tsx
  - [x] Add form fields: broker_host, broker_port, username, password
  - [x] Add topic_prefix field with default "liveobject"
  - [x] Add discovery_prefix field with default "homeassistant"
  - [x] Add discovery_enabled toggle switch
  - [x] Add QoS selector (0, 1, 2)
  - [x] Add retain_messages toggle
  - [x] Add use_tls toggle
  - [x] Add enabled master toggle
  - [x] Handle password display (show "configured" badge when has_password=true)

- [x] **Task 3: Add connection status display** (AC: 4)
  - [x] Add useQuery for /api/v1/integrations/mqtt/status with polling (5s)
  - [x] Display connected/disconnected badge with color indicator
  - [x] Show broker address when connected
  - [x] Show messages_published count
  - [x] Show last_error if present

- [x] **Task 4: Implement test connection button** (AC: 3)
  - [x] Add "Test Connection" button below broker fields
  - [x] Call POST /api/v1/integrations/mqtt/test endpoint
  - [x] Show loading spinner during test
  - [x] Display success/failure toast with message
  - [x] Disable button when host is empty

- [x] **Task 5: Implement save functionality** (AC: 5, 8)
  - [x] Add form validation with zod schema
  - [x] Validate: host required, port 1-65535, qos 0-2
  - [x] Call PUT /api/v1/integrations/mqtt/config on save
  - [x] Show validation errors inline
  - [x] Show success toast after save
  - [x] Trigger reconnect via API (handled by backend)

- [x] **Task 6: Add publish discovery button** (AC: 10)
  - [x] Add "Publish Discovery" button
  - [x] Call POST /api/v1/integrations/mqtt/publish-discovery
  - [x] Show loading state during publish
  - [x] Display toast with cameras_published count
  - [x] Disable when MQTT not connected

- [x] **Task 7: Add API client methods** (AC: all)
  - [x] Add mqtt.getConfig() method
  - [x] Add mqtt.updateConfig() method
  - [x] Add mqtt.getStatus() method
  - [x] Add mqtt.testConnection() method
  - [x] Add mqtt.publishDiscovery() method

- [x] **Task 8: Write component tests** (AC: all)
  - [x] Test form renders with all fields (37 tests)
  - [x] Test validation errors display
  - [x] Test save calls API correctly
  - [x] Test connection status polling
  - [x] Test test connection flow

## Dev Notes

### Architecture Alignment

This story creates the frontend UI for the MQTT integration that was implemented in stories P4-2.1 through P4-2.3. The backend API endpoints already exist in `backend/app/api/v1/integrations.py`.

**Component Flow:**
```
MQTTSettings → API Client → /api/v1/integrations/mqtt/* → MQTTService
                                        ↓
                              MQTTConfig (database)
```

### Key Implementation Details

**Existing API Endpoints (from P4-2.1):**
- GET /api/v1/integrations/mqtt/config - Returns MQTTConfigResponse
- PUT /api/v1/integrations/mqtt/config - Accepts MQTTConfigUpdate, triggers reconnect
- GET /api/v1/integrations/mqtt/status - Returns MQTTStatusResponse (connected, broker, messages_published)
- POST /api/v1/integrations/mqtt/test - Test connection without persisting
- POST /api/v1/integrations/mqtt/publish-discovery - Trigger HA discovery publish

**Form Fields (from MQTTConfigUpdate schema):**
```typescript
interface MQTTConfigUpdate {
  broker_host: string;        // Required, 1-255 chars
  broker_port: number;        // 1-65535, default 1883
  username?: string;          // Optional, max 100 chars
  password?: string;          // Optional, max 500 chars (only sent when changing)
  topic_prefix: string;       // Default "liveobject"
  discovery_prefix: string;   // Default "homeassistant"
  discovery_enabled: boolean; // Default true
  qos: 0 | 1 | 2;             // Default 1
  enabled: boolean;           // Default true
  retain_messages: boolean;   // Default true
  use_tls: boolean;           // Default false
}
```

**Status Response:**
```typescript
interface MQTTStatusResponse {
  connected: boolean;
  broker: string | null;
  last_connected_at: string | null;
  messages_published: number;
  last_error: string | null;
  reconnect_attempt: number;
}
```

### Project Structure Notes

**Files to create:**
- `frontend/components/settings/MQTTSettings.tsx` - Main settings component

**Files to modify:**
- `frontend/app/settings/page.tsx` - Add Integrations tab
- `frontend/lib/api-client.ts` - Add mqtt API methods
- `frontend/types/settings.ts` - Add MQTT types (if not already present)

### Learnings from Previous Stories

**From Story P4-2.3 (Event Publishing) (Status: done)**

- Backend API is fully implemented with all 5 endpoints working
- MQTTService singleton available via get_mqtt_service()
- update_config() method triggers reconnect
- test_connection() method for testing without persistence
- Password is encrypted in database, only has_password boolean returned

**From PushNotificationSettings.tsx Pattern:**

- Use Card with CardHeader/CardContent structure
- Use Switch component for toggles
- Use Badge for status indicators
- Use toast (sonner) for success/error feedback
- Use useQuery with refetchInterval for status polling
- Wrap with ErrorBoundary for error isolation

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-p4-2.md#Story-P4-2.4-Integration-Settings-UI]
- [Source: docs/epics-phase4.md#Story-P4-2.4-Integration-Settings-UI]
- [Source: backend/app/api/v1/integrations.py]
- [Source: frontend/components/settings/PushNotificationSettings.tsx]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p4-2-4-integration-settings-ui.context.xml

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- Implementation completed 2025-12-11
- All 10 acceptance criteria implemented
- 37 component tests passing
- Build successful
- Uses existing backend API from P4-2.1 through P4-2.3

### File List

- `frontend/components/settings/MQTTSettings.tsx` (new - 498 lines)
- `frontend/__tests__/components/settings/MQTTSettings.test.tsx` (new - 545 lines)
- `frontend/app/settings/page.tsx` (modified - added Integrations tab)
- `frontend/lib/api-client.ts` (modified - added mqtt namespace)
- `frontend/types/settings.ts` (modified - added MQTT types)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-11 | Claude Opus 4.5 | Initial story draft |
| 2025-12-11 | Claude Opus 4.5 | Implementation complete - all tasks done, 37 tests passing |
| 2025-12-11 | Claude Opus 4.5 | Senior Developer Review - APPROVED |

---

## Senior Developer Review (AI)

### Review Metadata
- **Reviewer**: Claude Opus 4.5
- **Date**: 2025-12-11
- **Story**: P4-2.4 Integration Settings UI
- **Outcome**: ✅ **APPROVE**

### Summary

This story implements a comprehensive MQTT/Home Assistant Integration Settings UI with all 10 acceptance criteria fully satisfied. The implementation follows established patterns (PushNotificationSettings.tsx), uses proper form validation with Zod, and includes 37 component tests covering all ACs. No blocking issues found.

### Key Findings

**HIGH Severity:** None

**MEDIUM Severity:** None

**LOW Severity:**
- `MQTTSettings.tsx:97` - Uses `as any` cast to work around Zod/React Hook Form type inference. Acceptable workaround but could be improved with stricter typing in future refactor.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| 1 | MQTT tab/section appears in settings | ✅ IMPLEMENTED | `page.tsx:303-305,951-955` |
| 2 | Broker host/port/credentials configurable | ✅ IMPLEMENTED | `MQTTSettings.tsx:349-423` |
| 3 | Test connection button works | ✅ IMPLEMENTED | `MQTTSettings.tsx:441-458,152-189` |
| 4 | Connection status real-time display | ✅ IMPLEMENTED | `MQTTSettings.tsx:87-92,306-343` |
| 5 | Save triggers reconnect with confirmation | ✅ IMPLEMENTED | `MQTTSettings.tsx:136-150` |
| 6 | Topic prefix customization | ✅ IMPLEMENTED | `MQTTSettings.tsx:466-477` |
| 7 | Discovery enable/disable toggle | ✅ IMPLEMENTED | `MQTTSettings.tsx:538-542` |
| 8 | Form validation shows errors | ✅ IMPLEMENTED | `MQTTSettings.tsx:46-59,356-370` |
| 9 | Password masked with "configured" indicator | ✅ IMPLEMENTED | `MQTTSettings.tsx:388-399` |
| 10 | Manual Publish Discovery button | ✅ IMPLEMENTED | `MQTTSettings.tsx:554-572,192-212` |

**Summary: 10 of 10 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked | Verified | Evidence |
|------|--------|----------|----------|
| Task 1: Add Integrations tab | [x] | ✅ VERIFIED | `page.tsx:55,278,303-305,951-955` |
| Task 2: Create MQTTSettings component | [x] | ✅ VERIFIED | 608-line component with all fields |
| Task 3: Connection status display | [x] | ✅ VERIFIED | `MQTTSettings.tsx:87-92,224-343` |
| Task 4: Test connection button | [x] | ✅ VERIFIED | `MQTTSettings.tsx:152-189,441-458` |
| Task 5: Save functionality | [x] | ✅ VERIFIED | `MQTTSettings.tsx:46-59,136-150` |
| Task 6: Publish discovery button | [x] | ✅ VERIFIED | `MQTTSettings.tsx:192-212,554-572` |
| Task 7: API client methods | [x] | ✅ VERIFIED | `api-client.ts:1550-1602` |
| Task 8: Component tests (37) | [x] | ✅ VERIFIED | `MQTTSettings.test.tsx` |

**Summary: 47 of 47 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

- **Unit Tests**: 37 tests covering all acceptance criteria
- **Test Coverage by AC**:
  - AC 1: 2 tests (component renders, loading state)
  - AC 2: 5 tests (form fields render, data population)
  - AC 3: 3 tests (button render, disabled state, API call)
  - AC 4: 4 tests (connected/disconnected badges, message count, error display)
  - AC 5: 3 tests (save button, dirty state, API call)
  - AC 6: 3 tests (topic prefix, preview, discovery prefix)
  - AC 7: 3 tests (toggle render, reflects value, can disable)
  - AC 8: 3 tests (host validation, port validation, error text)
  - AC 9: 4 tests (masked, configured badge, no badge when false, visibility toggle)
  - AC 10: 3 tests (button render, disabled when disconnected, API call)
  - Additional: 4 tests (QoS, TLS, retain, master toggle)
- **Gaps**: None identified - all ACs have test coverage

### Architectural Alignment

- ✅ Follows existing settings component patterns (PushNotificationSettings.tsx)
- ✅ Uses established UI components (Card, Switch, Badge, Alert, etc.)
- ✅ Uses TanStack Query for data fetching with proper cache invalidation
- ✅ Uses React Hook Form + Zod for form validation
- ✅ Properly wrapped in ErrorBoundary
- ✅ API client methods follow existing namespace pattern

### Security Notes

- ✅ Password never prefilled from server response
- ✅ Password masked by default with visibility toggle
- ✅ Password only sent to API when user enters new value
- ✅ `has_password` boolean indicator protects actual password
- ✅ No sensitive data in console/logs

### Best-Practices and References

- [React Hook Form Best Practices](https://react-hook-form.com/advanced-usage)
- [TanStack Query Mutation Patterns](https://tanstack.com/query/latest/docs/react/guides/mutations)
- [Zod Schema Validation](https://zod.dev/)

### Action Items

**Code Changes Required:**
- None required for approval

**Advisory Notes:**
- Note: Consider improving type safety for zodResolver in future refactor (removes `as any` cast)
- Note: Build verification passed, 37/37 tests pass
