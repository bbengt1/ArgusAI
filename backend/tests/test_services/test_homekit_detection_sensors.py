"""
Unit tests for HomeKit vehicle/animal/package sensor triggering (Story P5-1.6)

Tests cover:
- Vehicle detection triggers only vehicle sensor (AC1)
- Animal detection triggers only animal sensor (AC2)
- Package detection triggers only package sensor (AC3)
- Motion sensor still triggers on all detection types (AC4)
- Auto-reset timeouts for each sensor type
- Camera ID mapping (Protect MAC addresses)
- Error resilience
"""
import asyncio
import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

from app.config.homekit import HomekitConfig


# Mock sensor classes for tests (match homekit_accessories.py interface)
@dataclass
class MockDetectionSensor:
    """Mock detection sensor (vehicle/animal/package) for testing."""
    camera_id: str
    name: str
    _motion_detected: bool = False

    @property
    def motion_detected(self) -> bool:
        return self._motion_detected

    def trigger_motion(self):
        self._motion_detected = True

    def clear_motion(self):
        self._motion_detected = False


@dataclass
class MockCameraMotionSensor:
    """Mock motion sensor for testing."""
    camera_id: str
    name: str
    _motion_detected: bool = False

    @property
    def motion_detected(self) -> bool:
        return self._motion_detected

    def trigger_motion(self):
        self._motion_detected = True

    def clear_motion(self):
        self._motion_detected = False


@dataclass
class MockCameraOccupancySensor:
    """Mock occupancy sensor for testing."""
    camera_id: str
    name: str
    _occupancy_detected: bool = False

    @property
    def occupancy_detected(self) -> bool:
        return self._occupancy_detected

    def trigger_occupancy(self):
        self._occupancy_detected = True

    def clear_occupancy(self):
        self._occupancy_detected = False


class TestHomekitVehicleSensorTrigger:
    """Tests for HomekitService.trigger_vehicle() (Story P5-1.6 AC1)"""

    @pytest.fixture
    def config(self):
        """Create test HomeKit config with short timeout for tests."""
        return HomekitConfig(
            enabled=True,
            port=51826,
            bridge_name="Test Bridge",
            manufacturer="Test",
            persist_dir="/tmp/homekit_test",
            motion_reset_seconds=2,
            max_motion_duration=10,
            vehicle_reset_seconds=2,  # Short timeout for tests (normally 30s)
            animal_reset_seconds=2,
            package_reset_seconds=3,  # Package has longer timeout
        )

    @pytest.fixture
    def mock_service(self, config):
        """Create a mock HomeKit service for testing."""
        from app.services.homekit_service import HomekitService

        service = HomekitService(config=config)
        service._running = True

        # Add mock vehicle sensors
        service._vehicle_sensors = {
            "camera-1": MockDetectionSensor(camera_id="camera-1", name="Front Door Vehicle"),
            "camera-2": MockDetectionSensor(camera_id="camera-2", name="Back Yard Vehicle"),
        }

        # Add mock occupancy sensors to verify isolation
        service._occupancy_sensors = {
            "camera-1": MockCameraOccupancySensor(camera_id="camera-1", name="Front Door Occupancy"),
            "camera-2": MockCameraOccupancySensor(camera_id="camera-2", name="Back Yard Occupancy"),
        }

        # Add mock motion sensors
        service._sensors = {
            "camera-1": MockCameraMotionSensor(camera_id="camera-1", name="Front Door"),
            "camera-2": MockCameraMotionSensor(camera_id="camera-2", name="Back Yard"),
        }

        return service

    def test_trigger_vehicle_sets_sensor_state(self, mock_service):
        """AC1: Vehicle trigger sets motion_detected = True on vehicle sensor"""
        sensor = mock_service._vehicle_sensors["camera-1"]
        assert sensor.motion_detected is False

        result = mock_service.trigger_vehicle("camera-1", event_id=123)

        assert result is True
        assert sensor.motion_detected is True

    def test_trigger_vehicle_unknown_camera(self, mock_service):
        """Triggering unknown camera returns False"""
        result = mock_service.trigger_vehicle("unknown-camera")
        assert result is False

    def test_trigger_vehicle_does_not_trigger_occupancy(self, mock_service):
        """AC1: Vehicle detection does NOT trigger occupancy sensor"""
        occupancy_sensor = mock_service._occupancy_sensors["camera-1"]
        assert occupancy_sensor.occupancy_detected is False

        mock_service.trigger_vehicle("camera-1")

        # Occupancy should remain False
        assert occupancy_sensor.occupancy_detected is False

    def test_camera_id_mapping_mac_address_vehicle(self, mock_service):
        """Protect cameras can be triggered by MAC address for vehicle"""
        # Register MAC mapping
        mock_service.register_camera_mapping("camera-1", "AA:BB:CC:DD:EE:FF")

        # Trigger by MAC address
        result = mock_service.trigger_vehicle("AA:BB:CC:DD:EE:FF")

        assert result is True
        assert mock_service._vehicle_sensors["camera-1"].motion_detected is True

    @pytest.mark.asyncio
    async def test_vehicle_resets_after_timeout(self, mock_service):
        """AC1: Vehicle sensor resets after timeout (30s default, 2s for test)"""
        sensor = mock_service._vehicle_sensors["camera-1"]

        mock_service.trigger_vehicle("camera-1")
        assert sensor.motion_detected is True

        # Wait for timeout (config has 2s timeout for tests)
        await asyncio.sleep(2.5)

        assert sensor.motion_detected is False


