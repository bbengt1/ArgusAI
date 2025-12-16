"""
API Tests for Push Notification endpoints (Stories P4-1.1 & P4-1.2)

Tests cover:
- GET /api/v1/push/vapid-public-key
- POST /api/v1/push/subscribe
- DELETE /api/v1/push/subscribe
- GET /api/v1/push/subscriptions
- POST /api/v1/push/test
"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import models and setup after database is configured
from main import app
from app.core.database import Base, get_db
from app.models.push_subscription import PushSubscription


# Create module-level temp database
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_test_db_fd)

TEST_DATABASE_URL = f"sqlite:///{_test_db_path}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_module_database():
    """Set up database at module level and clean up after all tests"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Apply override for all tests in this module
    app.dependency_overrides[get_db] = _override_get_db
    yield
    # Drop tables after all tests in module complete
    Base.metadata.drop_all(bind=engine)


# Create test client (module-level)
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def cleanup_push_subscriptions(db_session):
    """Clean up push subscriptions before each test."""
    db_session.query(PushSubscription).delete()
    db_session.commit()
    yield
    # Also clean up after test
    db = TestingSessionLocal()
    try:
        db.query(PushSubscription).delete()
        db.commit()
    finally:
        db.close()


class TestVapidPublicKeyEndpoint:
    """Tests for GET /api/v1/push/vapid-public-key."""

    def test_get_vapid_public_key_success(self):
        """Successfully get VAPID public key."""
        response = client.get("/api/v1/push/vapid-public-key")

        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 0

    def test_get_vapid_public_key_consistent(self):
        """Same key returned on multiple requests."""
        response1 = client.get("/api/v1/push/vapid-public-key")
        response2 = client.get("/api/v1/push/vapid-public-key")

        assert response1.json()["public_key"] == response2.json()["public_key"]


