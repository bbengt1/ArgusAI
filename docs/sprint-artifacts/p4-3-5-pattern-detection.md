# Story P4-3.5: Pattern Detection

Status: done

## Story

As a **home security system user**,
I want **the system to analyze time-based activity patterns for each camera, detecting typical hours, day-of-week regularity, and unusual timing**,
so that **the AI can provide context like "This is typical activity for this time" or "Unusual - this camera is normally quiet at this hour" in event descriptions**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | System calculates hourly activity distribution per camera (events per hour across all days) | Unit test with historical event data |
| 2 | System calculates daily activity distribution per camera (events per day-of-week) | Unit test with historical event data |
| 3 | System identifies peak activity hours for each camera (hours with above-average activity) | Unit test with pattern calculation |
| 4 | System calculates average events per day metric for each camera | Unit test with aggregate calculation |
| 5 | System identifies quiet hours (below-threshold activity) for each camera | Unit test with threshold calculation |
| 6 | Pattern data persisted in `camera_activity_patterns` table, updated periodically | Database schema test, update test |
| 7 | `PatternService.get_patterns(camera_id)` returns activity patterns for a camera | Unit test with mock data |
| 8 | `PatternService.is_typical_timing(camera_id, timestamp)` returns True/False with confidence | Unit test with typical/unusual times |
| 9 | Pattern recalculation scheduled to run periodically (configurable, default: hourly) | Settings test, scheduler test |
| 10 | API endpoint `GET /api/v1/context/patterns/{camera_id}` returns pattern data | API test returns proper JSON |
| 11 | Pattern data includes: hourly_distribution, daily_distribution, peak_hours, quiet_hours, average_events_per_day | API response schema test |
| 12 | Pattern context integrated with ContextEnhancedPromptService for AI descriptions | Integration test with context service |
| 13 | Performance: Pattern lookup completes in <50ms (uses cached/persisted data) | Performance benchmark test |
| 14 | Graceful handling of cameras with insufficient history (<7 days data) - returns null/defaults | Test with new camera |
| 15 | Pattern data considers configurable time window (default: 30 days rolling) | Settings test with different windows |

## Tasks / Subtasks

- [x] **Task 1: Create CameraActivityPattern database model** (AC: 6)
  - [x] Create `backend/app/models/camera_activity_pattern.py`
  - [x] Define fields: id, camera_id, hourly_distribution (JSON), daily_distribution (JSON), peak_hours (JSON array), quiet_hours (JSON array), average_events_per_day (FLOAT), calculation_window_days (INT), last_calculated_at, created_at, updated_at
  - [x] Add model to `backend/app/models/__init__.py`
  - [x] Create Alembic migration for camera_activity_patterns table
  - [x] Add unique constraint on camera_id (one pattern record per camera)

- [x] **Task 2: Implement PatternService core calculations** (AC: 1, 2, 3, 4, 5, 7)
  - [x] Create `backend/app/services/pattern_service.py`
  - [x] Implement `_calculate_hourly_distribution(db, camera_id, days_back)` - count events per hour (0-23)
  - [x] Implement `_calculate_daily_distribution(db, camera_id, days_back)` - count events per day-of-week (0-6)
  - [x] Implement `_calculate_peak_hours(hourly_distribution)` - hours with events > mean + 0.5*std_dev
  - [x] Implement `_calculate_quiet_hours(hourly_distribution)` - hours with events < 0.1 * max_hour
  - [x] Implement `_calculate_average_events_per_day(db, camera_id, days_back)` - total events / days
  - [x] Implement `get_patterns(db, camera_id)` - retrieve or calculate patterns

- [x] **Task 3: Implement timing analysis methods** (AC: 8)
  - [x] Implement `is_typical_timing(db, camera_id, timestamp)` method
  - [x] Return `TimingAnalysisResult` with: is_typical (bool), confidence (float), reason (str)
  - [x] Compare current hour to peak_hours and quiet_hours
  - [x] Compare current day-of-week to daily_distribution average
  - [x] Return neutral result if insufficient history

- [x] **Task 4: Implement pattern calculation scheduler** (AC: 9, 15)
  - [x] Implement `recalculate_patterns(db, camera_id)` method
  - [x] Add `pattern_calculation_interval_hours` setting (default: 1)
  - [x] Add `pattern_time_window_days` setting (default: 30)
  - [x] Implement `recalculate_all_patterns(db)` for batch updates
  - [x] Add background task to run recalculation on schedule
  - [x] Check last_calculated_at before recalculating (skip if recent)