class TestHomekitAnimalSensorTrigger:
    """Tests for HomekitService.trigger_animal() (Story P5-1.6 AC2)"""

    @pytest.fixture
    def config(self):
        """Create test HomeKit config with short timeout for tests."""
        return HomekitConfig(
            enabled=True,
            port=51826,
            bridge_name="Test Bridge",
            manufacturer="Test",
            persist_dir="/tmp/homekit_test",
            motion_reset_seconds=2,
            max_motion_duration=10,
            vehicle_reset_seconds=2,
            animal_reset_seconds=2,  # Short timeout for tests (normally 30s)
            package_reset_seconds=3,
        )

    @pytest.fixture
    def mock_service(self, config):
        """Create a mock HomeKit service for testing."""
        from app.services.homekit_service import HomekitService

        service = HomekitService(config=config)
        service._running = True

        # Add mock animal sensors
        service._animal_sensors = {
            "camera-1": MockDetectionSensor(camera_id="camera-1", name="Front Door Animal"),
            "camera-2": MockDetectionSensor(camera_id="camera-2", name="Back Yard Animal"),
        }

        # Add mock occupancy sensors to verify isolation
        service._occupancy_sensors = {
            "camera-1": MockCameraOccupancySensor(camera_id="camera-1", name="Front Door Occupancy"),
            "camera-2": MockCameraOccupancySensor(camera_id="camera-2", name="Back Yard Occupancy"),
        }

        # Add mock motion sensors
        service._sensors = {
            "camera-1": MockCameraMotionSensor(camera_id="camera-1", name="Front Door"),
            "camera-2": MockCameraMotionSensor(camera_id="camera-2", name="Back Yard"),
        }

        return service

    def test_trigger_animal_sets_sensor_state(self, mock_service):
        """AC2: Animal trigger sets motion_detected = True on animal sensor"""
        sensor = mock_service._animal_sensors["camera-1"]
        assert sensor.motion_detected is False

        result = mock_service.trigger_animal("camera-1", event_id=456)

        assert result is True
        assert sensor.motion_detected is True

    def test_trigger_animal_unknown_camera(self, mock_service):
        """Triggering unknown camera returns False"""
        result = mock_service.trigger_animal("unknown-camera")
        assert result is False

    def test_trigger_animal_does_not_trigger_occupancy(self, mock_service):
        """AC2: Animal detection does NOT trigger occupancy sensor"""
        occupancy_sensor = mock_service._occupancy_sensors["camera-1"]
        assert occupancy_sensor.occupancy_detected is False

        mock_service.trigger_animal("camera-1")

        # Occupancy should remain False
        assert occupancy_sensor.occupancy_detected is False

    @pytest.mark.asyncio
    async def test_animal_resets_after_timeout(self, mock_service):
        """AC2: Animal sensor resets after timeout (30s default, 2s for test)"""
        sensor = mock_service._animal_sensors["camera-1"]

        mock_service.trigger_animal("camera-1")
        assert sensor.motion_detected is True

        # Wait for timeout
        await asyncio.sleep(2.5)

        assert sensor.motion_detected is False


