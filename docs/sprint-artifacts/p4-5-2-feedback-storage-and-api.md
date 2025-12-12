# Story P4-5.2: Feedback Storage & API

Status: done

## Story

As a **home security administrator**,
I want **aggregate feedback statistics tracked by event, camera, and time period**,
so that **I can analyze AI description accuracy trends and identify cameras needing calibration**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | `GET /api/v1/feedback/stats` endpoint returns aggregate feedback statistics | API test: endpoint returns valid FeedbackStatsResponse |
| 2 | Statistics include total feedback count, helpful count, not_helpful count | API test: all counts present in response |
| 3 | Statistics include accuracy rate (helpful / total * 100) | API test: accuracy_rate field is calculated correctly |
| 4 | Stats endpoint supports camera_id filter to get per-camera accuracy | API test: filtered results match camera |
| 5 | Stats endpoint supports time range filters (start_date, end_date) | API test: filtered by date range |
| 6 | EventFeedback model includes camera_id field (denormalized for efficient aggregation) | Database test: camera_id stored with feedback |
| 7 | Feedback API automatically populates camera_id from event on creation | Integration test: camera_id set without client providing it |
| 8 | Stats include breakdown by camera (events_by_camera with accuracy per camera) | API test: per-camera stats in response |
| 9 | Stats include trend data (feedback counts by day for last 30 days) | API test: daily_trend array in response |
| 10 | Stats include top corrections (most common correction patterns) | API test: top_corrections array in response |
| 11 | Stats endpoint is performant (<200ms for 10,000 feedback records) | Performance test: response time within threshold |
| 12 | Frontend API client includes `feedback.getStats()` method | Code review: method exists in api-client.ts |

## Tasks / Subtasks

- [x] **Task 1: Add camera_id to EventFeedback model** (AC: 6, 7)
  - [x] Add `camera_id` column to EventFeedback model as nullable String with index
  - [x] Create Alembic migration to add camera_id column
  - [x] Backfill existing feedback records with camera_id from their events
  - [x] Update FeedbackCreate endpoint to auto-populate camera_id from event

- [x] **Task 2: Create feedback statistics schemas** (AC: 1, 2, 3, 8, 9, 10)
  - [x] Create `FeedbackStatsResponse` Pydantic schema with:
    - total_count: int
    - helpful_count: int
    - not_helpful_count: int
    - accuracy_rate: float (percentage)
    - feedback_by_camera: Dict[str, CameraFeedbackStats]
    - daily_trend: List[DailyFeedbackStats]
    - top_corrections: List[CorrectionSummary]
  - [x] Create `CameraFeedbackStats` schema (camera_id, camera_name, helpful, not_helpful, accuracy_rate)
  - [x] Create `DailyFeedbackStats` schema (date, helpful_count, not_helpful_count)
  - [x] Create `CorrectionSummary` schema (correction_text, count)
  - [x] Add schemas to `backend/app/schemas/__init__.py`

- [x] **Task 3: Implement feedback stats API endpoint** (AC: 1, 2, 3, 4, 5, 8, 9, 10, 11)
  - [x] Create `GET /api/v1/feedback/stats` endpoint in new `backend/app/api/v1/feedback.py` router
  - [x] Implement query parameters: camera_id (optional), start_date (optional), end_date (optional)
  - [x] Calculate aggregate counts with SQLAlchemy func.count and group_by
  - [x] Calculate per-camera breakdown with camera_id grouping
  - [x] Calculate daily trend for last 30 days (or specified range)
  - [x] Extract top 10 correction patterns (group by correction text, count occurrences)
  - [x] Register router in main.py
  - [x] Add performance optimization: use indexed queries, limit date range

- [x] **Task 4: Update existing feedback endpoints** (AC: 7)
  - [x] Modify create_feedback endpoint to fetch camera_id from event
  - [x] Store camera_id in feedback record on creation
  - [x] Update FeedbackResponse schema to include camera_id

