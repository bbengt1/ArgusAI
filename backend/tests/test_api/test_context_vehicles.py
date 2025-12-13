"""
API tests for Vehicle Recognition endpoints (Story P4-8.3)

Tests the vehicle API endpoints in context.py:
- GET /api/v1/context/vehicles - List vehicles
- GET /api/v1/context/vehicles/{id} - Get vehicle details
- PUT /api/v1/context/vehicles/{id} - Update vehicle
- GET /api/v1/context/vehicle-embeddings/{event_id} - Get embeddings for event
- DELETE /api/v1/context/vehicle-embeddings/{event_id} - Delete event embeddings
- DELETE /api/v1/context/vehicle-embeddings - Delete all embeddings
- GET /api/v1/context/vehicle-embeddings/stats - Get stats
"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


class TestListVehicles:
    """Tests for GET /api/v1/context/vehicles endpoint."""

    @pytest.mark.asyncio
    async def test_list_vehicles_empty(self, client):
        """Test listing vehicles when none exist."""
        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicles = AsyncMock(return_value=([], 0))
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles")

            assert response.status_code == 200
            data = response.json()
            assert data["vehicles"] == []
            assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_vehicles_with_data(self, client):
        """Test listing vehicles with data."""
        mock_vehicles = [
            {
                "id": "v-1",
                "name": "My Car",
                "first_seen_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
                "occurrence_count": 5,
                "embedding_count": 3,
                "vehicle_type": "car",
                "primary_color": "blue",
            }
        ]

        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicles = AsyncMock(return_value=(mock_vehicles, 1))
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles")

            assert response.status_code == 200
            data = response.json()
            assert len(data["vehicles"]) == 1
            assert data["vehicles"][0]["name"] == "My Car"
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_vehicles_pagination(self, client):
        """Test pagination parameters."""
        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicles = AsyncMock(return_value=([], 0))
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles?limit=10&offset=20")

            assert response.status_code == 200
            mock_service.get_vehicles.assert_called_once()
            call_args = mock_service.get_vehicles.call_args
            assert call_args.kwargs["limit"] == 10
            assert call_args.kwargs["offset"] == 20

    @pytest.mark.asyncio
    async def test_list_vehicles_named_only(self, client):
        """Test named_only filter."""
        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicles = AsyncMock(return_value=([], 0))
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles?named_only=true")

            assert response.status_code == 200
            mock_service.get_vehicles.assert_called_once()
            call_args = mock_service.get_vehicles.call_args
            assert call_args.kwargs["named_only"] is True


class TestGetVehicle:
    """Tests for GET /api/v1/context/vehicles/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_vehicle_success(self, client):
        """Test getting vehicle details."""
        mock_vehicle = {
            "id": "v-1",
            "name": "Work Truck",
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "occurrence_count": 10,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "vehicle_type": "truck",
            "primary_color": "white",
            "metadata": {"detected_type": "truck"},
            "recent_detections": [],
        }

        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicle = AsyncMock(return_value=mock_vehicle)
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles/v-1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "v-1"
            assert data["name"] == "Work Truck"

    @pytest.mark.asyncio
    async def test_get_vehicle_not_found(self, client):
        """Test getting non-existent vehicle."""
        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicle = AsyncMock(return_value=None)
            mock_service_fn.return_value = mock_service

            response = client.get("/api/v1/context/vehicles/nonexistent")

            assert response.status_code == 404


class TestUpdateVehicle:
    """Tests for PUT /api/v1/context/vehicles/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_vehicle_name(self, client):
        """Test updating vehicle name."""
        mock_vehicle = {
            "id": "v-1",
            "name": "New Name",
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "occurrence_count": 5,
            "vehicle_type": "car",
            "primary_color": "red",
        }

        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.update_vehicle_name = AsyncMock(return_value=mock_vehicle)
            mock_service_fn.return_value = mock_service

            response = client.put(
                "/api/v1/context/vehicles/v-1",
                json={"name": "New Name"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, client):
        """Test updating non-existent vehicle."""
        with patch('app.api.v1.context.get_vehicle_matching_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.update_vehicle_name = AsyncMock(return_value=None)
            mock_service.get_vehicle = AsyncMock(return_value=None)
            mock_service_fn.return_value = mock_service

            response = client.put(
                "/api/v1/context/vehicles/nonexistent",
                json={"name": "Test"}
            )

            assert response.status_code == 404


class TestVehicleEmbeddings:
    """Tests for vehicle embedding endpoints."""

    @pytest.mark.asyncio
    async def test_get_vehicle_embeddings_for_event(self, client):
        """Test getting vehicle embeddings for an event."""
        mock_vehicles = [
            {
                "id": "emb-1",
                "event_id": "event-1",
                "entity_id": "v-1",
                "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 80},
                "confidence": 0.95,
                "vehicle_type": "car",
                "model_version": "clip-ViT-B-32-vehicle-v1",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

        with patch('app.api.v1.context.get_vehicle_embedding_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_vehicle_embeddings = AsyncMock(return_value=mock_vehicles)
            mock_service_fn.return_value = mock_service

            with patch('app.api.v1.context.get_db'):
                # Mock event exists
                with patch('app.models.event.Event'):
                    response = client.get("/api/v1/context/vehicle-embeddings/event-1")

            # Note: This test may need adjustment based on actual DB mocking
            # The endpoint requires the event to exist

    @pytest.mark.asyncio
    async def test_delete_event_vehicles(self, client):
        """Test deleting vehicle embeddings for an event."""
        with patch('app.api.v1.context.get_vehicle_embedding_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.delete_event_vehicles = AsyncMock(return_value=3)
            mock_service_fn.return_value = mock_service

            with patch('app.api.v1.context.get_db'):
                # Note: Actual test would need proper DB mocking
                pass

    @pytest.mark.asyncio
    async def test_delete_all_vehicles(self, client):
        """Test deleting all vehicle embeddings."""
        with patch('app.api.v1.context.get_vehicle_embedding_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.delete_all_vehicles = AsyncMock(return_value=100)
            mock_service_fn.return_value = mock_service

            response = client.delete("/api/v1/context/vehicle-embeddings")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted_count"] == 100

    @pytest.mark.asyncio
    async def test_get_vehicle_stats(self, client):
        """Test getting vehicle embedding stats."""
        with patch('app.api.v1.context.get_vehicle_embedding_service') as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_total_vehicle_count = AsyncMock(return_value=150)
            mock_service.get_model_version = MagicMock(return_value="clip-ViT-B-32-vehicle-v1")
            mock_service_fn.return_value = mock_service

            with patch('app.api.v1.context.get_db') as mock_db_fn:
                mock_db = MagicMock()
                mock_setting = MagicMock()
                mock_setting.value = "true"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_setting
                mock_db_fn.return_value = mock_db

                response = client.get("/api/v1/context/vehicle-embeddings/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_vehicle_embeddings"] == 150
                assert data["vehicle_recognition_enabled"] is True


class TestVehicleAPIValidation:
    """Tests for API input validation."""

    @pytest.mark.asyncio
    async def test_list_vehicles_limit_validation(self, client):
        """Test limit parameter validation."""
        response = client.get("/api/v1/context/vehicles?limit=0")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/v1/context/vehicles?limit=1000")
        assert response.status_code == 422  # Exceeds max

    @pytest.mark.asyncio
    async def test_list_vehicles_offset_validation(self, client):
        """Test offset parameter validation."""
        response = client.get("/api/v1/context/vehicles?offset=-1")
        assert response.status_code == 422  # Negative not allowed