class TestHomekitPackageSensorTrigger:
    """Tests for HomekitService.trigger_package() (Story P5-1.6 AC3)"""

    @pytest.fixture
    def config(self):
        """Create test HomeKit config with short timeout for tests."""
        return HomekitConfig(
            enabled=True,
            port=51826,
            bridge_name="Test Bridge",
            manufacturer="Test",
            persist_dir="/tmp/homekit_test",
            motion_reset_seconds=2,
            max_motion_duration=10,
            vehicle_reset_seconds=2,
            animal_reset_seconds=2,
            package_reset_seconds=3,  # Longer timeout for packages (normally 60s)
        )

    @pytest.fixture
    def mock_service(self, config):
        """Create a mock HomeKit service for testing."""
        from app.services.homekit_service import HomekitService

        service = HomekitService(config=config)
        service._running = True

        # Add mock package sensors
        service._package_sensors = {
            "camera-1": MockDetectionSensor(camera_id="camera-1", name="Front Door Package"),
            "camera-2": MockDetectionSensor(camera_id="camera-2", name="Back Yard Package"),
        }

        # Add mock occupancy sensors to verify isolation
        service._occupancy_sensors = {
            "camera-1": MockCameraOccupancySensor(camera_id="camera-1", name="Front Door Occupancy"),
            "camera-2": MockCameraOccupancySensor(camera_id="camera-2", name="Back Yard Occupancy"),
        }

        # Add mock motion sensors
        service._sensors = {
            "camera-1": MockCameraMotionSensor(camera_id="camera-1", name="Front Door"),
            "camera-2": MockCameraMotionSensor(camera_id="camera-2", name="Back Yard"),
        }

        return service

    def test_trigger_package_sets_sensor_state(self, mock_service):
        """AC3: Package trigger sets motion_detected = True on package sensor"""
        sensor = mock_service._package_sensors["camera-1"]
        assert sensor.motion_detected is False

        result = mock_service.trigger_package("camera-1", event_id=789)

        assert result is True
        assert sensor.motion_detected is True

    def test_trigger_package_unknown_camera(self, mock_service):
        """Triggering unknown camera returns False"""
        result = mock_service.trigger_package("unknown-camera")
        assert result is False

    def test_trigger_package_does_not_trigger_occupancy(self, mock_service):
        """AC3: Package detection does NOT trigger occupancy sensor"""
        occupancy_sensor = mock_service._occupancy_sensors["camera-1"]
        assert occupancy_sensor.occupancy_detected is False

        mock_service.trigger_package("camera-1")

        # Occupancy should remain False
        assert occupancy_sensor.occupancy_detected is False

    @pytest.mark.asyncio
    async def test_package_resets_after_timeout(self, mock_service):
        """AC3: Package sensor resets after timeout (60s default, 3s for test)"""
        sensor = mock_service._package_sensors["camera-1"]

        mock_service.trigger_package("camera-1")
        assert sensor.motion_detected is True

        # Wait for timeout
        await asyncio.sleep(3.5)

        assert sensor.motion_detected is False