- [x] **Task 5: Create pattern API endpoint** (AC: 10, 11)
  - [x] Add route to `backend/app/api/v1/context.py`
  - [x] `GET /api/v1/context/patterns/{camera_id}` - get camera patterns
  - [x] Define Pydantic schemas: PatternResponse, HourlyDistribution, DailyDistribution
  - [x] Return 404 if camera not found
  - [x] Return partial data with warning if insufficient history

- [x] **Task 6: Handle edge cases** (AC: 14)
  - [x] Detect cameras with <7 days of history
  - [x] Return `insufficient_data: true` flag in response
  - [x] Provide sensible defaults (neutral timing analysis)
  - [x] Log warning for cameras with no events

- [x] **Task 7: Integrate with ContextEnhancedPromptService** (AC: 12)
  - [x] Modify `context_prompt_service.py` to use PatternService
  - [x] Replace inline time pattern logic with PatternService.is_typical_timing()
  - [x] Include pattern context in AI prompt when available
  - [x] Format timing context: "Typical activity time" or "Unusual - normally quiet at this hour"

- [x] **Task 8: Optimize performance** (AC: 13)
  - [x] Ensure pattern data is read from persisted table (not calculated on-demand)
  - [x] Add timing instrumentation for pattern lookups
  - [x] Verify <50ms lookup time with populated patterns
  - [x] Consider memory caching for frequently accessed cameras

- [x] **Task 9: Write unit tests** (AC: 1, 2, 3, 4, 5, 7, 8)
  - [x] Test hourly distribution calculation with mock events
  - [x] Test daily distribution calculation with mock events
  - [x] Test peak hour identification
  - [x] Test quiet hour identification
  - [x] Test average events per day calculation
  - [x] Test is_typical_timing with various scenarios
  - [x] Test edge cases (empty data, single event, etc.)

- [x] **Task 10: Write integration tests** (AC: 6, 12)
  - [x] Test pattern persistence in database
  - [x] Test pattern recalculation updates existing record
  - [x] Test context service integration with pattern data
  - [x] Test full pipeline: event → pattern update → context in description

- [x] **Task 11: Write API tests** (AC: 10, 11, 14)
  - [x] Test GET /api/v1/context/patterns/{camera_id} endpoint
  - [x] Test response schema matches expected format
  - [x] Test 404 response for non-existent camera
  - [x] Test insufficient_data flag for new cameras

## Dev Notes

### Architecture Alignment

This story is the fifth component of the Temporal Context Engine (Epic P4-3). It provides time-based pattern analysis that complements the visitor-based context from previous stories. The pattern data is used by ContextEnhancedPromptService (P4-3.4) to enrich AI descriptions with timing context.

**Component Integration Flow:**
```
Historical Events (past 30 days)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ PatternService.recalculate_patterns(camera_id)              │
│                                                             │
│   1. Query events within time window (30 days default)      │
│   2. Calculate hourly_distribution (events per hour 0-23)   │
│   3. Calculate daily_distribution (events per day 0-6)      │
│   4. Identify peak_hours (above average activity)           │
│   5. Identify quiet_hours (minimal activity)                │
│   6. Calculate average_events_per_day                       │
│   7. Persist to camera_activity_patterns table              │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼ (scheduled hourly)
┌─────────────────────────────────────────────────────────────┐
│ CameraActivityPattern record (persisted)                    │
│   - hourly_distribution: {"0": 2, "1": 0, ..., "23": 5}     │
│   - daily_distribution: {"0": 15, "1": 23, ..., "6": 18}    │
│   - peak_hours: ["09", "14", "17"]                          │
│   - quiet_hours: ["02", "03", "04", "05"]                   │
│   - average_events_per_day: 8.5                             │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼ (at event processing time)
┌─────────────────────────────────────────────────────────────┐
│ ContextEnhancedPromptService._format_time_pattern_context() │
│                                                             │
│   1. Call PatternService.is_typical_timing(camera_id, time) │
│   2. Get is_typical, confidence, reason                     │
│   3. Format as prompt context:                              │
│      - "Timing: Typical activity time for this camera"      │
│      - "Timing: Unusual - this camera normally quiet now"   │
└─────────────────────────────────────────────────────────────┘
```

### Key Implementation Details

