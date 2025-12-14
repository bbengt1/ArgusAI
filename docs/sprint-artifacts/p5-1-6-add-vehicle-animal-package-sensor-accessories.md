# Story P5-1.6: Add Vehicle/Animal/Package Sensor Accessories

**Epic:** P5-1 Native HomeKit Integration
**Status:** done
**Created:** 2025-12-14
**Story Key:** p5-1-6-add-vehicle-animal-package-sensor-accessories

---

## User Story

**As a** HomeKit user with Apple Home app,
**I want** separate sensor accessories for vehicle, animal, and package detections,
**So that** I can create distinct HomeKit automations for each detection type (e.g., "turn on garage lights when vehicle detected" vs "play sound when animal in yard").

---

## Background & Context

This story extends the HomeKit sensor infrastructure to provide detection-type-specific sensors beyond the existing motion and occupancy sensors. Currently, the motion sensor triggers on ALL detection events, which prevents users from creating type-specific automations.

**What exists (from P5-1.4/P5-1.5):**
- `CameraMotionSensor` class - triggers on any motion/detection event
- `CameraOccupancySensor` class - triggers only on person detection
- `trigger_motion()` and `trigger_occupancy()` methods in homekit_service.py
- Event processor integration for HomeKit triggers
- Auto-reset timer infrastructure (30s for motion, 5min for occupancy)

**What this story adds:**
1. `CameraVehicleSensor` class - MotionSensor service, only triggers on vehicle detection
2. `CameraAnimalSensor` class - MotionSensor service, only triggers on animal detection
3. `CameraPackageSensor` class - MotionSensor service, only triggers on package detection
4. `trigger_vehicle()`, `trigger_animal()`, `trigger_package()` methods
5. Event routing based on `smart_detection_type`
6. Sensors created for each camera in bridge startup

**Design Decision:** Use MotionSensor service (not custom characteristics) for vehicle/animal/package sensors because:
- HomeKit automations fully support MotionSensor triggers
- Users can name sensors clearly (e.g., "Driveway Vehicle Detector")
- Consistent with occupancy sensor approach (separate accessory per detection type)
- No need for custom HomeKit categories or services

**PRD Reference:** docs/PRD-phase5.md (FR7)
**Tech Spec Reference:** docs/sprint-artifacts/tech-spec-epic-p5-1.md (P5-1.6-1 through P5-1.6-4)

---

## Acceptance Criteria

### AC1: Vehicle Detection Triggers Vehicle Sensor
- [x] `CameraVehicleSensor` class created using MotionSensor service
- [x] Vehicle sensor named "{camera_name} Vehicle" to distinguish from motion sensor
- [x] Only triggers when `smart_detection_type == 'vehicle'`
- [x] Auto-reset after configurable timeout (default 30 seconds)
- [x] Does NOT trigger occupancy sensor

### AC2: Animal Detection Triggers Animal Sensor
- [x] `CameraAnimalSensor` class created using MotionSensor service
- [x] Animal sensor named "{camera_name} Animal" to distinguish
- [x] Only triggers when `smart_detection_type == 'animal'`
- [x] Auto-reset after configurable timeout (default 30 seconds)
- [x] Does NOT trigger occupancy sensor

### AC3: Package Detection Triggers Package Sensor
- [x] `CameraPackageSensor` class created using MotionSensor service
- [x] Package sensor named "{camera_name} Package" to distinguish
- [x] Only triggers when `smart_detection_type == 'package'`
- [x] Auto-reset after configurable timeout (default 60 seconds, packages persist)
- [x] Does NOT trigger occupancy sensor

### AC4: Each Detection Type Can Trigger Separate Automations
- [x] Vehicle sensor can trigger HomeKit automations independently
- [x] Animal sensor can trigger HomeKit automations independently
- [x] Package sensor can trigger HomeKit automations independently
- [x] Motion sensor continues to trigger on ALL detection types (unchanged behavior)
- [x] Occupancy sensor continues to trigger only on person detection

---

## Tasks / Subtasks

### Task 1: Create Vehicle/Animal/Package Sensor Classes (AC: 1, 2, 3)
**File:** `backend/app/services/homekit_accessories.py`
- [x] Create `CameraVehicleSensor` class following `CameraMotionSensor` pattern
- [x] Create `CameraAnimalSensor` class following `CameraMotionSensor` pattern
- [x] Create `CameraPackageSensor` class following `CameraMotionSensor` pattern
- [x] All use HAP-python MotionSensor service (same as motion, different naming)
- [x] Add `set_detected()`, `trigger_detection()`, `clear_detection()` methods
- [x] Add `create_vehicle_sensor()`, `create_animal_sensor()`, `create_package_sensor()` factory functions

