"""
Unit tests for VehicleDetectionService (Story P4-8.3)

Tests vehicle detection functionality including:
- Vehicle detection on images with single/multiple/no vehicles
- Confidence threshold filtering
- Vehicle region extraction with padding
- Error handling for invalid input
- Fallback mode when model files not found
"""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
from PIL import Image


# Create a simple test image with a colored rectangle (simulating a vehicle region)
def create_test_image(width: int = 300, height: int = 300, has_vehicle: bool = True) -> bytes:
    """Create a test image as bytes.

    Args:
        width: Image width
        height: Image height
        has_vehicle: If True, add a vehicle-like region (car-colored rectangle)

    Returns:
        JPEG bytes of the test image
    """
    # Create a simple image with numpy
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Fill with background color (road-like gray)
    img[:, :] = [128, 128, 128]  # BGR gray background

    if has_vehicle:
        # Add a car-colored rectangle (vehicle-like region)
        vehicle_x1, vehicle_y1 = width // 4, height // 3
        vehicle_x2, vehicle_y2 = 3 * width // 4, 2 * height // 3
        img[vehicle_y1:vehicle_y2, vehicle_x1:vehicle_x2] = [50, 50, 150]  # BGR reddish car

    # Convert to PIL Image and save as JPEG
    pil_img = Image.fromarray(img[:, :, ::-1])  # BGR to RGB
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestVehicleDetectionService:
    """Tests for VehicleDetectionService class."""

    @pytest.fixture
    def vehicle_service(self):
        """Create a VehicleDetectionService instance."""
        from app.services.vehicle_detection_service import VehicleDetectionService

        service = VehicleDetectionService()
        return service

    def test_service_initialization(self, vehicle_service):
        """Test that service initializes correctly."""
        assert vehicle_service is not None
        assert vehicle_service.CONFIDENCE_THRESHOLD == 0.50
        assert vehicle_service.TARGET_SIZE == (224, 224)
        assert vehicle_service.DEFAULT_PADDING == 0.1
        assert vehicle_service._model_loaded is False

    def test_is_model_loaded_initially_false(self, vehicle_service):
        """Test that model is not loaded initially."""
        assert vehicle_service.is_model_loaded() is False

    def test_is_using_fallback_initially_false(self, vehicle_service):
        """Test that fallback is not active initially."""
        assert vehicle_service.is_using_fallback() is False

    def test_bounding_box_to_dict(self):
        """Test BoundingBox serialization."""
        from app.services.vehicle_detection_service import BoundingBox

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        result = bbox.to_dict()

        assert result == {"x": 10, "y": 20, "width": 100, "height": 150}

    def test_bounding_box_from_dict(self):
        """Test BoundingBox deserialization."""
        from app.services.vehicle_detection_service import BoundingBox

        data = {"x": 10, "y": 20, "width": 100, "height": 150}
        bbox = BoundingBox.from_dict(data)

        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 150

    def test_vehicle_detection_dataclass(self):
        """Test VehicleDetection dataclass."""
        from app.services.vehicle_detection_service import BoundingBox, VehicleDetection

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        detection = VehicleDetection(
            bbox=bbox,
            confidence=0.95,
            vehicle_type="car"
        )

        assert detection.confidence == 0.95
        assert detection.vehicle_type == "car"
        assert detection.bbox.x == 10

    def test_voc_vehicle_indices(self):
        """Test that VOC vehicle class indices are correct."""
        from app.services.vehicle_detection_service import VOC_VEHICLE_INDICES

        assert 6 in VOC_VEHICLE_INDICES  # bus
        assert 7 in VOC_VEHICLE_INDICES  # car
        assert 14 in VOC_VEHICLE_INDICES  # motorbike
        assert 19 in VOC_VEHICLE_INDICES  # train

        assert VOC_VEHICLE_INDICES[7] == "car"
        assert VOC_VEHICLE_INDICES[6] == "bus"

    @pytest.mark.asyncio
    async def test_detect_vehicles_fallback_mode(self, vehicle_service):
        """Test that fallback mode returns empty list."""
        # Force fallback mode
        vehicle_service._use_fallback = True
        vehicle_service._model_loaded = True

        test_image = create_test_image()

        vehicles = await vehicle_service.detect_vehicles(test_image)

        assert vehicles == []

    @pytest.mark.asyncio
    async def test_detect_vehicles_with_mocked_model(self, vehicle_service):
        """Test vehicle detection with mocked OpenCV model."""
        mock_net = MagicMock()

        # Create mock detection output for MobileNet-SSD
        # Shape: (1, 1, num_detections, 7)
        # Each detection: [batch_id, class_id, confidence, x1, y1, x2, y2]
        # Class 7 = car in VOC
        mock_detections = np.array([[[[0, 7, 0.95, 0.1, 0.2, 0.8, 0.7]]]])
        mock_net.forward.return_value = mock_detections

        vehicle_service._net = mock_net
        vehicle_service._model_loaded = True
        vehicle_service._use_fallback = False

        test_image = create_test_image()

        vehicles = await vehicle_service.detect_vehicles(test_image)

        assert len(vehicles) == 1
        assert vehicles[0].confidence == 0.95
        assert vehicles[0].vehicle_type == "car"
        assert vehicles[0].bbox.x >= 0
        assert vehicles[0].bbox.y >= 0
        assert vehicles[0].bbox.width > 0
        assert vehicles[0].bbox.height > 0

    @pytest.mark.asyncio
    async def test_detect_vehicles_no_vehicles_found(self, vehicle_service):
        """Test vehicle detection returns empty list when no vehicles found."""
        mock_net = MagicMock()

        # Create mock detection output with person (class 15), not vehicle
        mock_detections = np.array([[[[0, 15, 0.95, 0.1, 0.1, 0.9, 0.9]]]])
        mock_net.forward.return_value = mock_detections

        vehicle_service._net = mock_net
        vehicle_service._model_loaded = True
        vehicle_service._use_fallback = False

        test_image = create_test_image(has_vehicle=False)

        vehicles = await vehicle_service.detect_vehicles(test_image)

        assert vehicles == []

    @pytest.mark.asyncio
    async def test_detect_vehicles_multiple_vehicles(self, vehicle_service):
        """Test vehicle detection with multiple vehicles of different types."""
        mock_net = MagicMock()

        # Create mock detection output with car, bus, and motorcycle
        mock_detections = np.array([[
            [[0, 7, 0.9, 0.1, 0.1, 0.4, 0.4]],   # car
            [[0, 6, 0.85, 0.5, 0.5, 0.8, 0.8]],  # bus
            [[0, 14, 0.7, 0.2, 0.6, 0.4, 0.9]], # motorbike
        ]])
        mock_detections = mock_detections.reshape(1, 1, 3, 7)
        mock_net.forward.return_value = mock_detections

        vehicle_service._net = mock_net
        vehicle_service._model_loaded = True
        vehicle_service._use_fallback = False

        test_image = create_test_image()

        vehicles = await vehicle_service.detect_vehicles(test_image)

        assert len(vehicles) == 3
        vehicle_types = [v.vehicle_type for v in vehicles]
        assert "car" in vehicle_types
        assert "bus" in vehicle_types
        assert "motorbike" in vehicle_types

    @pytest.mark.asyncio
    async def test_detect_vehicles_custom_confidence_threshold(self, vehicle_service):
        """Test vehicle detection with custom confidence threshold."""
        mock_net = MagicMock()

        # Create mock detection output with various confidences
        mock_detections = np.array([[
            [[0, 7, 0.9, 0.1, 0.1, 0.4, 0.4]],
            [[0, 7, 0.6, 0.5, 0.5, 0.8, 0.8]],
            [[0, 7, 0.3, 0.2, 0.6, 0.4, 0.9]],  # Below default threshold
        ]])
        mock_detections = mock_detections.reshape(1, 1, 3, 7)
        mock_net.forward.return_value = mock_detections

        vehicle_service._net = mock_net
        vehicle_service._model_loaded = True
        vehicle_service._use_fallback = False

        test_image = create_test_image()

        # With default threshold (0.50), should get 2 vehicles
        vehicles = await vehicle_service.detect_vehicles(test_image)
        assert len(vehicles) == 2

        # With higher threshold (0.8), should get only 1 vehicle
        vehicles_high = await vehicle_service.detect_vehicles(
            test_image, confidence_threshold=0.8
        )
        assert len(vehicles_high) == 1
        assert vehicles_high[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_detect_vehicles_low_confidence_filtered(self, vehicle_service):
        """Test that low confidence detections are filtered out."""
        mock_net = MagicMock()

        # Create mock detection output with low confidence
        mock_detections = np.array([[[[0, 7, 0.3, 0.1, 0.1, 0.9, 0.9]]]])
        mock_net.forward.return_value = mock_detections

        vehicle_service._net = mock_net
        vehicle_service._model_loaded = True
        vehicle_service._use_fallback = False

        test_image = create_test_image()

        vehicles = await vehicle_service.detect_vehicles(test_image)

        assert vehicles == []

    def test_crop_vehicle_returns_bytes(self, vehicle_service):
        """Test that vehicle cropping returns valid JPEG bytes."""
        from app.services.vehicle_detection_service import BoundingBox

        test_image = create_test_image(width=300, height=300)
        bbox = BoundingBox(x=50, y=50, width=100, height=100)

        vehicle_bytes = vehicle_service.crop_vehicle(test_image, bbox)

        assert vehicle_bytes is not None
        assert len(vehicle_bytes) > 0

        # Verify it's a valid JPEG
        assert vehicle_bytes[:2] == b'\xff\xd8'  # JPEG magic bytes

    def test_crop_vehicle_correct_size(self, vehicle_service):
        """Test that cropped vehicle has correct target size."""
        from app.services.vehicle_detection_service import BoundingBox

        test_image = create_test_image(width=300, height=300)
        bbox = BoundingBox(x=50, y=50, width=100, height=100)

        vehicle_bytes = vehicle_service.crop_vehicle(test_image, bbox)

        # Verify output size matches TARGET_SIZE (224x224)
        vehicle_img = Image.open(io.BytesIO(vehicle_bytes))
        assert vehicle_img.size == (224, 224)

    def test_crop_vehicle_with_padding(self, vehicle_service):
        """Test vehicle cropping with custom padding."""
        from app.services.vehicle_detection_service import BoundingBox

        test_image = create_test_image(width=300, height=300)
        bbox = BoundingBox(x=100, y=100, width=50, height=50)

        # With 0 padding
        vehicle_bytes_no_pad = vehicle_service.crop_vehicle(
            test_image, bbox, padding=0.0
        )

        # With 50% padding
        vehicle_bytes_pad = vehicle_service.crop_vehicle(
            test_image, bbox, padding=0.5
        )

        # Both should produce valid images (resized to same target)
        assert len(vehicle_bytes_no_pad) > 0
        assert len(vehicle_bytes_pad) > 0


class TestVehicleDetectionServiceSingleton:
    """Tests for singleton pattern."""

    def test_get_vehicle_detection_service_returns_same_instance(self):
        """Test that get_vehicle_detection_service returns singleton."""
        from app.services.vehicle_detection_service import (
            get_vehicle_detection_service,
            reset_vehicle_detection_service,
        )

        # Reset singleton for test
        reset_vehicle_detection_service()

        service1 = get_vehicle_detection_service()
        service2 = get_vehicle_detection_service()

        assert service1 is service2

    def test_reset_vehicle_detection_service(self):
        """Test that reset creates new instance."""
        from app.services.vehicle_detection_service import (
            get_vehicle_detection_service,
            reset_vehicle_detection_service,
        )

        service1 = get_vehicle_detection_service()
        reset_vehicle_detection_service()
        service2 = get_vehicle_detection_service()

        assert service1 is not service2


class TestVehicleDetectionImageConversion:
    """Tests for image conversion utilities."""

    def test_bytes_to_cv2_grayscale(self):
        """Test conversion of grayscale image."""
        from app.services.vehicle_detection_service import VehicleDetectionService

        service = VehicleDetectionService()

        # Create grayscale image
        gray_img = np.zeros((100, 100), dtype=np.uint8)
        gray_img[:] = 128

        pil_img = Image.fromarray(gray_img)
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        cv2_img = service._bytes_to_cv2(image_bytes)

        assert cv2_img.shape == (100, 100, 3)  # Converted to BGR

    def test_bytes_to_cv2_rgba(self):
        """Test conversion of RGBA image."""
        from app.services.vehicle_detection_service import VehicleDetectionService

        service = VehicleDetectionService()

        # Create RGBA image
        rgba_img = np.zeros((100, 100, 4), dtype=np.uint8)
        rgba_img[:, :, :3] = 128
        rgba_img[:, :, 3] = 255  # Alpha channel

        pil_img = Image.fromarray(rgba_img, mode='RGBA')
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")  # PNG supports RGBA
        image_bytes = buffer.getvalue()

        cv2_img = service._bytes_to_cv2(image_bytes)

        assert cv2_img.shape == (100, 100, 3)  # Converted to BGR