**CameraActivityPattern Model:**
```python
class CameraActivityPattern(Base):
    __tablename__ = "camera_activity_patterns"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(Text, ForeignKey("cameras.id", ondelete="CASCADE"), unique=True, nullable=False)
    hourly_distribution = Column(Text, nullable=False)  # JSON: {"0": count, "1": count, ...}
    daily_distribution = Column(Text, nullable=False)   # JSON: {"0": count, ..., "6": count}
    peak_hours = Column(Text, nullable=False)           # JSON array: ["09", "14", "17"]
    quiet_hours = Column(Text, nullable=False)          # JSON array: ["02", "03", "04"]
    average_events_per_day = Column(Float, nullable=False)
    calculation_window_days = Column(Integer, default=30)
    last_calculated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**PatternService Structure:**
```python
class PatternService:
    """Analyze and store activity patterns for cameras."""

    async def get_patterns(self, db: Session, camera_id: str) -> Optional[PatternResponse]:
        """Get activity patterns for a camera."""
        pattern = db.query(CameraActivityPattern).filter_by(camera_id=camera_id).first()
        if not pattern:
            return None
        return PatternResponse(
            camera_id=camera_id,
            hourly_distribution=json.loads(pattern.hourly_distribution),
            daily_distribution=json.loads(pattern.daily_distribution),
            peak_hours=json.loads(pattern.peak_hours),
            quiet_hours=json.loads(pattern.quiet_hours),
            average_events_per_day=pattern.average_events_per_day,
            last_calculated_at=pattern.last_calculated_at,
            insufficient_data=False,
        )

    async def is_typical_timing(
        self, db: Session, camera_id: str, timestamp: datetime
    ) -> TimingAnalysisResult:
        """Determine if the given timestamp represents typical activity timing."""
        pattern = await self.get_patterns(db, camera_id)
        if not pattern or pattern.insufficient_data:
            return TimingAnalysisResult(is_typical=None, confidence=0.0, reason="Insufficient history")

        hour = str(timestamp.hour).zfill(2)
        day_of_week = str(timestamp.weekday())

        # Check if current hour is in quiet hours
        if hour in pattern.quiet_hours:
            return TimingAnalysisResult(
                is_typical=False,
                confidence=0.8,
                reason=f"This camera is normally quiet at {timestamp.strftime('%H:%M')}"
            )

        # Check if current hour is in peak hours
        if hour in pattern.peak_hours:
            return TimingAnalysisResult(
                is_typical=True,
                confidence=0.9,
                reason=f"Typical activity time for this camera"
            )

        # Check daily pattern
        daily_avg = sum(pattern.daily_distribution.values()) / 7
        current_day_count = pattern.daily_distribution.get(day_of_week, 0)

        if current_day_count < daily_avg * 0.5:
            return TimingAnalysisResult(
                is_typical=False,
                confidence=0.6,
                reason=f"Less typical on {timestamp.strftime('%A')}s"
            )

        return TimingAnalysisResult(is_typical=True, confidence=0.5, reason="Normal activity period")

    async def recalculate_patterns(
        self, db: Session, camera_id: str, window_days: int = 30
    ) -> Optional[CameraActivityPattern]:
        """Recalculate and persist activity patterns for a camera."""
        # Query events within time window
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        events = db.query(Event).filter(
            Event.camera_id == camera_id,
            Event.created_at >= cutoff
        ).all()

        if len(events) < 10:  # Minimum threshold for meaningful patterns
            return None

        # Calculate distributions
        hourly = self._calculate_hourly_distribution(events)
        daily = self._calculate_daily_distribution(events)
        peak = self._calculate_peak_hours(hourly)
        quiet = self._calculate_quiet_hours(hourly)
        avg_per_day = len(events) / window_days

        # Upsert pattern record
        pattern = db.query(CameraActivityPattern).filter_by(camera_id=camera_id).first()
        if pattern:
            pattern.hourly_distribution = json.dumps(hourly)
            pattern.daily_distribution = json.dumps(daily)
            pattern.peak_hours = json.dumps(peak)
            pattern.quiet_hours = json.dumps(quiet)
            pattern.average_events_per_day = avg_per_day
            pattern.last_calculated_at = datetime.utcnow()
        else:
            pattern = CameraActivityPattern(
                camera_id=camera_id,
                hourly_distribution=json.dumps(hourly),
                daily_distribution=json.dumps(daily),
                peak_hours=json.dumps(peak),
                quiet_hours=json.dumps(quiet),
                average_events_per_day=avg_per_day,
                calculation_window_days=window_days,
                last_calculated_at=datetime.utcnow(),
            )
            db.add(pattern)

        db.commit()
        return pattern