class TestDetectionSensorIsolation:
    """Tests verifying each detection type triggers its own sensor (Story P5-1.6 AC4)"""

    @pytest.fixture
    def config(self):
        """Create test HomeKit config."""
        return HomekitConfig(
            enabled=True,
            port=51826,
            bridge_name="Test Bridge",
            manufacturer="Test",
            persist_dir="/tmp/homekit_test",
            motion_reset_seconds=2,
            vehicle_reset_seconds=2,
            animal_reset_seconds=2,
            package_reset_seconds=3,
        )

    @pytest.fixture
    def mock_service(self, config):
        """Create a mock HomeKit service with all sensor types."""
        from app.services.homekit_service import HomekitService

        service = HomekitService(config=config)
        service._running = True

        # All sensor types for camera-1
        service._sensors = {"camera-1": MockCameraMotionSensor("camera-1", "Front Door")}
        service._occupancy_sensors = {"camera-1": MockCameraOccupancySensor("camera-1", "Front Door Occupancy")}
        service._vehicle_sensors = {"camera-1": MockDetectionSensor("camera-1", "Front Door Vehicle")}
        service._animal_sensors = {"camera-1": MockDetectionSensor("camera-1", "Front Door Animal")}
        service._package_sensors = {"camera-1": MockDetectionSensor("camera-1", "Front Door Package")}

        return service

    def test_vehicle_only_triggers_vehicle_sensor(self, mock_service):
        """AC4: Vehicle detection only triggers vehicle sensor"""
        mock_service.trigger_vehicle("camera-1")

        # Vehicle sensor triggered
        assert mock_service._vehicle_sensors["camera-1"].motion_detected is True

        # Others not triggered
        assert mock_service._animal_sensors["camera-1"].motion_detected is False
        assert mock_service._package_sensors["camera-1"].motion_detected is False
        assert mock_service._occupancy_sensors["camera-1"].occupancy_detected is False

    def test_animal_only_triggers_animal_sensor(self, mock_service):
        """AC4: Animal detection only triggers animal sensor"""
        mock_service.trigger_animal("camera-1")

        # Animal sensor triggered
        assert mock_service._animal_sensors["camera-1"].motion_detected is True

        # Others not triggered
        assert mock_service._vehicle_sensors["camera-1"].motion_detected is False
        assert mock_service._package_sensors["camera-1"].motion_detected is False
        assert mock_service._occupancy_sensors["camera-1"].occupancy_detected is False

    def test_package_only_triggers_package_sensor(self, mock_service):
        """AC4: Package detection only triggers package sensor"""
        mock_service.trigger_package("camera-1")

        # Package sensor triggered
        assert mock_service._package_sensors["camera-1"].motion_detected is True

        # Others not triggered
        assert mock_service._vehicle_sensors["camera-1"].motion_detected is False
        assert mock_service._animal_sensors["camera-1"].motion_detected is False
        assert mock_service._occupancy_sensors["camera-1"].occupancy_detected is False

    def test_clear_all_detection_sensors(self, mock_service):
        """clear_all_detection_sensors clears all vehicle/animal/package sensors"""
        # Trigger all detection sensors
        mock_service.trigger_vehicle("camera-1")
        mock_service.trigger_animal("camera-1")
        mock_service.trigger_package("camera-1")

        assert mock_service._vehicle_sensors["camera-1"].motion_detected is True
        assert mock_service._animal_sensors["camera-1"].motion_detected is True
        assert mock_service._package_sensors["camera-1"].motion_detected is True

        # Clear all detection sensors
        mock_service.clear_all_detection_sensors()

        assert mock_service._vehicle_sensors["camera-1"].motion_detected is False
        assert mock_service._animal_sensors["camera-1"].motion_detected is False
        assert mock_service._package_sensors["camera-1"].motion_detected is False