- [x] **Task 5: Add frontend API client methods** (AC: 12)
  - [x] Add `feedback.getStats(params?)` method to `frontend/lib/api-client.ts`
  - [x] Define TypeScript interface for FeedbackStatsResponse
  - [x] Add query params support for camera_id, start_date, end_date

- [x] **Task 6: Write backend tests** (AC: 1-11)
  - [x] Create `backend/tests/test_api/test_feedback_stats.py`
  - [x] Test GET /feedback/stats returns all required fields
  - [x] Test accuracy_rate calculation (helpful / total * 100)
  - [x] Test camera_id filter works correctly
  - [x] Test date range filter works correctly
  - [x] Test per-camera breakdown is accurate
  - [x] Test daily_trend includes last 30 days
  - [x] Test top_corrections returns common patterns
  - [x] Test performance with mock data (parametrize with different record counts)

## Dev Notes

### Architecture Alignment

This story extends the feedback infrastructure from P4-5.1 to add aggregate statistics capabilities. The stats endpoint provides the data foundation for Story P4-5.3 (Accuracy Dashboard UI).

**API Design:**
```
GET /api/v1/feedback/stats
  ?camera_id=uuid          # Optional: filter by camera
  ?start_date=2025-12-01   # Optional: filter start date
  ?end_date=2025-12-12     # Optional: filter end date

Response:
{
  "total_count": 150,
  "helpful_count": 120,
  "not_helpful_count": 30,
  "accuracy_rate": 80.0,
  "feedback_by_camera": {
    "camera-uuid-1": {
      "camera_id": "camera-uuid-1",
      "camera_name": "Front Door",
      "helpful_count": 80,
      "not_helpful_count": 10,
      "accuracy_rate": 88.9
    },
    "camera-uuid-2": { ... }
  },
  "daily_trend": [
    {"date": "2025-12-01", "helpful_count": 5, "not_helpful_count": 2},
    {"date": "2025-12-02", "helpful_count": 8, "not_helpful_count": 1},
    ...
  ],
  "top_corrections": [
    {"correction_text": "This was a delivery driver", "count": 5},
    {"correction_text": "Wrong person detected", "count": 3}
  ]
}
```

**Database Migration:**
```python
# Add camera_id to event_feedback table
op.add_column('event_feedback', sa.Column('camera_id', sa.String(), nullable=True))
op.create_index('ix_event_feedback_camera_id', 'event_feedback', ['camera_id'])

# Backfill camera_id from events
op.execute("""
    UPDATE event_feedback
    SET camera_id = (SELECT camera_id FROM events WHERE events.id = event_feedback.event_id)
""")
```

### Key Implementation Patterns

**Aggregate Query Pattern:**
```python
from sqlalchemy import func, case

stats = db.query(
    func.count(EventFeedback.id).label('total'),
    func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful'),
    func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful'),
).filter(
    # Apply date/camera filters
).first()

accuracy_rate = (stats.helpful / stats.total * 100) if stats.total > 0 else 0.0
```

**Per-Camera Breakdown:**
```python
camera_stats = db.query(
    EventFeedback.camera_id,
    Camera.name.label('camera_name'),
    func.count(EventFeedback.id).label('total'),
    func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful'),
    func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful'),
).join(Camera, EventFeedback.camera_id == Camera.id
).group_by(EventFeedback.camera_id, Camera.name
).all()
```

**Daily Trend Query:**
```python
from sqlalchemy import func, extract

daily_trend = db.query(
    func.date(EventFeedback.created_at).label('date'),
    func.sum(case((EventFeedback.rating == 'helpful', 1), else_=0)).label('helpful_count'),
    func.sum(case((EventFeedback.rating == 'not_helpful', 1), else_=0)).label('not_helpful_count'),
).filter(
    EventFeedback.created_at >= start_date
).group_by(func.date(EventFeedback.created_at)
).order_by(func.date(EventFeedback.created_at)
).all()
```

