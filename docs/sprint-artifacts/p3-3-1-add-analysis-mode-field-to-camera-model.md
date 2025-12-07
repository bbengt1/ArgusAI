# Story P3-3.1: Add Analysis Mode Field to Camera Model

Status: done

## Story

As a **system administrator**,
I want **each camera to store an analysis mode preference**,
So that **cameras can be configured independently for different quality/cost trade-offs in AI analysis**.

## Acceptance Criteria

1. **AC1:** Given the Camera database model, when schema is updated, then `analysis_mode` field exists with type VARCHAR(20), valid values: 'single_frame', 'multi_frame', 'video_native', and default value is 'single_frame' for existing cameras

2. **AC2:** Given a new camera is created, when no analysis_mode is specified, then defaults to 'single_frame'

3. **AC3:** Given a Protect camera is discovered via auto-discovery, when auto-added to system, then defaults to 'multi_frame' (balanced choice per UX principles)

4. **AC4:** Given camera.analysis_mode is 'video_native', when camera is non-Protect (RTSP/USB), then system treats as 'single_frame' (no clip source available)

## Tasks / Subtasks

- [x] **Task 1: Add analysis_mode column to Camera model** (AC: 1)
  - [x] 1.1 Add `analysis_mode` column to Camera model (String(20), nullable=False, default='single_frame')
  - [x] 1.2 Add CheckConstraint for valid values: 'single_frame', 'multi_frame', 'video_native'
  - [x] 1.3 Add index on analysis_mode column for query performance
  - [x] 1.4 Update Camera model docstring to document the new field

- [x] **Task 2: Create Alembic migration** (AC: 1, 2)
  - [x] 2.1 Generate migration: `alembic revision -m "add_analysis_mode_to_camera"`
  - [x] 2.2 Add analysis_mode column with default 'single_frame' for existing records
  - [x] 2.3 Add CHECK constraint for valid enum values
  - [x] 2.4 Apply migration and verify schema update
  - [x] 2.5 Test rollback works correctly

- [x] **Task 3: Update Pydantic schemas** (AC: 2)
  - [x] 3.1 Add `analysis_mode` to CameraBase with Literal type and default 'single_frame'
  - [x] 3.2 Add `analysis_mode` to CameraUpdate (optional field)
  - [x] 3.3 Add `analysis_mode` to CameraResponse
  - [x] 3.4 Add field description explaining valid values and trade-offs

- [x] **Task 4: Update Protect camera discovery default** (AC: 3)
  - [x] 4.1 Locate camera creation in protect_service.py or protect_event_handler.py
  - [x] 4.2 When auto-creating Protect cameras, set analysis_mode='multi_frame'
  - [x] 4.3 Add comment explaining UX rationale for balanced default

- [x] **Task 5: Implement video_native fallback for non-Protect cameras** (AC: 4)
  - [x] 5.1 In ProtectEventHandler multi-frame logic, check source_type
  - [x] 5.2 If analysis_mode='video_native' and source_type != 'protect', treat as 'single_frame'
  - [x] 5.3 Log info message explaining fallback reason
  - [x] 5.4 Consider adding validation warning in API when setting video_native on non-Protect camera

- [x] **Task 6: Write unit tests** (AC: All)
  - [x] 6.1 Test Camera model has analysis_mode field with correct defaults
  - [x] 6.2 Test analysis_mode constraint rejects invalid values
  - [x] 6.3 Test CameraCreate schema defaults to 'single_frame'
  - [x] 6.4 Test CameraUpdate schema accepts valid analysis_mode values
  - [x] 6.5 Test CameraResponse includes analysis_mode field
  - [x] 6.6 Test Protect camera discovery sets 'multi_frame' default
  - [x] 6.7 Test video_native fallback for RTSP/USB cameras

- [x] **Task 7: Integration test with existing multi-frame pipeline** (AC: 4)
  - [x] 7.1 Test camera with analysis_mode='multi_frame' triggers frame extraction
  - [x] 7.2 Test camera with analysis_mode='single_frame' uses thumbnail only
  - [x] 7.3 Verify existing P3-2.6 getattr() logic works with actual field

## Dev Notes

### Architecture References

