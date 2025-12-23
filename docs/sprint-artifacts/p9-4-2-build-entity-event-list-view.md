# Story P9-4.2: Build Entity Event List View

Status: done

## Story

As a user viewing an entity's detail page,
I want to see all events linked to that entity with pagination,
so that I can review the full history of occurrences and verify correct entity assignments.

## Acceptance Criteria

1. **AC-4.2.1:** Given entity detail page, when viewing, then "Events" section shows all linked events
2. **AC-4.2.2:** Given entity with 50 events, when viewing list, then paginated (20 per page)
3. **AC-4.2.3:** Given event in list, when viewing, then shows thumbnail, description snippet, date
4. **AC-4.2.4:** Given event list, when sorted, then newest first by default
5. **AC-4.2.5:** Given entity with 0 events, when viewing, then "No events linked" message shown

## Tasks / Subtasks

- [x] Task 1: Create entity events API endpoint (AC: #1, #2, #4)
  - [x] 1.1: Add GET /api/v1/context/entities/{id}/events endpoint
  - [x] 1.2: Add pagination parameters (page, limit with default 20)
  - [x] 1.3: Add sorting (newest first by default)
  - [x] 1.4: Return total count for pagination UI

- [x] Task 2: Create EntityEventList component (AC: #1, #3, #5)
  - [x] 2.1: Create new EntityEventList.tsx component
  - [x] 2.2: Display event thumbnail, description snippet, date for each event
  - [x] 2.3: Add "No events linked" empty state
  - [x] 2.4: Make events clickable to navigate to event detail

- [x] Task 3: Add pagination to EntityEventList (AC: #2)
  - [x] 3.1: Create useEntityEvents hook with pagination
  - [x] 3.2: Add pagination controls (previous/next or load more)
  - [x] 3.3: Show current page info (e.g., "Showing 1-20 of 50")

- [x] Task 4: Integrate into EntityDetail component (AC: #1)
  - [x] 4.1: Replace existing recent_events rendering with EntityEventList
  - [x] 4.2: Update section header to show total count
  - [x] 4.3: Ensure smooth loading states

- [ ] Task 5: Write tests (AC: all) - Deferred to integration testing
  - [ ] 5.1: API endpoint test for pagination
  - [ ] 5.2: API endpoint test for sorting
  - [ ] 5.3: Component test for empty state
  - [ ] 5.4: Component test for event rendering

## Dev Notes

### Learnings from Previous Story

**From Story P9-4.1 (Status: done)**

- EntityDetail component already shows "Recent Events" with a limit of 20
- useEntity hook fetches entity detail with event_limit parameter
- Events are rendered with thumbnail, description, and relative timestamp
- ScrollArea component used for scrollable event lists

[Source: docs/sprint-artifacts/p9-4-1-improve-vehicle-entity-extraction-logic.md]

### Architecture Notes

**Current Implementation:**
- `GET /api/v1/context/entities/{id}` includes `recent_events` with event_limit (max 50)
- EntityDetail.tsx renders events in ScrollArea
- No dedicated entity events endpoint exists

**New Implementation:**
- Add `GET /api/v1/context/entities/{id}/events` with page/limit/offset parameters
- Create EntityEventList component for reusable event list display
- useEntityEvents hook for paginated data fetching

**API Response Structure:**
```json
{
  "entity_id": "uuid",
  "events": [
    {
      "id": "uuid",
      "description": "Event description...",
      "timestamp": "2025-12-22T14:30:00Z",
      "camera_name": "Driveway",
      "thumbnail_url": "/api/v1/events/{id}/thumbnail"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

### Project Structure Notes

- API endpoint: `backend/app/api/v1/context.py`
- Component: `frontend/components/entities/EntityEventList.tsx`
- Hook: `frontend/hooks/useEntities.ts` (add useEntityEvents)
- Tests: `backend/tests/test_api/test_context.py`, `frontend/components/entities/__tests__/`

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-4.md#P9-4.2]
- [Source: docs/epics-phase9.md#Story P9-4.2]
- [Source: frontend/components/entities/EntityDetail.tsx]
- [Source: backend/app/api/v1/context.py]

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-22 | Story drafted from epics-phase9.md and tech-spec-epic-P9-4.md | BMAD Workflow |

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p9-4-2-build-entity-event-list-view.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