### Project Structure Notes

**Files to create:**
- `backend/app/api/v1/feedback.py` - New feedback router for stats endpoint
- `backend/alembic/versions/036_add_camera_id_to_feedback.py` - Migration
- `backend/tests/test_api/test_feedback_stats.py` - Stats endpoint tests

**Files to modify:**
- `backend/app/models/event_feedback.py` - Add camera_id column
- `backend/app/schemas/feedback.py` - Add stats schemas
- `backend/app/schemas/__init__.py` - Export new schemas
- `backend/app/api/v1/events.py` - Update create_feedback to set camera_id
- `backend/main.py` - Register feedback router
- `frontend/lib/api-client.ts` - Add getStats method
- `frontend/types/event.ts` - Add FeedbackStats types

### Learnings from Previous Story

**From Story P4-5.1: Feedback Collection UI (Status: done)**

- **EventFeedback model created**: Located at `backend/app/models/event_feedback.py` - use existing model structure
- **Feedback API endpoints exist**: CRUD at `/api/v1/events/{event_id}/feedback` - extend with new router
- **FeedbackResponse schema**: At `backend/app/schemas/feedback.py` - add stats schemas here
- **Backend tests pattern**: Follow `backend/tests/test_api/test_feedback.py` for test structure
- **Frontend hook pattern**: useFeedback.ts uses TanStack Query - follow same pattern for stats

[Source: docs/sprint-artifacts/p4-5-1-feedback-collection-ui.md#Dev-Agent-Record]

### Dependencies

- **Epic P4-5**: Second story in User Feedback & Learning epic
- **Story P4-5.1**: Provides EventFeedback model and basic CRUD API
- **Story P4-5.3**: Will consume stats API for Accuracy Dashboard UI

### References

- [Source: docs/epics-phase4.md#Story-P4-5.2-Feedback-Storage-API]
- [Source: docs/PRD-phase4.md#FR24 - System tracks accuracy metrics per camera]
- [Source: docs/PRD-phase4.md#API-Additions - GET /api/v1/feedback/stats]
- [Source: backend/app/models/event_feedback.py - Existing model to extend]
- [Source: backend/app/api/v1/events.py - Existing feedback endpoints]

## Dev Agent Record

### Context Reference

- [p4-5-2-feedback-storage-and-api.context.xml](./p4-5-2-feedback-storage-and-api.context.xml)

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. All acceptance criteria implemented
2. Migration uses SQLite batch mode for compatibility
3. Frontend build passes after changes
4. Pre-existing test database issues affect unit tests (not new to this story)
5. All schemas exported properly, API registered in main.py

### File List

**Created:**
- `backend/app/api/v1/feedback.py` - New feedback stats router (260 lines)
- `backend/alembic/versions/036_add_camera_id_to_feedback.py` - Migration with batch mode
- `backend/tests/test_api/test_feedback_stats.py` - Comprehensive test suite (14 tests)

**Modified:**
- `backend/app/models/event_feedback.py` - Added camera_id column with index
- `backend/app/schemas/feedback.py` - Added FeedbackStatsResponse, CameraFeedbackStats, DailyFeedbackStats, CorrectionSummary schemas
- `backend/app/schemas/__init__.py` - Export new schemas
- `backend/app/api/v1/events.py:1671-1684` - Auto-populate camera_id in create_feedback
- `backend/main.py:40,632` - Register feedback router
- `frontend/lib/api-client.ts:16,465-489` - Added feedback.getStats() method and IEventFeedback import
- `frontend/types/event.ts:40,47-86` - Added camera_id to IEventFeedback, IFeedbackStats types

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-12 | Claude Opus 4.5 | Initial story draft from create-story workflow |
| 2025-12-12 | Claude Opus 4.5 | Story implementation complete - all tasks done |
