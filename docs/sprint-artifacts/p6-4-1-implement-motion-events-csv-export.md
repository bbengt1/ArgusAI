# Story P6-4.1: Implement Motion Events CSV Export

Status: done

## Story

As a home owner,
I want to export motion event data to CSV format,
so that I can analyze raw motion detection data in external tools for security review or trend analysis.

## Acceptance Criteria

1. GET `/api/v1/motion-events/export?format=csv` endpoint created
2. CSV columns include: timestamp, camera_id, camera_name, confidence, algorithm, x, y, width, height, zone_id
3. Date range filtering supported via `start_date` and `end_date` query parameters
4. Camera filtering supported via `camera_id` query parameter
5. Streaming response for large datasets (no memory issues with 100k+ events)
6. Response filename includes date range (e.g., `motion_events_2025-12-01_2025-12-17.csv`)

## Tasks / Subtasks

- [x] Task 1: Create CSV export endpoint in motion_events.py (AC: #1, #2, #5)
  - [x] Add `GET /motion-events/export` endpoint before `/{event_id}` routes to avoid path shadowing
  - [x] Accept `format` query param (validate: must be "csv")
  - [x] Implement streaming response generator using `StreamingResponse`
  - [x] Write CSV headers matching AC #2 columns
  - [x] Stream data in batches of 100 to avoid memory issues

- [x] Task 2: Implement filtering and filename generation (AC: #3, #4, #6)
  - [x] Add `start_date` and `end_date` query params (date type, optional)
  - [x] Add `camera_id` query param (string, optional)
  - [x] Convert dates to datetime for timestamp comparison
  - [x] Generate filename with date range (or "all" if no range specified)

- [x] Task 3: Handle camera name lookup for CSV (AC: #2)
  - [x] Join with Camera table to get camera.name
  - [x] Use camera_id as fallback if camera not found (deleted camera scenario)

- [x] Task 4: Parse bounding_box JSON for CSV columns (AC: #2)
  - [x] Parse `bounding_box` JSON field to extract x, y, width, height
  - [x] Handle null/missing bounding_box gracefully (empty strings in CSV)
  - [x] Handle zone_id (may be null - use empty string)

- [x] Task 5: Write backend tests (AC: #1-6)
  - [x] Test CSV export with no filters returns all events
  - [x] Test date range filtering
  - [x] Test camera_id filtering
  - [x] Test combined filters
  - [x] Test empty result set
  - [x] Test streaming response headers
  - [x] Test CSV format and columns

## Dev Notes

- Follow the existing pattern from `events.py` export endpoint (lines 542-723)
- Use `StreamingResponse` from FastAPI for memory-efficient exports
- Batch size of 100 matches existing events export pattern
- The `MotionEvent` model has `bounding_box` as JSON text field with format `{"x": int, "y": int, "width": int, "height": int}`
- Zone_id is not currently stored on MotionEvent model - check if it needs to be added or use empty
- Route placement is critical - must be before `/{event_id}` to avoid shadowing

### Project Structure Notes

- Modified: `backend/app/api/v1/motion_events.py` - Add export endpoint
- New test: `backend/tests/test_api/test_motion_events_export.py` - Export tests

### Learnings from Previous Story

**From Story p6-3-3-add-audio-settings-to-camera-configuration (Status: review)**

- **Test Patterns**: 15 frontend tests and 9 backend tests - follow comprehensive test coverage patterns
- **API Pattern**: Follow established endpoint patterns with proper query parameter validation
- **Migration**: No migration needed for this story (export only, no schema changes)

[Source: docs/sprint-artifacts/p6-3-3-add-audio-settings-to-camera-configuration.md#Dev-Agent-Record]

### References

- [Source: docs/epics-phase6.md#Story P6-4.1]
- [Source: docs/backlog.md#FF-017] - Export Motion Events to CSV
- [Source: backend/app/api/v1/events.py#export_events] - Existing export pattern (lines 542-723)
- [Source: backend/app/models/motion_event.py] - MotionEvent model definition
- [Source: backend/app/schemas/motion.py#MotionEventResponse] - Response schema

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p6-4-1-implement-motion-events-csv-export.context.xml

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

- Implemented CSV export endpoint following existing events.py export pattern
- Added streaming response with batch size 100 for memory efficiency
- Implemented date range filtering (start_date, end_date) and camera_id filtering
- Added Camera table join via outerjoin for camera name lookup with fallback to camera_id
- Parsed bounding_box JSON to extract x, y, width, height; gracefully handles null/invalid JSON
- zone_id column included as empty string (not stored on MotionEvent model)
- Created 22 comprehensive tests covering all acceptance criteria
- All tests pass (22/22)

### File List

- backend/app/api/v1/motion_events.py (modified) - Added export endpoint
- backend/tests/test_api/test_motion_events_export.py (new) - 22 test cases

## Change Log

- 2025-12-17: Story drafted (P6-4.1)
- 2025-12-17: Story implemented - CSV export endpoint with filtering, streaming, tests
- 2025-12-17: Senior Developer Review (AI) - APPROVED

---

## Senior Developer Review (AI)

### Reviewer
claude-opus-4-5-20251101

### Date
2025-12-17

### Outcome
**APPROVE** - All acceptance criteria verified with evidence. All tasks completed and verified. Clean implementation following established patterns.

### Summary
The motion events CSV export endpoint is well-implemented following the existing events.py export pattern. The code is clean, well-documented, and has comprehensive test coverage (22 tests). No security concerns or architectural violations found.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| 1 | GET `/api/v1/motion-events/export?format=csv` endpoint created | IMPLEMENTED | `backend/app/api/v1/motion_events.py:33-182` |
| 2 | CSV columns include required fields | IMPLEMENTED | `backend/app/api/v1/motion_events.py:119-122` - fieldnames array |
| 3 | Date range filtering via start_date/end_date | IMPLEMENTED | `backend/app/api/v1/motion_events.py:83-89` |
| 4 | Camera filtering via camera_id | IMPLEMENTED | `backend/app/api/v1/motion_events.py:92-93` |
| 5 | Streaming response for large datasets | IMPLEMENTED | `backend/app/api/v1/motion_events.py:113-167` - generator with batch size 100 |
| 6 | Response filename includes date range | IMPLEMENTED | `backend/app/api/v1/motion_events.py:98-106` |

**Summary: 6 of 6 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Create CSV export endpoint | [x] | VERIFIED | `motion_events.py:33-182` |
| Task 1.1: Route before /{event_id} | [x] | VERIFIED | `motion_events.py:32` comment + placement |
| Task 1.2: Format param validation | [x] | VERIFIED | `motion_events.py:35` pattern="^csv$" |
| Task 1.3: StreamingResponse | [x] | VERIFIED | `motion_events.py:169-175` |
| Task 1.4: CSV headers | [x] | VERIFIED | `motion_events.py:119-122` |
| Task 1.5: Batch size 100 | [x] | VERIFIED | `motion_events.py:115` |
| Task 2: Filtering and filename | [x] | VERIFIED | `motion_events.py:83-106` |
| Task 3: Camera name lookup | [x] | VERIFIED | `motion_events.py:78-80` outerjoin |
| Task 4: Bounding box parsing | [x] | VERIFIED | `motion_events.py:141-151` |
| Task 5: Backend tests | [x] | VERIFIED | `test_motion_events_export.py` - 22 tests |

**Summary: 10 of 10 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps
- 22 comprehensive tests covering all acceptance criteria
- Tests verify: endpoint responses, CSV format, filtering, filename generation, edge cases
- All tests pass (22/22)
- Good coverage of edge cases: empty results, invalid JSON, deleted cameras

### Architectural Alignment
- Follows existing events.py export pattern exactly
- Uses established patterns: StreamingResponse, batch processing, SQLAlchemy queries
- Route placement correctly handles path shadowing

### Security Notes
- No security concerns identified
- Input validation via FastAPI Query with pattern matching
- Error handling prevents information leakage

### Best-Practices and References
- FastAPI StreamingResponse: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- CSV module: https://docs.python.org/3/library/csv.html
- Pattern follows existing `events.py:542-723` export endpoint

### Action Items
None - implementation is complete and meets all requirements.
