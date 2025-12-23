# Story P9-4.6: Store Manual Adjustments for Future Matching

Status: done

## Story

As a system administrator,
I want manual entity adjustments to be recorded and queryable,
so that future AI/ML can learn from user corrections and improve entity matching accuracy.

## Acceptance Criteria

1. **AC-4.6.1:** Given any manual operation (unlink/assign/move/merge), when complete, then EntityAdjustment record is created
2. **AC-4.6.2:** Given adjustment record, when stored, then includes event_id, old_entity_id, new_entity_id, action
3. **AC-4.6.3:** Given adjustment record, when stored, then includes event description snapshot
4. **AC-4.6.4:** Given adjustments exist, when querying API, then can retrieve adjustment history
5. **AC-4.6.5:** Given adjustment data, when exported, then suitable for ML training input

## Tasks / Subtasks

- [x] Task 1: Verify existing adjustment record creation (AC: #1, #2, #3)
  - [x] 1.1: Review unlink_event method creates adjustment records correctly
  - [x] 1.2: Review assign_event method creates adjustment records correctly
  - [x] 1.3: Review merge_entities method creates adjustment records correctly
  - [x] 1.4: Add test coverage for adjustment record fields

- [x] Task 2: Create GET /api/v1/context/adjustments endpoint (AC: #4)
  - [x] 2.1: Add AdjustmentListResponse and AdjustmentResponse Pydantic models
  - [x] 2.2: Add get_adjustments method to EntityService
  - [x] 2.3: Add GET /api/v1/context/adjustments endpoint with pagination
  - [x] 2.4: Add filtering by action type, entity_id, date range

- [x] Task 3: Create GET /api/v1/context/adjustments/export endpoint (AC: #5)
  - [x] 3.1: Add export endpoint returning JSON Lines format
  - [x] 3.2: Include event description, entity types, and correction context
  - [x] 3.3: Add date range filtering for export

- [x] Task 4: Add useAdjustments hook for frontend (optional) (AC: #4)
  - [x] 4.1: Skipped - Frontend hook not required for initial backend implementation
  - [x] 4.2: Skipped - TypeScript types can be added when frontend integration needed

- [x] Task 5: Write tests (AC: all)
  - [x] 5.1: Test adjustment records contain all required fields
  - [x] 5.2: Test GET /adjustments endpoint pagination
  - [x] 5.3: Test GET /adjustments filtering by action type
  - [x] 5.4: Test export endpoint returns valid JSON Lines

## Dev Notes

### Learnings from Previous Story

**From Story P9-4.5 (Status: done)**

- **EntityAdjustment Model**: Already exists at `backend/app/models/entity_adjustment.py` with fields:
  - id, event_id, old_entity_id, new_entity_id, action, event_description, created_at
- **Adjustment Actions**: "unlink", "assign", "move_from", "move_to", "merge" already defined
- **Entity Service**: Methods `unlink_event()`, `assign_event()`, `merge_entities()` already create adjustment records
- **Transaction Patterns**: All entity modifications are atomic with proper transaction handling

[Source: docs/sprint-artifacts/p9-4-5-implement-entity-merge.md#Dev-Agent-Record]

**From Story P9-4.4 (Status: done)**

- **Dual Adjustment Pattern**: Move operations create TWO records (move_from and move_to)
- **Event Description Snapshot**: Always captured at time of adjustment for ML context

[Source: docs/sprint-artifacts/p9-4-4-implement-event-entity-assignment.md]

### Architecture Notes

**Existing EntityAdjustment Model:**
```python
class EntityAdjustment(Base):
    __tablename__ = "entity_adjustments"

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"))
    old_entity_id = Column(String, ForeignKey("recognized_entities.id"))
    new_entity_id = Column(String, ForeignKey("recognized_entities.id"))
    action = Column(String(20))  # unlink, assign, move_from, move_to, merge
    event_description = Column(Text)  # Snapshot for ML training
    created_at = Column(DateTime)
```

**API Design:**
```
GET /api/v1/context/adjustments
Parameters:
  - page: int (default 1)
  - limit: int (default 50, max 100)
  - action: str (optional filter: unlink, assign, move, merge)
  - entity_id: str (optional filter by old or new entity)
  - start_date: datetime (optional)
  - end_date: datetime (optional)

Response:
{
  "adjustments": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "old_entity_id": "uuid or null",
      "new_entity_id": "uuid or null",
      "action": "unlink",
      "event_description": "Person walking...",
      "created_at": "2025-12-22T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50
}
```

**Export Format (JSON Lines):**
```jsonl
{"event_id":"uuid","action":"unlink","old_entity_id":"uuid","new_entity_id":null,"event_description":"Person in red jacket...","created_at":"2025-12-22T10:30:00Z"}
{"event_id":"uuid","action":"assign","old_entity_id":null,"new_entity_id":"uuid","event_description":"White Toyota Camry...","created_at":"2025-12-22T10:35:00Z"}
```

### Project Structure Notes

**Backend Files:**
- Model: `backend/app/models/entity_adjustment.py` (EXISTS)
- Service: `backend/app/services/entity_service.py` (add get_adjustments method)
- API: `backend/app/api/v1/context.py` (add adjustments endpoints)

**Frontend Files (optional):**
- Hook: `frontend/hooks/useEntities.ts` (add useAdjustments if needed)

### This Story's Primary Purpose

This story validates and completes the adjustment tracking infrastructure established in P9-4.3, P9-4.4, and P9-4.5. The main new work is:
1. API endpoint to query adjustment history
2. Export endpoint for ML training data
3. Ensure all adjustment records have complete data

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-4.md#P9-4.6]
- [Source: docs/epics-phase9.md#Story P9-4.6]
- [Source: backend/app/models/entity_adjustment.py]
- [Source: backend/app/services/entity_service.py]
- [Source: backend/app/api/v1/context.py]

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-22 | Story drafted from epics-phase9.md and tech-spec-epic-P9-4.md | BMAD Workflow |
| 2025-12-22 | Implemented: verified adjustment records, added endpoints, wrote tests | Claude Opus 4.5 |
| 2025-12-23 | Senior Developer Review: APPROVED - all ACs verified, 23 tests pass | Brent (via Claude Opus 4.5) |

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p9-4-6-store-manual-adjustments-for-future-matching.context.xml

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Verified existing adjustment creation in unlink_event(), assign_event(), and merge_entities() methods
- Added AdjustmentResponse and AdjustmentListResponse Pydantic models to context.py
- Added get_adjustments() method to EntityService with pagination and filtering
- Added export_adjustments() method returning ML-friendly format with entity types
- Added GET /api/v1/context/adjustments endpoint with pagination and filtering
- Added GET /api/v1/context/adjustments/export endpoint returning JSON Lines
- Created 23 tests in test_context_adjustments.py and test_entity_service.py
- All tests pass

### File List

- backend/app/api/v1/context.py (modified - added adjustment endpoints and Pydantic models)
- backend/app/services/entity_service.py (modified - added get_adjustments and export_adjustments methods)
- backend/tests/test_api/test_context_adjustments.py (created - API endpoint tests)
- backend/tests/test_services/test_entity_service.py (modified - added service method tests)
- docs/sprint-artifacts/p9-4-6-store-manual-adjustments-for-future-matching.md (modified - story file)
- docs/sprint-artifacts/p9-4-6-store-manual-adjustments-for-future-matching.context.xml (created - context file)
- docs/sprint-artifacts/sprint-status.yaml (modified - status updates)

---

## Senior Developer Review (AI)

### Reviewer
Brent

### Date
2025-12-23

### Outcome
**APPROVE** - All acceptance criteria fully implemented with comprehensive test coverage. Implementation follows established FastAPI patterns and is well-documented.

### Summary

Story P9-4.6 successfully implements the adjustment history API for ML training. The implementation adds two new endpoints (`GET /api/v1/context/adjustments` and `GET /api/v1/context/adjustments/export`) and corresponding service methods that query existing EntityAdjustment records created by previous stories (P9-4.3, P9-4.4, P9-4.5). All 5 acceptance criteria are verified with evidence, and 23 new tests pass.

### Key Findings

No HIGH or MEDIUM severity issues found.

**LOW Severity:**
- Note: The Pydantic deprecation warnings in test output (using `class Config` instead of `ConfigDict`) are pre-existing in other schema files, not introduced by this story.

### Acceptance Criteria Coverage

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-4.6.1 | EntityAdjustment record created for unlink/assign/move/merge | IMPLEMENTED | `backend/app/services/entity_service.py:1339-1346` (unlink), `1530-1537` (assign), `1482-1509` (move), `1628-1635` (merge) |
| AC-4.6.2 | Adjustment includes event_id, old_entity_id, new_entity_id, action | IMPLEMENTED | `backend/app/models/entity_adjustment.py:48-70` - Model defines all fields; `entity_service.py` methods populate all fields |
| AC-4.6.3 | Adjustment includes event description snapshot | IMPLEMENTED | `entity_service.py:1320-1321` (unlink), `1487,1507,1535` (assign/move), `1625` (merge) - All methods capture `event.description` |
| AC-4.6.4 | API endpoint to retrieve adjustment history | IMPLEMENTED | `backend/app/api/v1/context.py:2564-2632` - GET /adjustments with pagination, filtering by action/entity_id/date_range |
| AC-4.6.5 | Export endpoint suitable for ML training | IMPLEMENTED | `backend/app/api/v1/context.py:2635-2682` - GET /adjustments/export returns JSON Lines with entity types |

**Summary: 5 of 5 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Verify existing adjustment record creation | [x] Complete | VERIFIED | `entity_service.py:1339-1346,1482-1509,1530-1537,1628-1635` - All methods create EntityAdjustment records |
| Task 1.1: Review unlink_event creates adjustment | [x] Complete | VERIFIED | `entity_service.py:1339-1346` |
| Task 1.2: Review assign_event creates adjustment | [x] Complete | VERIFIED | `entity_service.py:1530-1537` |
| Task 1.3: Review merge_entities creates adjustment | [x] Complete | VERIFIED | `entity_service.py:1628-1635` |
| Task 1.4: Add test coverage for adjustment fields | [x] Complete | VERIFIED | `test_entity_service.py:1326-1345` - test_merge_entities_creates_adjustment_records |
| Task 2: Create GET /adjustments endpoint | [x] Complete | VERIFIED | `context.py:2564-2632` |
| Task 2.1: Add Pydantic models | [x] Complete | VERIFIED | `context.py:1196-1220` - AdjustmentResponse, AdjustmentListResponse |
| Task 2.2: Add get_adjustments service method | [x] Complete | VERIFIED | `entity_service.py:1689-1776` |
| Task 2.3: Add GET endpoint with pagination | [x] Complete | VERIFIED | `context.py:2564-2632` with page/limit params |
| Task 2.4: Add filtering by action/entity_id/date range | [x] Complete | VERIFIED | `entity_service.py:1719-1744` handles all filters |
| Task 3: Create GET /adjustments/export endpoint | [x] Complete | VERIFIED | `context.py:2635-2682` |
| Task 3.1: Add export endpoint returning JSON Lines | [x] Complete | VERIFIED | `context.py:2673-2681` StreamingResponse with application/x-ndjson |
| Task 3.2: Include event description and entity types | [x] Complete | VERIFIED | `entity_service.py:1834-1846` includes old_entity_type, new_entity_type |
| Task 3.3: Add date range filtering for export | [x] Complete | VERIFIED | `entity_service.py:1803-1807` |
| Task 4: Add useAdjustments hook (optional) | [x] Complete (Skipped) | VERIFIED | Skipped as noted - frontend hook not required for backend implementation |
| Task 5: Write tests | [x] Complete | VERIFIED | 23 tests in `test_context_adjustments.py` and `test_entity_service.py` - all pass |

**Summary: 16 of 16 tasks verified, 0 questionable, 0 false completions**

### Test Coverage and Gaps

**Tests Present:**
- `test_context_adjustments.py`: 15 API endpoint tests covering pagination, filtering, validation, export format
- `test_entity_service.py`: 8 service method tests for get_adjustments and export_adjustments

**Coverage:**
- API endpoint pagination: Tested ✓
- Action type filtering: Tested ✓
- Entity ID filtering: Tested ✓
- Date range filtering: Tested ✓
- Invalid action validation: Tested ✓
- Export JSON Lines format: Tested ✓
- Entity types in export: Tested ✓

**No test gaps identified for this story's scope.**

### Architectural Alignment

- Follows established FastAPI patterns in `context.py`
- Uses standard Pydantic models for request/response validation
- Service layer properly separates business logic from API layer
- Uses SQLAlchemy ORM patterns consistent with existing codebase
- Export uses StreamingResponse for memory efficiency with large datasets
- Aligns with tech spec API design (docs/sprint-artifacts/tech-spec-epic-P9-4.md)

### Security Notes

- No security issues identified
- Endpoint does not expose sensitive data beyond what's already in EntityAdjustment records
- Input validation on action types prevents arbitrary query injection
- Date parameters use standard datetime parsing

### Best-Practices and References

- FastAPI Query parameters with validation: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
- JSON Lines format for ML data: https://jsonlines.org/
- SQLAlchemy 2.0 query patterns: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html

### Action Items

**Code Changes Required:**
- None required

**Advisory Notes:**
- Note: Consider adding OpenAPI documentation examples for the export format in a future enhancement
- Note: The service's `export_adjustments` method loads all matching adjustments into memory; for very large datasets, consider pagination or cursor-based streaming in future
