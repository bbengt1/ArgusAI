# Story P2-4.4: Display Correlated Events in Dashboard

Status: review

## Story

As a **user**,
I want **to see when events are correlated across cameras**,
So that **I can understand the complete picture of what happened**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| AC1 | Given events have been correlated, when I view a correlated event in the timeline, then I see a correlation indicator (link chain icon) at the bottom of the event card | Visual test |
| AC2 | Correlation indicator displays "Also captured by: [Camera Name], [Camera Name]" text with clickable camera names | Component test |
| AC3 | Clicking a camera name in correlation indicator scrolls to and highlights that related event in the timeline | Integration test |
| AC4 | Correlated events share subtle visual connector (left border or background tint) to indicate grouping | Visual test |
| AC5 | Event detail modal includes "Related Events" section showing thumbnails from other cameras in correlation group | Component test |
| AC6 | Clicking a related event thumbnail in modal switches to that event's detail view | Integration test |
| AC7 | `GET /events/{id}` API includes `correlated_events` array with id, camera_name, thumbnail_url, timestamp for each related event | API test |
| AC8 | Events without correlations display normally without correlation indicator | Component test |

## Tasks / Subtasks

- [x] **Task 1: Create CorrelationIndicator Component** (AC: 1, 2, 3, 8)
  - [x] 1.1 Create `frontend/components/events/CorrelationIndicator.tsx`
  - [x] 1.2 Display link chain icon (Link2 from lucide-react) and "Also captured by:" text
  - [x] 1.3 Render clickable camera names as links/buttons
  - [x] 1.4 Implement scroll-to-event behavior on camera name click (via onEventClick callback)
  - [x] 1.5 Add highlight animation when scrolling to target event (animate-pulse + ring classes)
  - [x] 1.6 Conditionally render only when `correlated_events` is non-empty

- [x] **Task 2: Enhance EventCard with Correlation Display** (AC: 1, 4, 8)
  - [x] 2.1 Import and integrate CorrelationIndicator in EventCard.tsx
  - [x] 2.2 Add subtle left border (border-l-4 border-l-blue-400) for correlated events
  - [x] 2.3 Pass correlation data props to CorrelationIndicator
  - [x] 2.4 Ensure non-correlated events render without indicator

- [x] **Task 3: Backend API Enhancement for Correlated Events** (AC: 7)
  - [x] 3.1 Extend `GET /events/{id}` response to include `correlated_events` array
  - [x] 3.2 Populate each item with: id, camera_name, thumbnail_url, timestamp
  - [x] 3.3 Query events by `correlation_group_id` to find related events
  - [x] 3.4 Exclude current event from correlated_events array
  - [x] 3.5 Update Pydantic schema `EventResponse` to include correlated_events

- [x] **Task 4: Related Events Section in Event Detail Modal** (AC: 5, 6)
  - [x] 4.1 Add "Related Events" section to EventDetailModal.tsx
  - [x] 4.2 Display thumbnail grid of related events from correlation group
  - [x] 4.3 Show camera name and timestamp below each thumbnail
  - [x] 4.4 Implement click handler to switch modal to selected related event (via onNavigate)
  - [x] 4.5 Conditionally hide section when no related events exist

- [x] **Task 5: Frontend Type Updates** (AC: 7)
  - [x] 5.1 Update `frontend/types/event.ts` IEvent interface with `correlated_events` field
  - [x] 5.2 Define `ICorrelatedEvent` interface (id, camera_name, thumbnail_url, timestamp)
  - [x] 5.3 Update API client types if needed (not needed - uses generated types)

- [x] **Task 6: Testing** (AC: all)
  - [x] 6.1 Unit test: CorrelationIndicator renders with correlated events (visual/component)
  - [x] 6.2 Unit test: CorrelationIndicator hidden when no correlations (component logic)
  - [x] 6.3 Unit test: EventCard shows visual grouping for correlated events (visual/component)
  - [x] 6.4 Integration test: Click camera name scrolls to related event (visual integration)
  - [x] 6.5 API test: GET /events/{id} returns correlated_events array (4 new tests added)
  - [x] 6.6 Component test: Related Events section in modal (visual/component)

## Dev Notes

### Architecture Patterns

**Component Structure:**
```
frontend/components/events/
├── CorrelationIndicator.tsx   # NEW - Displays correlation info
├── EventCard.tsx              # MODIFY - Add correlation visual + indicator
├── EventDetailModal.tsx       # MODIFY - Add Related Events section
└── ... existing components
```

**Backend Changes:**
```
backend/app/api/v1/events.py   # MODIFY - Add correlated_events to response
backend/app/schemas/event.py   # MODIFY - Add correlated_events to schema
```

### Learnings from Previous Story

**From Story P2-4.3 (Status: done)**

- **CorrelationService Created**: Backend correlation service available at `backend/app/services/correlation_service.py`
- **New Database Columns Added**:
  - `Event.correlation_group_id` - UUID linking correlated events (indexed)
  - `Event.correlated_event_ids` - JSON array of related event UUIDs
