"""
Unit tests for VehicleEmbeddingService (Story P4-8.3)

Tests vehicle embedding service functionality including:
- Processing event vehicles (detection + embedding)
- Storing vehicle embeddings with metadata
- Retrieving vehicle embeddings
- Deleting vehicle embeddings (privacy)
"""
import io
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
from PIL import Image


def create_test_image(width: int = 300, height: int = 300) -> bytes:
    """Create a test image as bytes."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = [128, 128, 128]
    pil_img = Image.fromarray(img[:, :, ::-1])
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestVehicleEmbeddingService:
    """Tests for VehicleEmbeddingService class."""

    @pytest.fixture
    def mock_vehicle_detector(self):
        """Create a mock VehicleDetectionService."""
        from app.services.vehicle_detection_service import BoundingBox, VehicleDetection

        mock = MagicMock()
        mock.detect_vehicles = AsyncMock(return_value=[
            VehicleDetection(
                bbox=BoundingBox(x=50, y=50, width=100, height=80),
                confidence=0.95,
                vehicle_type="car"
            )
        ])
        mock.crop_vehicle = MagicMock(return_value=create_test_image(224, 224))
        return mock

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock EmbeddingService."""
        mock = MagicMock()
        mock.generate_embedding = AsyncMock(return_value=[0.1] * 512)
        return mock

    @pytest.fixture
    def vehicle_service(self, mock_vehicle_detector, mock_embedding_service):
        """Create a VehicleEmbeddingService with mocked dependencies."""
        from app.services.vehicle_embedding_service import VehicleEmbeddingService

        service = VehicleEmbeddingService(
            vehicle_detector=mock_vehicle_detector,
            embedding_service=mock_embedding_service
        )
        return service

    def test_service_initialization(self, vehicle_service):
        """Test that service initializes correctly."""
        assert vehicle_service is not None
        assert vehicle_service.MODEL_VERSION == "clip-ViT-B-32-vehicle-v1"

    def test_get_model_version(self, vehicle_service):
        """Test model version retrieval."""
        assert vehicle_service.get_model_version() == "clip-ViT-B-32-vehicle-v1"

    @pytest.mark.asyncio
    async def test_process_event_vehicles_empty_bytes_raises(self, vehicle_service):
        """Test that empty image bytes raises ValueError."""
        mock_db = MagicMock()

        with pytest.raises(ValueError, match="thumbnail_bytes cannot be empty"):
            await vehicle_service.process_event_vehicles(
                db=mock_db,
                event_id="test-event-id",
                thumbnail_bytes=b""
            )

    @pytest.mark.asyncio
    async def test_process_event_vehicles_success(self, vehicle_service, mock_vehicle_detector):
        """Test successful vehicle processing."""
        from app.models.vehicle_embedding import VehicleEmbedding

        # Create mock DB session
        mock_db = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.id = "test-embedding-id"
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 'test-embedding-id'))

        test_image = create_test_image()

        result = await vehicle_service.process_event_vehicles(
            db=mock_db,
            event_id="test-event-id",
            thumbnail_bytes=test_image
        )

        assert len(result) == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_event_vehicles_no_vehicles_found(self, vehicle_service, mock_vehicle_detector):
        """Test processing when no vehicles are detected."""
        mock_vehicle_detector.detect_vehicles = AsyncMock(return_value=[])

        mock_db = MagicMock()
        test_image = create_test_image()

        result = await vehicle_service.process_event_vehicles(
            db=mock_db,
            event_id="test-event-id",
            thumbnail_bytes=test_image
        )

        assert result == []
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_event_vehicles_multiple_vehicles(self, vehicle_service, mock_vehicle_detector):
        """Test processing with multiple vehicles."""
        from app.services.vehicle_detection_service import BoundingBox, VehicleDetection

        mock_vehicle_detector.detect_vehicles = AsyncMock(return_value=[
            VehicleDetection(
                bbox=BoundingBox(x=10, y=10, width=50, height=40),
                confidence=0.95,
                vehicle_type="car"
            ),
            VehicleDetection(
                bbox=BoundingBox(x=100, y=100, width=60, height=50),
                confidence=0.88,
                vehicle_type="truck"
            ),
        ])

        mock_db = MagicMock()
        mock_db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', f'id-{id(x)}'))
        test_image = create_test_image()

        result = await vehicle_service.process_event_vehicles(
            db=mock_db,
            event_id="test-event-id",
            thumbnail_bytes=test_image
        )

        assert len(result) == 2
        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_get_vehicle_embeddings(self, vehicle_service):
        """Test retrieving vehicle embeddings for an event."""
        # Create mock embedding records
        mock_embedding = MagicMock()
        mock_embedding.id = "emb-1"
        mock_embedding.event_id = "event-1"
        mock_embedding.entity_id = None
        mock_embedding.bounding_box = '{"x": 10, "y": 20, "width": 100, "height": 80}'
        mock_embedding.confidence = 0.95
        mock_embedding.vehicle_type = "car"
        mock_embedding.model_version = "clip-ViT-B-32-vehicle-v1"
        mock_embedding.created_at = datetime.now(timezone.utc)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_embedding]
        mock_db.query.return_value = mock_query

        result = await vehicle_service.get_vehicle_embeddings(mock_db, "event-1")

        assert len(result) == 1
        assert result[0]["id"] == "emb-1"
        assert result[0]["confidence"] == 0.95
        assert result[0]["vehicle_type"] == "car"

    @pytest.mark.asyncio
    async def test_get_vehicle_embedding_vector(self, vehicle_service):
        """Test retrieving embedding vector."""
        mock_embedding = MagicMock()
        mock_embedding.embedding = json.dumps([0.1] * 512)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_embedding

        result = await vehicle_service.get_vehicle_embedding_vector(
            mock_db, "emb-1"
        )

        assert result is not None
        assert len(result) == 512

    @pytest.mark.asyncio
    async def test_get_vehicle_embedding_vector_not_found(self, vehicle_service):
        """Test retrieving non-existent embedding vector."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await vehicle_service.get_vehicle_embedding_vector(
            mock_db, "nonexistent"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_event_vehicles(self, vehicle_service):
        """Test deleting vehicle embeddings for an event."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.delete.return_value = 3

        result = await vehicle_service.delete_event_vehicles(mock_db, "event-1")

        assert result == 3
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_vehicles(self, vehicle_service):
        """Test deleting all vehicle embeddings."""
        mock_db = MagicMock()
        mock_db.query.return_value.delete.return_value = 100

        result = await vehicle_service.delete_all_vehicles(mock_db)

        assert result == 100
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vehicle_count(self, vehicle_service):
        """Test getting vehicle count for an event."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 2

        result = await vehicle_service.get_vehicle_count(mock_db, "event-1")

        assert result == 2

    @pytest.mark.asyncio
    async def test_get_total_vehicle_count(self, vehicle_service):
        """Test getting total vehicle count."""
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 150

        result = await vehicle_service.get_total_vehicle_count(mock_db)

        assert result == 150


class TestVehicleEmbeddingServiceSingleton:
    """Tests for singleton pattern."""

    def test_get_vehicle_embedding_service_returns_same_instance(self):
        """Test that get_vehicle_embedding_service returns singleton."""
        from app.services.vehicle_embedding_service import (
            get_vehicle_embedding_service,
            reset_vehicle_embedding_service,
        )

        # Reset singleton for test
        reset_vehicle_embedding_service()

        service1 = get_vehicle_embedding_service()
        service2 = get_vehicle_embedding_service()

        assert service1 is service2

    def test_reset_vehicle_embedding_service(self):
        """Test that reset creates new instance."""
        from app.services.vehicle_embedding_service import (
            get_vehicle_embedding_service,
            reset_vehicle_embedding_service,
        )

        service1 = get_vehicle_embedding_service()
        reset_vehicle_embedding_service()
        service2 = get_vehicle_embedding_service()

        assert service1 is not service2