### Task 2: Add Sensor Configuration Options (AC: 1, 2, 3)
**File:** `backend/app/config/homekit.py`
- [x] Add `DEFAULT_VEHICLE_RESET_SECONDS = 30` constant
- [x] Add `DEFAULT_ANIMAL_RESET_SECONDS = 30` constant
- [x] Add `DEFAULT_PACKAGE_RESET_SECONDS = 60` constant (packages persist longer)
- [x] Add `vehicle_reset_seconds`, `animal_reset_seconds`, `package_reset_seconds` to `HomekitConfig`
- [x] Load from environment variables `HOMEKIT_VEHICLE_RESET_SECONDS`, etc.

### Task 3: Implement trigger Methods in HomeKit Service (AC: 1, 2, 3)
**File:** `backend/app/services/homekit_service.py`
- [x] Add `_vehicle_sensors: Dict[str, CameraVehicleSensor]` storage
- [x] Add `_animal_sensors: Dict[str, CameraAnimalSensor]` storage
- [x] Add `_package_sensors: Dict[str, CameraPackageSensor]` storage
- [x] Add reset task dicts for each sensor type
- [x] Implement `trigger_vehicle(camera_id, event_id)` with auto-reset timer
- [x] Implement `trigger_animal(camera_id, event_id)` with auto-reset timer
- [x] Implement `trigger_package(camera_id, event_id)` with auto-reset timer
- [x] Update `stop()` to cancel all reset timers and clear state
- [x] Update `get_status()` to include vehicle/animal/package sensor counts

### Task 4: Create Sensors in Bridge Startup (AC: 1, 2, 3)
**File:** `backend/app/services/homekit_service.py`
- [x] In `start()` method, create vehicle sensor for each camera: `f"{camera_name} Vehicle"`
- [x] In `start()` method, create animal sensor for each camera: `f"{camera_name} Animal"`
- [x] In `start()` method, create package sensor for each camera: `f"{camera_name} Package"`
- [x] Add all sensors to bridge: `self._bridge.add_accessory()`
- [x] Add `vehicle_count`, `animal_count`, `package_count` to `HomekitStatus`

### Task 5: Integrate with Event Processor (AC: 1, 2, 3, 4)
**File:** `backend/app/services/event_processor.py`
- [x] Add `_trigger_homekit_vehicle()` helper method
- [x] Add `_trigger_homekit_animal()` helper method
- [x] Add `_trigger_homekit_package()` helper method
- [x] Route `smart_detection_type == 'vehicle'` to vehicle sensor
- [x] Route `smart_detection_type == 'animal'` to animal sensor
- [x] Route `smart_detection_type == 'package'` to package sensor
- [x] Keep motion sensor triggering on ALL types (existing behavior)
- [x] Keep occupancy sensor triggering only on person (existing behavior)

### Task 6: Write Unit Tests (AC: 1, 2, 3, 4)
**File:** `backend/tests/test_services/test_homekit_detection_sensors.py`
- [x] Test `CameraVehicleSensor` class creation
- [x] Test `CameraAnimalSensor` class creation
- [x] Test `CameraPackageSensor` class creation
- [x] Test `trigger_vehicle()` sets sensor state
- [x] Test `trigger_animal()` sets sensor state
- [x] Test `trigger_package()` sets sensor state
- [x] Test vehicle detection triggers only vehicle sensor (not occupancy)
- [x] Test animal detection triggers only animal sensor (not occupancy)
- [x] Test package detection triggers only package sensor (not occupancy)
- [x] Test auto-reset timeouts for each sensor type
- [x] Test motion sensor still triggers on all types
- [x] Test unknown camera returns False

---

## Dev Notes

### HAP-python MotionSensor Service

All three new sensor types use the same MotionSensor service but with different names:
- Type: `bool` (True = Motion Detected, False = No Motion)
- Service UUID: `0085` (MotionSensor)

```python
# Example implementation pattern (same as CameraMotionSensor)
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR

class CameraVehicleSensor:
    def __init__(self, driver, camera_id: str, name: str):
        self._accessory = Accessory(driver, name)
        self._accessory.category = CATEGORY_SENSOR

        # Use MotionSensor service - HomeKit identifies by accessory name
        self._motion_service = self._accessory.add_preload_service("MotionSensor")
        self._motion_char = self._motion_service.configure_char(
            "MotionDetected",
            value=False
        )

    def trigger_detection(self):
        self._motion_char.set_value(True)

    def clear_detection(self):
        self._motion_char.set_value(False)
```

### Event Routing Logic

The event processor should route events as follows:
```
Event Created
    │
    ├─> trigger_motion() [always, for ANY detection]
    │
    ├─> smart_detection_type == 'person'?
    │       └─> Yes: trigger_occupancy() [5-minute timeout]
    │
    ├─> smart_detection_type == 'vehicle'?
    │       └─> Yes: trigger_vehicle() [30-second timeout]
    │
    ├─> smart_detection_type == 'animal'?
    │       └─> Yes: trigger_animal() [30-second timeout]
    │
    └─> smart_detection_type == 'package'?
            └─> Yes: trigger_package() [60-second timeout]
```