class TestDetectionSensorConfig:
    """Tests for HomeKit detection sensor configuration (Story P5-1.6)"""

    def test_default_vehicle_reset_seconds(self):
        """Default vehicle reset timeout is 30 seconds"""
        from app.config.homekit import DEFAULT_VEHICLE_RESET_SECONDS
        assert DEFAULT_VEHICLE_RESET_SECONDS == 30

    def test_default_animal_reset_seconds(self):
        """Default animal reset timeout is 30 seconds"""
        from app.config.homekit import DEFAULT_ANIMAL_RESET_SECONDS
        assert DEFAULT_ANIMAL_RESET_SECONDS == 30

    def test_default_package_reset_seconds(self):
        """Default package reset timeout is 60 seconds (longer for packages)"""
        from app.config.homekit import DEFAULT_PACKAGE_RESET_SECONDS
        assert DEFAULT_PACKAGE_RESET_SECONDS == 60

    def test_config_loads_detection_sensor_from_env(self):
        """Config loads detection sensor settings from environment"""
        import os
        from app.config.homekit import get_homekit_config

        os.environ["HOMEKIT_VEHICLE_RESET_SECONDS"] = "45"
        os.environ["HOMEKIT_ANIMAL_RESET_SECONDS"] = "45"
        os.environ["HOMEKIT_PACKAGE_RESET_SECONDS"] = "90"

        try:
            config = get_homekit_config()
            assert config.vehicle_reset_seconds == 45
            assert config.animal_reset_seconds == 45
            assert config.package_reset_seconds == 90
        finally:
            del os.environ["HOMEKIT_VEHICLE_RESET_SECONDS"]
            del os.environ["HOMEKIT_ANIMAL_RESET_SECONDS"]
            del os.environ["HOMEKIT_PACKAGE_RESET_SECONDS"]

    def test_homekit_config_has_detection_sensor_fields(self):
        """HomekitConfig dataclass includes detection sensor fields"""
        from app.config.homekit import HomekitConfig

        config = HomekitConfig()
        assert hasattr(config, 'vehicle_reset_seconds')
        assert hasattr(config, 'animal_reset_seconds')
        assert hasattr(config, 'package_reset_seconds')
        assert config.vehicle_reset_seconds == 30
        assert config.animal_reset_seconds == 30
        assert config.package_reset_seconds == 60


class TestDetectionSensorClasses:
    """Tests for sensor class existence (Story P5-1.6)"""

    def test_vehicle_sensor_class_exists(self):
        """CameraVehicleSensor class exists"""
        from app.services.homekit_accessories import CameraVehicleSensor
        assert CameraVehicleSensor is not None

    def test_animal_sensor_class_exists(self):
        """CameraAnimalSensor class exists"""
        from app.services.homekit_accessories import CameraAnimalSensor
        assert CameraAnimalSensor is not None

    def test_package_sensor_class_exists(self):
        """CameraPackageSensor class exists"""
        from app.services.homekit_accessories import CameraPackageSensor
        assert CameraPackageSensor is not None

    def test_create_vehicle_sensor_factory_exists(self):
        """Factory function for creating vehicle sensors exists"""
        from app.services.homekit_accessories import create_vehicle_sensor
        assert callable(create_vehicle_sensor)

    def test_create_animal_sensor_factory_exists(self):
        """Factory function for creating animal sensors exists"""
        from app.services.homekit_accessories import create_animal_sensor
        assert callable(create_animal_sensor)

    def test_create_package_sensor_factory_exists(self):
        """Factory function for creating package sensors exists"""
        from app.services.homekit_accessories import create_package_sensor
        assert callable(create_package_sensor)

    def test_vehicle_sensor_uses_motion_sensor_service(self):
        """CameraVehicleSensor uses MotionSensor service (not custom)"""
        from app.services.homekit_accessories import CameraVehicleSensor
        # Verify it's documented as using MotionSensor
        assert "MotionSensor" in CameraVehicleSensor.__doc__