class TestSubscribeEndpoint:
    """Tests for POST /api/v1/push/subscribe."""

    @pytest.fixture
    def valid_subscription_data(self):
        """Valid subscription request data."""
        return {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test_subscription_123",
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_test_key",
                "auth": "tBHItJI5svbpez7KI4CCXg=="
            },
            "user_agent": "Mozilla/5.0 Test Browser"
        }

    def test_subscribe_creates_subscription(self, db_session, valid_subscription_data):
        """POST creates new subscription."""
        response = client.post("/api/v1/push/subscribe", json=valid_subscription_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "endpoint" in data
        assert "created_at" in data

        # Verify in database - use fresh session to see committed data
        with TestingSessionLocal() as check_db:
            subscription = check_db.query(PushSubscription).filter(
                PushSubscription.id == data["id"]
            ).first()
            assert subscription is not None
            assert subscription.p256dh_key == valid_subscription_data["keys"]["p256dh"]
            assert subscription.auth_key == valid_subscription_data["keys"]["auth"]

    def test_subscribe_updates_existing(self, valid_subscription_data):
        """POST updates existing subscription with same endpoint."""
        # Create initial subscription
        response1 = client.post("/api/v1/push/subscribe", json=valid_subscription_data)
        assert response1.status_code == 201
        original_id = response1.json()["id"]

        # Update with same endpoint, different keys
        updated_data = valid_subscription_data.copy()
        updated_data["keys"] = {
            "p256dh": "updated_p256dh_key",
            "auth": "updated_auth_key"
        }
        response2 = client.post("/api/v1/push/subscribe", json=updated_data)

        # Should succeed (upsert)
        assert response2.status_code == 201
        assert response2.json()["id"] == original_id

        # Verify keys updated
        with TestingSessionLocal() as check_db:
            subscription = check_db.query(PushSubscription).filter(
                PushSubscription.id == original_id
            ).first()
            assert subscription.p256dh_key == "updated_p256dh_key"

    def test_subscribe_invalid_endpoint_format(self):
        """POST rejects invalid endpoint URL."""
        invalid_data = {
            "endpoint": "not-a-valid-url",
            "keys": {
                "p256dh": "test",
                "auth": "test"
            }
        }

        response = client.post("/api/v1/push/subscribe", json=invalid_data)

        assert response.status_code == 400
        assert "endpoint" in response.json()["detail"].lower()

    def test_subscribe_missing_keys(self):
        """POST rejects missing keys."""
        invalid_data = {
            "endpoint": "https://example.com/push"
            # Missing keys
        }

        response = client.post("/api/v1/push/subscribe", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_subscribe_truncates_endpoint_in_response(self):
        """Response truncates long endpoint."""
        long_endpoint = "https://fcm.googleapis.com/" + "x" * 100
        data = {
            "endpoint": long_endpoint,
            "keys": {
                "p256dh": "test",
                "auth": "test"
            }
        }

        response = client.post("/api/v1/push/subscribe", json=data)

        assert response.status_code == 201
        # Response endpoint should be truncated
        assert len(response.json()["endpoint"]) < len(long_endpoint)


class TestUnsubscribeEndpoint:
    """Tests for DELETE /api/v1/push/subscribe."""

    def test_unsubscribe_removes_subscription(self, db_session):
        """DELETE removes subscription by endpoint."""
        # Create subscription first
        subscription = PushSubscription(
            endpoint="https://example.com/push/to_delete",
            p256dh_key="test",
            auth_key="test"
        )
        db_session.add(subscription)
        db_session.commit()

        response = client.request(
            "DELETE",
            "/api/v1/push/subscribe",
            json={"endpoint": "https://example.com/push/to_delete"}
        )

        assert response.status_code == 204

        # Verify deleted
        with TestingSessionLocal() as check_db:
            deleted = check_db.query(PushSubscription).filter(
                PushSubscription.endpoint == "https://example.com/push/to_delete"
            ).first()
            assert deleted is None

    def test_unsubscribe_not_found(self):
        """DELETE returns 404 for non-existent subscription."""
        response = client.request(
            "DELETE",
            "/api/v1/push/subscribe",
            json={"endpoint": "https://example.com/non_existent"}
        )

        assert response.status_code == 404


class TestListSubscriptionsEndpoint:
    """Tests for GET /api/v1/push/subscriptions."""

    def test_list_subscriptions_empty(self):
        """GET returns empty list when no subscriptions."""
        response = client.get("/api/v1/push/subscriptions")

        assert response.status_code == 200
        data = response.json()
        assert data["subscriptions"] == []
        assert data["total"] == 0

    def test_list_subscriptions_returns_all(self, db_session):
        """GET returns all subscriptions."""
        # Create multiple subscriptions
        for i in range(3):
            sub = PushSubscription(
                endpoint=f"https://example.com/push/{i}",
                p256dh_key=f"key_{i}",
                auth_key=f"auth_{i}"
            )
            db_session.add(sub)
        db_session.commit()

        response = client.get("/api/v1/push/subscriptions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["subscriptions"]) == 3

    def test_list_subscriptions_truncates_endpoints(self, db_session):
        """GET truncates endpoints in response."""
        long_endpoint = "https://fcm.googleapis.com/" + "x" * 100
        sub = PushSubscription(
            endpoint=long_endpoint,
            p256dh_key="test",
            auth_key="test"
        )
        db_session.add(sub)
        db_session.commit()

        response = client.get("/api/v1/push/subscriptions")

        assert response.status_code == 200
        endpoint_in_response = response.json()["subscriptions"][0]["endpoint"]
        assert len(endpoint_in_response) < len(long_endpoint)


class TestTestNotificationEndpoint:
    """Tests for POST /api/v1/push/test (Story P4-1.2)."""

    def test_send_test_no_subscriptions(self):
        """POST returns message when no subscriptions exist."""
        response = client.post("/api/v1/push/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "No push subscriptions" in data["message"]
        assert data["results"] == []

    def test_send_test_with_subscriptions(self, db_session):
        """POST sends to all subscriptions and returns results."""
        # Create test subscriptions
        for i in range(2):
            sub = PushSubscription(
                endpoint=f"https://fcm.googleapis.com/fcm/send/test_{i}",
                p256dh_key=f"test_p256dh_{i}",
                auth_key=f"test_auth_{i}"
            )
            db_session.add(sub)
        db_session.commit()

        # Mock the PushNotificationService to avoid actual push sending
        with patch('app.api.v1.push.PushNotificationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            # Create mock notification results
            from app.services.push_notification_service import NotificationResult
            mock_results = [
                NotificationResult(subscription_id="sub1", success=True),
                NotificationResult(subscription_id="sub2", success=True),
            ]
            # Use AsyncMock for async method
            mock_service.broadcast_notification = AsyncMock(return_value=mock_results)

            response = client.post("/api/v1/push/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2/2" in data["message"]
        assert len(data["results"]) == 2

    def test_send_test_partial_success(self, db_session):
        """POST reports partial success when some notifications fail."""
        # Create test subscription
        sub = PushSubscription(
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            p256dh_key="test_p256dh",
            auth_key="test_auth"
        )
        db_session.add(sub)
        db_session.commit()

        # Mock the service with partial failure
        with patch('app.api.v1.push.PushNotificationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            from app.services.push_notification_service import NotificationResult
            mock_results = [
                NotificationResult(subscription_id="sub1", success=True),
                NotificationResult(subscription_id="sub2", success=False, error="expired"),
            ]
            # Use AsyncMock for async method
            mock_service.broadcast_notification = AsyncMock(return_value=mock_results)

            response = client.post("/api/v1/push/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True  # At least one succeeded
        assert "1/2" in data["message"]
        # Check error is included for failed subscription
        failed = [r for r in data["results"] if not r["success"]]
        assert len(failed) == 1
        assert failed[0]["error"] == "expired"

    def test_send_test_response_structure(self, db_session):
        """POST returns correct response structure."""
        # Create test subscription
        sub = PushSubscription(
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            p256dh_key="test_p256dh",
            auth_key="test_auth"
        )
        db_session.add(sub)
        db_session.commit()

        with patch('app.api.v1.push.PushNotificationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            from app.services.push_notification_service import NotificationResult
            mock_results = [
                NotificationResult(subscription_id="test-uuid", success=True),
            ]
            # Use AsyncMock for async method
            mock_service.broadcast_notification = AsyncMock(return_value=mock_results)

            response = client.post("/api/v1/push/test")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "success" in data
        assert "message" in data
        assert "results" in data
        assert isinstance(data["results"], list)

        if data["results"]:
            result = data["results"][0]
            assert "subscription_id" in result
            assert "success" in result


# ============================================================================
# Story P4-1.4: Notification Preferences API Tests
# ============================================================================


class TestGetPreferencesEndpoint:
    """Tests for POST /api/v1/push/preferences (get preferences) (Story P4-1.4)."""

    def test_get_preferences_for_new_subscription(self, db_session):
        """Returns default preferences for subscription that just subscribed."""
        # Create subscription which should auto-create preferences
        response = client.post("/api/v1/push/subscribe", json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/prefs_test_1",
            "keys": {
                "p256dh": "test_key_1",
                "auth": "test_auth_1"
            }
        })
        assert response.status_code == 201

        # Get preferences
        response = client.post("/api/v1/push/preferences", json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/prefs_test_1"
        })

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "subscription_id" in data
        # Default values
        assert data["enabled_cameras"] is None  # All cameras
        assert data["enabled_object_types"] is None  # All types
        assert data["quiet_hours_enabled"] is False
        assert data["sound_enabled"] is True
        assert data["timezone"] == "UTC"

    def test_get_preferences_not_found(self):
        """Returns 404 for non-existent subscription."""
        response = client.post("/api/v1/push/preferences", json={
            "endpoint": "https://example.com/non_existent"
        })

        assert response.status_code == 404

    def test_get_preferences_validates_endpoint(self):
        """Returns 400 or 404 for invalid endpoint format."""
        response = client.post("/api/v1/push/preferences", json={
            "endpoint": "not-a-valid-url"
        })

        # Invalid endpoint is caught either by validation (400) or not found (404)
        assert response.status_code in [400, 404]


class TestUpdatePreferencesEndpoint:
    """Tests for PUT /api/v1/push/preferences (update preferences) (Story P4-1.4)."""

    @pytest.fixture
    def subscription_with_preferences(self, db_session):
        """Create a subscription with default preferences."""
        from app.models.notification_preference import NotificationPreference

        # Create subscription
        response = client.post("/api/v1/push/subscribe", json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/update_prefs_test",
            "keys": {
                "p256dh": "test_key",
                "auth": "test_auth"
            }
        })
        assert response.status_code == 201

        return "https://fcm.googleapis.com/fcm/send/update_prefs_test"

    def test_update_preferences_cameras(self, subscription_with_preferences):
        """Updates enabled_cameras successfully."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_cameras": ["camera-1", "camera-2"],
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["enabled_cameras"] == ["camera-1", "camera-2"]

    def test_update_preferences_object_types(self, subscription_with_preferences):
        """Updates enabled_object_types successfully."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_object_types": ["person", "vehicle"],
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["enabled_object_types"] == ["person", "vehicle"]

    def test_update_preferences_quiet_hours(self, subscription_with_preferences):
        """Updates quiet hours settings successfully."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "06:00",
            "timezone": "America/New_York",
            "sound_enabled": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["quiet_hours_enabled"] is True
        assert data["quiet_hours_start"] == "22:00"
        assert data["quiet_hours_end"] == "06:00"
        assert data["timezone"] == "America/New_York"

    def test_update_preferences_sound_toggle(self, subscription_with_preferences):
        """Updates sound_enabled successfully."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": False
        })

        assert response.status_code == 200
        data = response.json()
        assert data["sound_enabled"] is False

    def test_update_preferences_not_found(self):
        """Returns 404 for non-existent subscription."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": "https://example.com/non_existent",
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 404

    def test_update_preferences_invalid_object_type(self, subscription_with_preferences):
        """Returns 400 for invalid object type."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_object_types": ["person", "invalid_type"],
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 400
        assert "object type" in response.json()["detail"].lower()

    def test_update_preferences_invalid_time_format(self, subscription_with_preferences):
        """Returns 400 for invalid time format."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "25:00",  # Invalid hour
            "quiet_hours_end": "06:00",
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 400
        # Error message contains format info
        detail = response.json()["detail"].lower()
        assert "format" in detail or "hh:mm" in detail

    def test_update_preferences_invalid_timezone(self, subscription_with_preferences):
        """Returns 400 for invalid timezone."""
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "quiet_hours_enabled": False,
            "timezone": "Invalid/Timezone",
            "sound_enabled": True
        })

        assert response.status_code == 400
        assert "timezone" in response.json()["detail"].lower()

    def test_update_preferences_null_cameras_means_all(self, subscription_with_preferences):
        """Setting enabled_cameras to null enables all cameras."""
        # First set specific cameras
        client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_cameras": ["camera-1"],
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        # Then set to null (all)
        response = client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_cameras": None,
            "quiet_hours_enabled": False,
            "timezone": "UTC",
            "sound_enabled": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["enabled_cameras"] is None

    def test_update_preferences_persists_across_requests(self, subscription_with_preferences):
        """Updated preferences are persisted and returned on subsequent get."""
        # Update preferences
        client.put("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences,
            "enabled_cameras": ["my-camera"],
            "enabled_object_types": ["person"],
            "quiet_hours_enabled": True,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "07:00",
            "timezone": "America/Los_Angeles",
            "sound_enabled": False
        })

        # Get preferences
        response = client.post("/api/v1/push/preferences", json={
            "endpoint": subscription_with_preferences
        })

        assert response.status_code == 200
        data = response.json()
        assert data["enabled_cameras"] == ["my-camera"]
        assert data["enabled_object_types"] == ["person"]
        assert data["quiet_hours_enabled"] is True
        assert data["quiet_hours_start"] == "23:00"
        assert data["quiet_hours_end"] == "07:00"
        assert data["timezone"] == "America/Los_Angeles"
        assert data["sound_enabled"] is False