- **Camera Model**: `backend/app/models/camera.py` - Add analysis_mode column alongside existing Phase 2 fields
- **Camera Schema**: `backend/app/schemas/camera.py` - Update Pydantic schemas for API
- **Protect Service**: `backend/app/services/protect_service.py` - Camera discovery and creation
- **Protect Event Handler**: `backend/app/services/protect_event_handler.py` - Multi-frame logic integration point
- [Source: docs/architecture.md#Database-Schema]
- [Source: docs/epics-phase3.md#Story-P3-3.1]

### Project Structure Notes

- Modify existing model: `backend/app/models/camera.py`
- Modify existing schema: `backend/app/schemas/camera.py`
- Add Alembic migration: `backend/alembic/versions/xxx_add_analysis_mode_to_camera.py`
- Modify: `backend/app/services/protect_service.py` (camera discovery)
- Modify: `backend/app/services/protect_event_handler.py` (fallback logic)
- Add tests: `backend/tests/test_models/test_camera.py`

### Implementation Guidance

1. **Camera Model Changes:**
   ```python
   # Add to Camera model alongside existing Phase 2 fields
   analysis_mode = Column(
       String(20),
       default='single_frame',
       nullable=False,
       index=True  # Optimizes filtering by analysis mode
   )

   # Add to __table_args__
   CheckConstraint(
       "analysis_mode IN ('single_frame', 'multi_frame', 'video_native')",
       name='check_analysis_mode'
   )
   ```

2. **Schema Updates:**
   ```python
   # In CameraBase
   analysis_mode: Literal['single_frame', 'multi_frame', 'video_native'] = Field(
       default='single_frame',
       description="AI analysis mode: single_frame (fast, low cost), multi_frame (balanced), video_native (best quality, highest cost)"
   )
   ```

3. **Protect Camera Discovery:**
   ```python
   # In protect_service.py during camera discovery
   camera = Camera(
       name=protect_camera.name,
       source_type='protect',
       analysis_mode='multi_frame',  # Balanced default for Protect cameras
       # ... other fields
   )
   ```

4. **Video Native Fallback:**
   ```python
   # In protect_event_handler.py
   camera_mode = getattr(camera, 'analysis_mode', 'single_frame')

   # Treat video_native as single_frame for non-Protect sources
   if camera_mode == 'video_native' and camera.source_type != 'protect':
       logger.info(f"Camera {camera.id} is non-Protect, falling back from video_native to single_frame")
       camera_mode = 'single_frame'
   ```

### Learnings from Previous Story

**From Story p3-2-6-integrate-multi-frame-analysis-into-event-pipeline (Status: done)**

- **Analysis Mode Check Already Exists**: `getattr(camera, 'analysis_mode', None)` is used in protect_event_handler.py - this story adds the actual field
- **Integration Point Identified**: Multi-frame logic is in `ProtectEventHandler._submit_to_ai_pipeline()`, not EventProcessor
- **SLA Differentiation**: Multi-frame uses 10s timeout vs 5s for single-frame
- **Files Modified in P3-2.6**:
  - `backend/app/models/event.py` - Added analysis_mode, frame_count_used columns
  - `backend/app/services/protect_event_handler.py` - Multi-frame integration with fallback
- **Test Patterns**: TestEventAnalysisModeFields, TestMultiFrameIntegration classes

**Key Dependencies:**
- P3-2.6: Multi-frame pipeline ready, just needs camera.analysis_mode to be a real field

[Source: docs/sprint-artifacts/p3-2-6-integrate-multi-frame-analysis-into-event-pipeline.md#Dev-Agent-Record]

### Testing Standards

- Add tests to `backend/tests/test_models/test_camera.py`
- Test migration up and down
- Test constraint validation rejects 'invalid_mode'
- Test API returns analysis_mode in camera responses
- Verify existing multi-frame tests still pass

### References

- [Source: docs/architecture.md#Database-Schema]
- [Source: docs/epics-phase3.md#Story-P3-3.1]
- [Source: docs/sprint-artifacts/p3-2-6-integrate-multi-frame-analysis-into-event-pipeline.md]
- [Source: backend/app/models/camera.py]
- [Source: backend/app/schemas/camera.py]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p3-3-1-add-analysis-mode-field-to-camera-model.context.xml

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 28 tests passed: 8 model tests, 9 API tests, 11 multi-frame integration tests

### Completion Notes List

1. Added `analysis_mode` column to Camera model with CheckConstraint and index
2. Created Alembic migration 017 with rollback support
3. Updated CameraBase, CameraUpdate schemas with Literal type validation
4. Protect cameras now default to 'multi_frame' when enabled via API
5. Added video_native fallback logic in ProtectEventHandler for non-Protect cameras
6. Added validation warning in cameras.py when setting video_native on non-Protect camera
7. Also fixed API endpoint to pass analysis_mode from request to Camera model

### File List

**Modified:**
- `backend/app/models/camera.py` - Added analysis_mode column, CheckConstraint, docstring
- `backend/app/schemas/camera.py` - Added analysis_mode to CameraBase, CameraUpdate
- `backend/app/api/v1/cameras.py` - Added analysis_mode to create_camera, validation warning
- `backend/app/api/v1/protect.py` - Set analysis_mode='multi_frame' for new Protect cameras
- `backend/app/services/protect_event_handler.py` - Added video_native fallback logic
- `backend/tests/test_models/test_camera.py` - Added TestCameraAnalysisModeField class (8 tests)
- `backend/tests/test_api/test_cameras.py` - Added TestCameraAnalysisModeAPI class (9 tests)

**Created:**
- `backend/alembic/versions/017_add_analysis_mode_to_cameras.py` - Migration for analysis_mode column

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-06 | 1.0 | Story drafted from epics-phase3.md |
| 2025-12-06 | 2.0 | Story implemented and tests passing |