### Configuration Options (Environment Variables)

| Setting | Default | Environment Variable | Description |
|---------|---------|---------------------|-------------|
| vehicle_reset_seconds | 30 | HOMEKIT_VEHICLE_RESET_SECONDS | Seconds before vehicle sensor resets |
| animal_reset_seconds | 30 | HOMEKIT_ANIMAL_RESET_SECONDS | Seconds before animal sensor resets |
| package_reset_seconds | 60 | HOMEKIT_PACKAGE_RESET_SECONDS | Seconds before package sensor resets |

### Learnings from Previous Story

**From Story P5-1.5 (Status: done)**

- **CameraOccupancySensor class** - Created in `homekit_accessories.py` following CameraMotionSensor pattern
  - Uses HAP-python OccupancySensor service
  - OccupancyDetected characteristic set to 0/1 integer (vs boolean for motion)
  - Factory function `create_occupancy_sensor()` provided

- **Auto-reset timer infrastructure** - Implemented in `homekit_service.py:734-873`:
  - Resolves camera ID through mapping (supports MAC addresses)
  - 5-minute auto-reset timer with `_occupancy_reset_coroutine()`
  - Max duration check to prevent stuck state
  - Rapid detections extend timeout (timer reset on each trigger)

- **Event Processor Integration** - Added at `event_processor.py:1036-1045`:
  - Only triggers when `smart_detection_type == 'person'`
  - Motion sensor continues to trigger for all events
  - Fire-and-forget async pattern (non-blocking)

- **Test Suite Pattern** - Created `test_homekit_occupancy.py` with 19 tests:
  - TestHomekitOccupancyTrigger (10 tests)
  - TestHomekitOccupancyEventFiltering (2 tests)
  - TestHomekitOccupancyConfig (4 tests)
  - TestCameraOccupancySensorClass (3 tests)

[Source: docs/sprint-artifacts/p5-1-5-implement-occupancy-sensor-for-person-detection.md#Dev-Agent-Record]

### Project Structure Notes

- New sensor classes go in existing `homekit_accessories.py`
- Configuration additions go in existing `app/config/homekit.py`
- New test file `test_homekit_detection_sensors.py` in `backend/tests/test_services/`
- Event processor integration follows existing HomeKit motion/occupancy pattern

### References

- HAP-python MotionSensor: https://github.com/ikalchev/HAP-python
- Tech spec: `docs/sprint-artifacts/tech-spec-epic-p5-1.md` (P5-1.6 section)
- Motion sensor implementation: `backend/app/services/homekit_accessories.py`
- Occupancy sensor implementation: `backend/app/services/homekit_accessories.py:148-274`
- Event processor: `backend/app/services/event_processor.py:1036-1045`

---

## Dev Agent Record

### Context Reference

- [docs/sprint-artifacts/p5-1-6-add-vehicle-animal-package-sensor-accessories.context.xml](p5-1-6-add-vehicle-animal-package-sensor-accessories.context.xml)

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created three new sensor classes (`CameraVehicleSensor`, `CameraAnimalSensor`, `CameraPackageSensor`) in `homekit_accessories.py` following the established `CameraMotionSensor` pattern
2. All three sensor classes use the HAP-python MotionSensor service with unique names to enable distinct HomeKit automations
3. Added configuration constants and environment variable support for sensor reset timeouts (30s vehicle, 30s animal, 60s package)
4. Implemented `trigger_vehicle()`, `trigger_animal()`, `trigger_package()` methods in `homekit_service.py` with auto-reset timer infrastructure
5. Updated `stop()` method to properly cancel all reset timers and clear sensor dictionaries
6. Updated `get_status()` to include vehicle_count, animal_count, package_count in HomekitStatus
7. Integrated with event_processor.py to route detection events based on `smart_detection_type`
8. Created comprehensive test suite with 35 tests covering all ACs - all tests pass
9. Verified existing 145 HomeKit tests still pass after changes

### File List

**Modified:**
- `backend/app/services/homekit_accessories.py` - Added CameraVehicleSensor, CameraAnimalSensor, CameraPackageSensor classes and factory functions
- `backend/app/config/homekit.py` - Added detection sensor configuration constants and fields
- `backend/app/services/homekit_service.py` - Added trigger methods, sensor storage, status updates, stop() cleanup
- `backend/app/services/event_processor.py` - Added detection-type routing and helper methods

**Created:**
- `backend/tests/test_services/test_homekit_detection_sensors.py` - 35 unit tests for detection sensors

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | SM Agent (Claude Opus 4.5) | Initial story creation |
| 2025-12-14 | Dev Agent (Claude Opus 4.5) | Implementation complete - all ACs verified |