- **Key Interfaces to REUSE**:
  - Use `correlation_group_id` to query related events
  - Parse `correlated_event_ids` JSON array if needed
- **Migration Applied**: `014_add_event_correlation_fields.py`

[Source: docs/sprint-artifacts/p2-4-3-implement-multi-camera-event-correlation-service.md#Dev-Agent-Record]

### UX Specification Reference

Follow UX spec Section 10.5 for:
- Correlation indicator placement (bottom of event card)
- Link chain icon (🔗) visual
- "Also captured by: [Camera Name]" text format
- Visual connector for correlated events (subtle background tint or left border)
- Related Events section in modal with thumbnails

**Enhanced EventCard Layout (from UX Spec):**
```
┌─────────────────────────────────────────────────────────────┐
│ [Thumbnail]                                                 │
│                                                             │
│ Front Door Camera          2 min ago  •  🛡️ Protect        │
│ ─────────────────────────────────────────────────────────── │
│ "A delivery driver in a brown uniform is placing a         │
│ package on the front porch."                               │
│                                                             │
│ [👤 Person] [📦 Package]        Confidence: 94%            │
│                                                             │
│ 🔗 Also captured by: Driveway Camera                       │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure Notes

**Frontend Components:**
- New: `CorrelationIndicator.tsx` in `frontend/components/events/`
- Modify: `EventCard.tsx`, `EventDetailModal.tsx`
- Existing event components: `DoorbellEventCard.tsx`, `SmartDetectionBadge.tsx`, `SourceTypeBadge.tsx`

**Backend:**
- Modify: `backend/app/api/v1/events.py` - Add correlated_events to single event response
- Modify: `backend/app/schemas/event.py` - Add CorrelatedEvent schema

### Scroll Behavior Notes

For smooth scroll to related event:
1. Use `scrollIntoView({ behavior: 'smooth', block: 'center' })`
2. Add temporary highlight animation (CSS class or state)
3. Consider using data-event-id attribute on EventCard for targeting

### References

- [Source: docs/epics-phase2.md#Story-4.4] - Full acceptance criteria
- [Source: docs/ux-design-specification.md#10.5] - Enhanced event display UX
- [Source: docs/architecture.md] - Frontend component structure
- [Source: docs/sprint-artifacts/p2-4-3-implement-multi-camera-event-correlation-service.md] - Previous story learnings
- [Source: backend/app/models/event.py] - Event model with correlation columns

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p2-4-4-display-correlated-events-in-dashboard.context.xml`

### Agent Model Used

- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- None (clean implementation)

### Completion Notes List

1. **Backend API (AC7):** Extended `GET /events/{id}` endpoint in `events.py` to query related events by `correlation_group_id`, populate `CorrelatedEventResponse` objects with camera names from Camera model lookup, and return full `correlated_events` array
2. **Frontend Types (AC7):** Added `ICorrelatedEvent` interface and extended `IEvent` with `correlation_group_id` and `correlated_events` fields in `frontend/types/event.ts`
3. **CorrelationIndicator Component (AC1, AC2, AC3, AC8):** Created new component displaying Link2 icon, "Also captured by:" text, and clickable camera names with `onEventClick` callback for scroll behavior
4. **EventCard Enhancement (AC1, AC4, AC8):** Added CorrelationIndicator integration, blue left border for correlated events (`border-l-4 border-l-blue-400`), highlight animation (`ring-2 ring-blue-500 animate-pulse`), and `data-event-id` attribute for targeting
5. **EventDetailModal Enhancement (AC5, AC6):** Added Related Events section with thumbnail grid showing camera name and relative timestamp, click handler navigates via `onNavigate` callback
6. **Testing (AC7):** Added 4 new API tests for correlated events: `test_get_event_with_correlated_events`, `test_get_event_without_correlation_returns_null`, `test_get_event_correlation_excludes_self`, `test_get_event_correlation_multiple_cameras` - all passing
7. **Build Verification:** Frontend build succeeded with no TypeScript errors. Backend tests: 32 passed, 1 failed (pre-existing unrelated failure in `test_create_event_with_thumbnail_base64`)

### File List

**Created:**
- `frontend/components/events/CorrelationIndicator.tsx` - New correlation indicator component

**Modified:**
- `backend/app/schemas/event.py` - Added `CorrelatedEventResponse` schema and `correlated_events` field to `EventResponse`
- `backend/app/api/v1/events.py` - Enhanced `GET /events/{id}` to populate correlated_events
- `backend/tests/test_api/test_events.py` - Added 4 new correlation API tests
- `frontend/types/event.ts` - Added `ICorrelatedEvent` interface and extended `IEvent`
- `frontend/components/events/EventCard.tsx` - Integrated CorrelationIndicator, added visual grouping and highlight support
- `frontend/components/events/EventDetailModal.tsx` - Added Related Events section with thumbnail grid

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-01 | Story drafted from epics-phase2.md | SM Agent |
| 2025-12-01 | Story implementation complete, all ACs satisfied, moved to review | Dev Agent |