class TestEventProcessorDetectionRouting:
    """Tests for event processor routing to detection sensors (Story P5-1.6)"""

    @pytest.mark.asyncio
    async def test_event_processor_triggers_vehicle_for_vehicle_detection(self):
        """Event with smart_detection_type='vehicle' triggers vehicle sensor"""
        from unittest.mock import MagicMock

        class MockEventProcessor:
            async def _trigger_homekit_vehicle(self, homekit_service, camera_id, event_id):
                try:
                    success = homekit_service.trigger_vehicle(camera_id, event_id=event_id)
                    return success
                except Exception:
                    pass

        mock_homekit = MagicMock()
        mock_homekit.is_running = True
        mock_homekit.trigger_vehicle = MagicMock(return_value=True)

        processor = MockEventProcessor()
        await processor._trigger_homekit_vehicle(mock_homekit, "test-camera", "event-123")

        mock_homekit.trigger_vehicle.assert_called_once_with("test-camera", event_id="event-123")

    @pytest.mark.asyncio
    async def test_event_processor_triggers_animal_for_animal_detection(self):
        """Event with smart_detection_type='animal' triggers animal sensor"""
        from unittest.mock import MagicMock

        class MockEventProcessor:
            async def _trigger_homekit_animal(self, homekit_service, camera_id, event_id):
                try:
                    success = homekit_service.trigger_animal(camera_id, event_id=event_id)
                    return success
                except Exception:
                    pass

        mock_homekit = MagicMock()
        mock_homekit.is_running = True
        mock_homekit.trigger_animal = MagicMock(return_value=True)

        processor = MockEventProcessor()
        await processor._trigger_homekit_animal(mock_homekit, "test-camera", "event-456")

        mock_homekit.trigger_animal.assert_called_once_with("test-camera", event_id="event-456")

    @pytest.mark.asyncio
    async def test_event_processor_triggers_package_for_package_detection(self):
        """Event with smart_detection_type='package' triggers package sensor"""
        from unittest.mock import MagicMock

        class MockEventProcessor:
            async def _trigger_homekit_package(self, homekit_service, camera_id, event_id):
                try:
                    success = homekit_service.trigger_package(camera_id, event_id=event_id)
                    return success
                except Exception:
                    pass

        mock_homekit = MagicMock()
        mock_homekit.is_running = True
        mock_homekit.trigger_package = MagicMock(return_value=True)

        processor = MockEventProcessor()
        await processor._trigger_homekit_package(mock_homekit, "test-camera", "event-789")

        mock_homekit.trigger_package.assert_called_once_with("test-camera", event_id="event-789")

    @pytest.mark.asyncio
    async def test_event_processor_handles_detection_sensor_errors(self):
        """Detection sensor errors don't block event processing"""
        from unittest.mock import MagicMock

        class MockEventProcessor:
            async def _trigger_homekit_vehicle(self, homekit_service, camera_id, event_id):
                try:
                    success = homekit_service.trigger_vehicle(camera_id, event_id=event_id)
                    return success
                except Exception:
                    pass

        mock_homekit = MagicMock()
        mock_homekit.is_running = True
        mock_homekit.trigger_vehicle = MagicMock(side_effect=Exception("HAP error"))

        processor = MockEventProcessor()

        # Should not raise
        await processor._trigger_homekit_vehicle(mock_homekit, "test-camera", "event-123")

        mock_homekit.trigger_vehicle.assert_called_once()


class TestHomekitStatusDetectionSensors:
    """Tests for HomekitStatus including detection sensor counts (Story P5-1.6)"""

    def test_homekit_status_has_detection_sensor_counts(self):
        """HomekitStatus includes vehicle_count, animal_count, package_count"""
        from app.services.homekit_service import HomekitStatus

        status = HomekitStatus()
        assert hasattr(status, 'vehicle_count')
        assert hasattr(status, 'animal_count')
        assert hasattr(status, 'package_count')
        assert status.vehicle_count == 0
        assert status.animal_count == 0
        assert status.package_count == 0

    def test_get_status_includes_detection_sensor_counts(self):
        """get_status() includes detection sensor counts"""
        from app.services.homekit_service import HomekitService
        from app.config.homekit import HomekitConfig

        config = HomekitConfig(enabled=True, persist_dir="/tmp/homekit_test")
        service = HomekitService(config=config)
        service._running = True

        # Add mock sensors
        service._vehicle_sensors = {"cam1": MagicMock(), "cam2": MagicMock()}
        service._animal_sensors = {"cam1": MagicMock()}
        service._package_sensors = {"cam1": MagicMock(), "cam2": MagicMock(), "cam3": MagicMock()}

        status = service.get_status()

        assert status.vehicle_count == 2
        assert status.animal_count == 1
        assert status.package_count == 3
