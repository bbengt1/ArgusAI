# Story P4-7.2: Anomaly Scoring

**Epic:** P4-7 Behavioral Anomaly Detection (Growth)
**Status:** done
**Created:** 2025-12-13
**Story Key:** p4-7-2-anomaly-scoring

---

## User Story

**As a** home security user
**I want** each event to be scored for how unusual it is compared to my camera's normal patterns
**So that** I can quickly identify potentially significant security events that deviate from routine activity

---

## Background & Context

Epic P4-7 introduces behavioral anomaly detection. Story P4-7.1 established the baseline activity learning with hourly/daily/object type distributions. This story builds on that foundation to score how anomalous each event is.

**Dependency:** P4-7.1 (Baseline Activity Learning) - DONE

**What P4-7.1 Provides:**
- `CameraActivityPattern` model with hourly_distribution, daily_distribution, object_type_distribution
- `PatternService` with `get_patterns()`, `recalculate_patterns()`, `update_baseline_incremental()`
- API endpoint `GET /api/v1/context/patterns/{camera_id}`

**What This Story Adds:**
1. **Anomaly scoring algorithm** - calculate deviation from expected patterns
2. **Anomaly score field on events** - persist score for historical analysis
3. **Scoring API** - calculate score for new/existing events
4. **New camera handling** - graceful degradation when no baseline exists

This data powers Story P4-7.3 (Anomaly Alerts) which creates notifications for high-scoring events.

---

## Acceptance Criteria

### AC1: Anomaly Score Field on Event Model
- [x] Add `anomaly_score` column (Float, nullable) to Event model
- [x] Score range: 0.0 (completely normal) to 1.0 (highly anomalous)
- [x] Create Alembic migration to add column
- [x] Nullable to handle events before scoring was implemented

### AC2: Anomaly Scoring Service
- [x] Create `AnomalyScoringService` class in `backend/app/services/`
- [x] Method `calculate_anomaly_score(camera_id, event, patterns)` -> float
- [x] Method `score_event(db, event)` - calculate and persist score
- [x] Return 0.0 (neutral) if insufficient baseline data

### AC3: Timing Anomaly Calculation
- [x] Compare event hour to hourly_distribution
- [x] Calculate z-score or percentile-based deviation
- [x] Higher score if event occurs during quiet hours
- [x] Lower score if event occurs during peak hours
- [x] Return component score: `timing_score` (0.0 to 1.0)

### AC4: Day-of-Week Anomaly Calculation
- [x] Compare event day-of-week to daily_distribution
- [x] Higher score if event occurs on low-activity days
- [x] Return component score: `day_score` (0.0 to 1.0)

### AC5: Object Type Anomaly Calculation
- [x] Compare detected objects to object_type_distribution
- [x] Higher score for rarely-seen object types
- [x] Higher score for first-time object types (not in baseline)
- [x] Return component score: `object_score` (0.0 to 1.0)

### AC6: Combined Anomaly Score
- [x] Combine component scores with configurable weights
- [x] Default weights: timing=0.4, day=0.2, object=0.4
- [x] Final score clamped to [0.0, 1.0]
- [x] Return detailed breakdown: `{total, timing_score, day_score, object_score}`

### AC7: Event Pipeline Integration
- [x] Calculate anomaly score after AI description in event_processor.py
- [x] Persist score to event record
- [x] Non-blocking (should not significantly slow event processing)
- [x] Skip scoring if no baseline exists (new camera)

### AC8: Severity Threshold Classification
- [x] Define thresholds: low (<0.3), medium (0.3-0.6), high (>0.6)
- [x] Add `anomaly_severity` field to scoring response
- [x] Classification used by P4-7.3 for alert triggering

### AC9: API Endpoint for Manual Scoring
- [x] GET `/api/v1/context/anomaly/score/{event_id}` - score existing event
- [x] POST `/api/v1/context/anomaly/score` - score event data without persisting
- [x] Response includes total score, component breakdown, severity classification

### AC10: Testing
- [x] Unit tests for timing anomaly calculation (3 tests)
- [x] Unit tests for day-of-week anomaly calculation (2 tests)
- [x] Unit tests for object type anomaly calculation (5 tests)
- [x] Unit tests for combined score calculation (2 tests)
- [x] Test new camera handling (no baseline - 2 tests)
- [x] API tests for endpoints (7 tests)

---

## Technical Implementation

### Task 1: Add anomaly_score Column to Event Model
**File:** `backend/app/models/event.py`
- Add `anomaly_score = Column(Float, nullable=True)`
- Document: 0.0 (normal) to 1.0 (highly anomalous)

### Task 2: Create Alembic Migration
**File:** `backend/alembic/versions/040_add_anomaly_score_to_events.py`
- Add anomaly_score column to events table