```

**API Response Schema:**
```python
class PatternResponse(BaseModel):
    camera_id: str
    hourly_distribution: dict[str, int]  # {"0": 5, "1": 2, ..., "23": 8}
    daily_distribution: dict[str, int]   # {"0": 23, "1": 45, ..., "6": 18}
    peak_hours: list[str]                # ["09", "14", "17"]
    quiet_hours: list[str]               # ["02", "03", "04", "05"]
    average_events_per_day: float
    last_calculated_at: datetime
    insufficient_data: bool = False

class TimingAnalysisResult(BaseModel):
    is_typical: Optional[bool]  # None if insufficient data
    confidence: float           # 0.0 to 1.0
    reason: str                 # Human-readable explanation
```

### Project Structure Notes

**Files to create:**
- `backend/app/models/camera_activity_pattern.py` - Pattern data model
- `backend/app/services/pattern_service.py` - Pattern calculation and analysis
- `backend/tests/test_services/test_pattern_service.py` - Unit tests
- `backend/tests/test_integration/test_pattern_integration.py` - Integration tests
- `backend/tests/test_api/test_pattern_api.py` - API tests
- `backend/alembic/versions/XXXX_add_camera_activity_patterns.py` - Migration

**Files to modify:**
- `backend/app/api/v1/context.py` - Add patterns endpoint
- `backend/app/models/__init__.py` - Export new model
- `backend/app/services/context_prompt_service.py` - Use PatternService for timing context
- `backend/app/schemas/system.py` - Add pattern-related settings schemas

### Performance Considerations

- Pattern data is persisted, not calculated on every event (enables <50ms lookup)
- Hourly recalculation avoids expensive queries during event processing
- Index on events(camera_id, created_at) for efficient historical queries
- JSON fields avoid additional table joins while maintaining structure
- Consider adding caching layer for frequently accessed camera patterns

### Testing Strategy

Per testing-strategy.md, target coverage:
- Unit tests: Distribution calculations, peak/quiet identification, timing analysis
- Integration tests: Database persistence, context service integration
- API tests: Patterns endpoint, schema validation, error responses
- Performance tests: Pattern lookup <50ms, recalculation efficiency

### Learnings from Previous Story

**From Story P4-3.4 (Context-Enhanced AI Prompts) (Status: done)**

- **ContextEnhancedPromptService Available**: Use `get_context_prompt_service()` - MODIFY to use PatternService
- **Time Pattern Integration Point**: `_format_time_pattern_context()` method exists - REPLACE inline logic with PatternService
- **Service Pattern**: Services in `backend/app/services/` with dependency injection via factory functions
- **Settings Integration**: Context settings already in SettingsService - ADD pattern settings
- **File Created**: `backend/app/services/context_prompt_service.py` - MODIFY for pattern integration
- **Test Coverage**: 48 tests - target similar

**From Story P4-3.3 (Recurring Visitor Detection) (Status: done)**

- **EntityService Pattern**: Similar service structure with factory function
- **Database Model Pattern**: UUID primary key, JSON for complex fields, foreign keys with CASCADE
- **Migration Pattern**: Use Alembic for schema changes
- **API Pattern**: Context endpoints in `backend/app/api/v1/context.py` - ADD patterns endpoint here

**Reusable Services (DO NOT RECREATE):**
- `ContextEnhancedPromptService._format_time_pattern_context()` - REPLACE with PatternService call
- `EntityService` - Reference for similar service structure
- `SimilarityService` - Reference for similar service structure

**Current State to Understand:**
- context_prompt_service.py has `_format_time_pattern_context()` - currently queries events inline
- This story moves that logic to PatternService with persistence and caching
- ContextEnhancedPromptService should call `PatternService.is_typical_timing()` instead

[Source: docs/sprint-artifacts/p4-3-4-context-enhanced-ai-prompts.md#Dev-Notes]
[Source: docs/sprint-artifacts/p4-3-3-recurring-visitor-detection.md#Dev-Agent-Record]

### References

- [Source: docs/epics-phase4.md#Story-P4-3.5-Pattern-Detection]
- [Source: docs/PRD-phase4.md#FR3 - System detects time-based patterns (daily, weekly)]
- [Source: docs/architecture.md#GET-/api/v1/context/patterns/{camera_id} - API specification]
- [Source: docs/sprint-artifacts/p4-3-4-context-enhanced-ai-prompts.md - ContextEnhancedPromptService patterns]
- [Source: docs/sprint-artifacts/p4-3-3-recurring-visitor-detection.md - Service and model patterns]

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p4-3-5-pattern-detection.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-11 | Claude Opus 4.5 | Initial story draft from create-story workflow |
