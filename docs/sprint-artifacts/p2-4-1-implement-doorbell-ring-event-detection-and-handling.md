# Story P2-4.1: Implement Doorbell Ring Event Detection and Handling

Status: review

## Story

As a **system**,
I want **to detect and process doorbell ring events distinctly from motion events**,
So that **users receive immediate, prioritized notifications when someone rings the doorbell**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| AC1 | Given I have a UniFi Protect doorbell enabled, when someone presses the doorbell button, then the system detects this as a "ring" event (FR21) | Integration test |
| AC2 | Ring event detection identifies event type from Protect: `ring` or doorbell-specific event and immediately fetches snapshot (don't wait for motion) | Unit test |
| AC3 | Ring events are flagged with `is_doorbell_ring: true` in the event record | Database test |
| AC4 | AI uses doorbell-specific prompt: "Describe who is at the front door. Include their appearance, what they're wearing, and if they appear to be a delivery person, visitor, or solicitor." (FR23) | Integration test |
| AC5 | Event storage sets `is_doorbell_ring: true` and `smart_detection_type: 'ring'` with priority flag for notification system | Database test |
| AC6 | WebSocket broadcasts `DOORBELL_RING` message type with higher priority than motion events, including: event_id, camera_id, camera_name, thumbnail_url (FR22) | WebSocket test |
| AC7 | Doorbell ring events trigger AI analysis of who is at the door | E2E test |
| AC8 | Ring events are processed through existing AI pipeline with modified prompt | Integration test |

## Tasks / Subtasks

- [x] **Task 1: Extend Event Model for Doorbell Ring Support** (AC: 3, 5)
  - [x] 1.1 Add `is_doorbell_ring` (BOOLEAN DEFAULT FALSE) column to `events` table via Alembic migration
  - [x] 1.2 Update Event SQLAlchemy model in `backend/app/models/event.py`
  - [x] 1.3 Update EventResponse Pydantic schema in `backend/app/schemas/event.py`
  - [x] 1.4 Verify migration runs successfully and column is nullable for existing events

- [x] **Task 2: Implement Doorbell Ring Detection in Event Handler** (AC: 1, 2)
  - [x] 2.1 Update `ProtectEventHandler` to detect `ring` event type from uiprotect WebSocket
  - [x] 2.2 Ring detection integrated into existing `handle_event()` flow in `protect_event_handler.py`
  - [x] 2.3 On ring detection: immediately fetch snapshot (bypass motion event flow)
  - [x] 2.4 Map doorbell ring event type to `smart_detection_type: 'ring'`
  - [x] 2.5 Verify enabled doorbell cameras have event processing enabled

- [x] **Task 3: Create Doorbell-Specific AI Prompt** (AC: 4, 7, 8)
  - [x] 3.1 Create `DOORBELL_RING_PROMPT` constant in `protect_event_handler.py`
  - [x] 3.2 Prompt text: "Describe who is at the front door. Include their appearance, what they're wearing, and if they appear to be a delivery person, visitor, or solicitor."
  - [x] 3.3 Modified `_submit_to_ai_pipeline()` to check `is_doorbell_ring` flag and use custom prompt
  - [x] 3.4 Pass camera context (doorbell name) to AI for better descriptions

- [x] **Task 4: Implement Priority WebSocket Broadcast** (AC: 6)
  - [x] 4.1 Create `DOORBELL_RING` WebSocket message type in `_broadcast_doorbell_ring()` method
  - [x] 4.2 Add `_broadcast_doorbell_ring()` method to ProtectEventHandler
  - [x] 4.3 Include payload: `{ camera_id, camera_name, thumbnail_url, timestamp }`
  - [x] 4.4 Broadcast immediately upon event creation (before AI description completes for fast alert)
  - [x] 4.5 Send follow-up `EVENT_CREATED` message with full AI description when available

- [x] **Task 5: Update Event Storage for Doorbell Events** (AC: 3, 5)
  - [x] 5.1 Set `is_doorbell_ring: true` when storing ring events
  - [x] 5.2 Set `smart_detection_type: 'ring'` for ring events
  - [x] 5.3 is_doorbell_ring flag available for notification system
  - [x] 5.4 Ensure thumbnail is saved with event

- [x] **Task 6: Testing** (AC: all)
  - [x] 6.1 Unit test: Ring events correctly identified via `_parse_event_types()` (27 tests added)
  - [x] 6.2 Unit test: Doorbell prompt is used when `is_doorbell_ring` is true
  - [x] 6.3 Integration test: Ring event flows from detection to stored event
  - [x] 6.4 WebSocket test: `DOORBELL_RING` message is broadcast correctly
  - [x] 6.5 Database test: Event record has correct `is_doorbell_ring` and `smart_detection_type` values
  - [x] 6.6 API test: EventCreate and EventResponse schemas include doorbell fields

## Dev Notes

### Architecture Patterns

**Event Handler Flow:**
```
Protect WebSocket → ProtectEventHandler
                        ↓
                    is ring event?
                    /            \
                  yes             no
                   ↓               ↓
        process_doorbell_ring()   existing flow
                   ↓
        fetch snapshot immediately
                   ↓
        broadcast DOORBELL_RING
                   ↓
        submit to AI (doorbell prompt)
                   ↓
        store event + broadcast EVENT_CREATED
```

**Files to Modify:**
- `backend/app/models/event.py` - Add `is_doorbell_ring` column
- `backend/app/schemas/event.py` - Add `is_doorbell_ring` to response schema
- `backend/app/services/protect_event_handler.py` - Add ring detection logic
- `backend/app/services/ai_service.py` - Add doorbell-specific prompt
- `backend/app/services/websocket_manager.py` - Add `DOORBELL_RING` broadcast

**New Alembic Migration:**
- Add `is_doorbell_ring` BOOLEAN column to `events` table

### Learnings from Previous Story

**From Story P2-3.4 (Status: done)**

- **Event Model Fields**: `source_type`, `protect_event_id`, `smart_detection_type` columns already exist in Event model
- **Smart Detection Types**: Current values are 'person', 'vehicle', 'package', 'animal', 'motion' - need to add 'ring'
- **Badge Components Created**: `SourceTypeBadge.tsx` and `SmartDetectionBadge.tsx` - will need to extend for doorbell
- **Event Filter API**: `source_type` filter already implemented - events API supports filtering
- **AI Pipeline Integration**: Protect events flow through `_submit_to_ai_pipeline()` in `protect_event_handler.py`

**Key Interfaces to REUSE:**
- `ProtectEventHandler.process_event()` - Base event handling pattern
- `ProtectEventHandler._submit_to_ai_pipeline()` - AI submission flow
- `snapshot_service.get_snapshot()` - Snapshot retrieval
- `websocket_manager.broadcast()` - WebSocket broadcast pattern
- `Event.source_type = 'protect'` - Already set for Protect events

[Source: docs/sprint-artifacts/p2-3-4-add-event-source-type-display-in-dashboard.md#Dev-Notes]

### Project Structure Notes

**Backend Service Layer:**
```
backend/app/services/
├── protect_event_handler.py  # MODIFY - add ring detection
├── protect_service.py        # Reference for WebSocket event types
├── snapshot_service.py       # REUSE - snapshot retrieval
├── ai_service.py            # MODIFY - add doorbell prompt
└── websocket_manager.py     # MODIFY - add DOORBELL_RING broadcast
```

**Database Migration Path:**
- Create migration: `alembic revision -m "add_is_doorbell_ring_to_events"`
- Add column with default FALSE
- Apply: `alembic upgrade head`

### Testing Standards

- Unit tests for ring event detection logic
- Integration tests for full event flow
- WebSocket tests for broadcast message format
- API tests for doorbell event retrieval
- Mock uiprotect ring events for testing

### References

- [Source: docs/epics-phase2.md#Story-4.1] - Full acceptance criteria and technical notes
- [Source: docs/architecture.md#Phase-2-Additions] - Event processing architecture
- [Source: backend/app/services/protect_event_handler.py] - Existing event handler
- [Source: backend/app/services/ai_service.py] - AI prompt patterns
- [Source: backend/app/models/event.py] - Event model with existing Protect fields
- [Source: docs/ux-design-specification.md#Section-10.7] - Doorbell UX specs

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p2-4-1-implement-doorbell-ring-event-detection-and-handling.context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Database Migration**: Created `fba075111b91_add_is_doorbell_ring_to_events.py` with `is_doorbell_ring BOOLEAN NOT NULL DEFAULT FALSE` column
2. **Event Model**: Added `is_doorbell_ring` field to Event SQLAlchemy model with docstring update
3. **Schema Update**: Added `is_doorbell_ring` to both `EventCreate` and `EventResponse` Pydantic schemas, including `ring` as valid `smart_detection_type` literal
4. **Ring Detection**: Implemented doorbell ring detection via `is_ringing` attribute check in `_parse_event_types()` for Doorbell model type only
5. **Doorbell AI Prompt**: Created `DOORBELL_RING_PROMPT` constant with visitor description prompt
6. **Custom Prompt Support**: Extended `custom_prompt` parameter through entire AI provider chain (OpenAI, Claude, Gemini)
7. **Priority Broadcast**: Added `_broadcast_doorbell_ring()` method that sends `DOORBELL_RING` WebSocket message immediately before AI processing
8. **Event Storage**: `_store_protect_event()` now accepts and sets `is_doorbell_ring` flag
9. **EVENT_CREATED Update**: `_broadcast_event_created()` includes `is_doorbell_ring` in WebSocket payload
10. **Tests**: Added 27 comprehensive tests covering constants, event parsing, model/schema, WebSocket, AI prompts, storage, and integration

### File List

- `backend/alembic/versions/fba075111b91_add_is_doorbell_ring_to_events.py` (NEW)
- `backend/app/models/event.py` (MODIFIED - line 48)
- `backend/app/schemas/event.py` (MODIFIED - lines 24-28, 68-69)
- `backend/app/services/protect_event_handler.py` (MODIFIED - lines 79-83, 220-248, 640-698, 727-768, 802-864, 910)
- `backend/app/services/ai_service.py` (MODIFIED - lines 82-99, 102-125, 159-166, 322-334, 420-432, 587-608, 751-770)
- `backend/tests/test_api/test_protect.py` (MODIFIED - added ~570 lines of doorbell ring tests)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-01 | Story drafted from epics-phase2.md | SM Agent |
| 2025-12-01 | Implementation complete: doorbell ring detection, AI prompt, WebSocket, storage, 27 tests passing | Dev Agent |