### Task 3: Create AnomalyScoringService
**File:** `backend/app/services/anomaly_scoring_service.py`
```python
@dataclass
class AnomalyScoreResult:
    total: float
    timing_score: float
    day_score: float
    object_score: float
    severity: str  # 'low', 'medium', 'high'
    has_baseline: bool

class AnomalyScoringService:
    TIMING_WEIGHT = 0.4
    DAY_WEIGHT = 0.2
    OBJECT_WEIGHT = 0.4

    LOW_THRESHOLD = 0.3
    HIGH_THRESHOLD = 0.6

    def calculate_anomaly_score(patterns, event) -> AnomalyScoreResult
    def _calculate_timing_score(hourly_dist, event_hour) -> float
    def _calculate_day_score(daily_dist, event_day) -> float
    def _calculate_object_score(object_dist, event_objects) -> float
    def _classify_severity(score) -> str
```

### Task 4: Implement Timing Anomaly Logic
**File:** `backend/app/services/anomaly_scoring_service.py`
- Get expected count for event's hour from hourly_distribution
- Calculate deviation from mean hourly count
- Normalize to 0-1 range (higher = more anomalous)
- Events in quiet hours score higher

### Task 5: Implement Object Type Anomaly Logic
**File:** `backend/app/services/anomaly_scoring_service.py`
- For each object in event.objects_detected:
  - If object not in baseline: score += 0.5 (novel object)
  - If object rare (< 5% of baseline): score += 0.3
  - If object common: score += 0.0
- Normalize to 0-1 range

### Task 6: Integrate with Event Pipeline
**File:** `backend/app/services/event_processor.py`
- After event saved and baseline updated:
  ```python
  # Calculate and persist anomaly score
  score_result = await anomaly_service.score_event(db, event)
  ```
- Wrap in try/except (scoring failure should not fail event processing)

### Task 7: Create API Endpoints
**File:** `backend/app/api/v1/anomaly.py` (new router)
- GET `/api/v1/anomaly/score/{event_id}`
- POST `/api/v1/anomaly/score` (body: {camera_id, timestamp, objects_detected})
- Response schema: AnomalyScoreResponse

### Task 8: Write Tests
**Files:**
- `backend/tests/test_services/test_anomaly_scoring_service.py` (new)
- `backend/tests/test_api/test_anomaly.py` (new)

---

## Dev Notes

### Scoring Algorithm Design

**Timing Score Calculation:**
```
hourly_mean = mean(hourly_distribution.values())
hourly_std = std(hourly_distribution.values())
event_count = hourly_distribution[event_hour]
z_score = (hourly_mean - event_count) / hourly_std  # Inverted: low count = high score
timing_score = min(1.0, max(0.0, z_score / 3))  # Normalize z-score to 0-1
```

**Object Type Score Calculation:**
```
total_objects = sum(object_type_distribution.values())
for obj in event.objects_detected:
    if obj not in object_type_distribution:
        object_score += 0.5  # Novel object is suspicious
    else:
        obj_pct = object_type_distribution[obj] / total_objects
        if obj_pct < 0.05:  # Rare object
            object_score += 0.3
object_score = min(1.0, object_score)  # Cap at 1.0
```

### Architecture Constraints
- Use PatternService.get_patterns() to retrieve baseline
- Keep scoring lightweight (<100ms)
- Design for future ML-based scoring replacement

[Source: docs/architecture.md#Phase-4-Additions]

### Relevant Existing Code
- **PatternService:** `backend/app/services/pattern_service.py` - provides baseline patterns
- **PatternData:** dataclass with hourly_distribution, daily_distribution, object_type_distribution
- **Event model:** `backend/app/models/event.py` - add anomaly_score field
- **Event processor:** `backend/app/services/event_processor.py` - call scoring after event saved

[Source: docs/epics-phase4.md#Epic-P4-7]

### Testing Standards
- Follow pytest patterns in `backend/tests/test_services/`
- Use mocks for PatternService
- Test edge cases: no baseline, empty distributions, first event

### Learnings from P4-7.1

**From Story p4-7-1-baseline-activity-learning (Status: done)**
- PatternService singleton pattern with `get_pattern_service()`
- JSON stored as Text column with `json.dumps()`/`json.loads()`
- Hourly distribution uses zero-padded string keys: `{"00": 5, "01": 2, ...}`
- Daily distribution uses day-of-week strings: `{"0": 45, ...}` (0=Monday)
- Non-blocking background tasks via `asyncio.create_task()`

---

## Dev Agent Record

### Context Reference

- [docs/sprint-artifacts/p4-7-2-anomaly-scoring.context.xml](p4-7-2-anomaly-scoring.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

**New Files:**
- `backend/app/services/anomaly_scoring_service.py` - AnomalyScoringService with z-score based anomaly detection
- `backend/alembic/versions/040_add_anomaly_score_to_events.py` - Migration for anomaly_score column
- `backend/tests/test_services/test_anomaly_scoring_service.py` - 21 unit tests
- `backend/tests/test_api/test_context_anomaly.py` - 7 API tests

**Modified Files:**
- `backend/app/models/event.py` - Added anomaly_score column (Float, nullable)
- `backend/app/services/event_processor.py` - Integration with non-blocking background scoring
- `backend/app/api/v1/context.py` - Added anomaly scoring API endpoints

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-13 | SM Agent | Initial story creation |
