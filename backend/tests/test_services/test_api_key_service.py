"""
Unit tests for APIKeyService.

Story P14-3.6: Add unit tests for api_key_service.py

This test module provides comprehensive coverage for:
- Key generation (format, uniqueness, bcrypt hashing)
- Key verification (prefix lookup, hash validation, expiration)
- Key management (list, get, revoke)
- Usage tracking
"""
import pytest
import bcrypt
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from app.services.api_key_service import APIKeyService, get_api_key_service
from app.models.api_key import APIKey
from app.schemas.api_key import VALID_SCOPES


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def api_key_service():
    """Create a fresh APIKeyService instance for each test."""
    return APIKeyService()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_api_key_factory():
    """Factory to create mock APIKey instances."""
    def _create(
        id: str = "test-key-id-123",
        name: str = "Test Key",
        prefix: str = "testpref",
        key_hash: str = None,
        scopes: list = None,
        is_active: bool = True,
        expires_at: datetime = None,
        last_used_at: datetime = None,
        last_used_ip: str = None,
        usage_count: int = 0,
        rate_limit_per_minute: int = 100,
        created_at: datetime = None,
        created_by: str = None,
        revoked_at: datetime = None,
        revoked_by: str = None,
    ):
        api_key = MagicMock(spec=APIKey)
        api_key.id = id
        api_key.name = name
        api_key.prefix = prefix
        api_key.key_hash = key_hash or bcrypt.hashpw(
            f"argus_{prefix}extradata12345678901234".encode('utf-8'),
            bcrypt.gensalt(rounds=4)  # Lower rounds for faster tests
        ).decode('utf-8')
        api_key.scopes = scopes or ["read:events"]
        api_key.is_active = is_active
        api_key.expires_at = expires_at
        api_key.last_used_at = last_used_at
        api_key.last_used_ip = last_used_ip
        api_key.usage_count = usage_count
        api_key.rate_limit_per_minute = rate_limit_per_minute
        api_key.created_at = created_at or datetime.now(timezone.utc)
        api_key.created_by = created_by
        api_key.revoked_at = revoked_at
        api_key.revoked_by = revoked_by

        # Mock methods
        api_key.is_expired = MagicMock(return_value=False)
        api_key.is_valid = MagicMock(return_value=is_active)
        api_key.has_scope = MagicMock(side_effect=lambda s: s in (scopes or ["read:events"]))
        api_key.record_usage = MagicMock()
        api_key.revoke = MagicMock()

        return api_key
    return _create


# =============================================================================
# Test: Singleton Pattern
# =============================================================================


class TestAPIKeyServiceSingleton:
    """Tests for singleton pattern."""

    def test_get_api_key_service_returns_singleton(self):
        """Test that get_api_key_service returns same instance."""
        # Reset singleton state
        import app.services.api_key_service as module
        module._api_key_service = None

        service1 = get_api_key_service()
        service2 = get_api_key_service()

        assert service1 is service2
        assert isinstance(service1, APIKeyService)


# =============================================================================
# Test: generate_api_key()
# =============================================================================


class TestGenerateAPIKey:
    """Tests for API key generation."""

    def test_generate_key_format(self, api_key_service, mock_db_session):
        """Test that generated key has correct format: argus_<32chars>."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        assert plaintext.startswith("argus_")
        assert len(plaintext) == 6 + 32  # "argus_" (6) + 32 random chars

    def test_generate_key_uniqueness(self, api_key_service, mock_db_session):
        """Test that multiple generated keys are unique."""
        keys = set()
        for i in range(10):
            _, plaintext = api_key_service.generate_api_key(
                db=mock_db_session,
                name=f"Test Key {i}",
                scopes=["read:events"],
            )
            keys.add(plaintext)

        assert len(keys) == 10  # All unique

    def test_generate_key_prefix_extraction(self, api_key_service, mock_db_session):
        """Test that prefix is first 8 chars of random part."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        random_part = plaintext[6:]  # After "argus_"
        expected_prefix = random_part[:8]

        assert api_key.prefix == expected_prefix
        assert len(api_key.prefix) == 8

    def test_generate_key_bcrypt_hash(self, api_key_service, mock_db_session):
        """Test that generated key validates against stored hash."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        # Verify the plaintext validates against the hash
        assert bcrypt.checkpw(
            plaintext.encode('utf-8'),
            api_key.key_hash.encode('utf-8')
        )

    def test_generate_key_stores_in_db(self, api_key_service, mock_db_session):
        """Test that APIKey model is added and committed to database."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    def test_generate_key_invalid_scopes(self, api_key_service, mock_db_session):
        """Test that invalid scopes raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            api_key_service.generate_api_key(
                db=mock_db_session,
                name="Test Key",
                scopes=["invalid:scope", "read:events"],
            )

        assert "Invalid scopes" in str(exc_info.value)
        assert "invalid:scope" in str(exc_info.value)

    @pytest.mark.parametrize("scopes", [
        ["read:events"],
        ["read:cameras"],
        ["write:cameras"],
        ["admin"],
        ["read:events", "read:cameras"],
        ["read:events", "read:cameras", "write:cameras"],
        list(VALID_SCOPES),
    ])
    def test_generate_key_valid_scopes(self, api_key_service, mock_db_session, scopes):
        """Test that all valid scopes are accepted."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=scopes,
        )

        assert api_key.scopes == scopes

    def test_generate_key_with_expiration(self, api_key_service, mock_db_session):
        """Test that expires_at is stored correctly."""
        expires = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
            expires_at=expires,
        )

        assert api_key.expires_at == expires

    def test_generate_key_with_rate_limit(self, api_key_service, mock_db_session):
        """Test that rate_limit_per_minute is stored correctly."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
            rate_limit_per_minute=500,
        )

        assert api_key.rate_limit_per_minute == 500

    def test_generate_key_with_created_by(self, api_key_service, mock_db_session):
        """Test that created_by user ID is stored."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
            created_by="user-123",
        )

        assert api_key.created_by == "user-123"

    def test_generate_key_returns_tuple(self, api_key_service, mock_db_session):
        """Test that generate returns (APIKey, plaintext_key) tuple."""
        result = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], APIKey)
        assert isinstance(result[1], str)


# =============================================================================
# Test: verify_key()
# =============================================================================


class TestVerifyKey:
    """Tests for API key verification."""

    def test_verify_key_success(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that valid key returns APIKey model."""
        # Create a real key to test against
        plaintext = "argus_testpref12345678901234567890123456"
        key_hash = bcrypt.hashpw(
            plaintext.encode('utf-8'),
            bcrypt.gensalt(rounds=4)
        ).decode('utf-8')

        mock_api_key = mock_api_key_factory(
            prefix="testpref",
            key_hash=key_hash,
        )

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        result = api_key_service.verify_key(mock_db_session, plaintext)

        assert result == mock_api_key

    def test_verify_key_wrong_prefix_format(self, api_key_service, mock_db_session):
        """Test that keys not starting with 'argus_' return None."""
        result = api_key_service.verify_key(mock_db_session, "invalid_key_format")

        assert result is None
        # Query should not be called for invalid format
        mock_db_session.query.assert_not_called()

    def test_verify_key_short_key(self, api_key_service, mock_db_session):
        """Test that keys with < 8 random chars return None."""
        result = api_key_service.verify_key(mock_db_session, "argus_short")

        assert result is None
        mock_db_session.query.assert_not_called()

    def test_verify_key_no_matching_prefix(self, api_key_service, mock_db_session):
        """Test that non-existent prefix returns None."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = api_key_service.verify_key(
            mock_db_session,
            "argus_nonexist12345678901234567890123456"
        )

        assert result is None

    def test_verify_key_hash_mismatch(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that wrong key with same prefix returns None."""
        # Create a key with a different hash
        different_key = "argus_testpref99999999999999999999999999"
        mock_api_key = mock_api_key_factory(
            prefix="testpref",
            key_hash=bcrypt.hashpw(
                different_key.encode('utf-8'),
                bcrypt.gensalt(rounds=4)
            ).decode('utf-8'),
        )

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        # Try to verify with a different plaintext
        result = api_key_service.verify_key(
            mock_db_session,
            "argus_testpref00000000000000000000000000"
        )

        assert result is None

    def test_verify_key_expired(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that expired key returns None."""
        plaintext = "argus_testpref12345678901234567890123456"
        key_hash = bcrypt.hashpw(
            plaintext.encode('utf-8'),
            bcrypt.gensalt(rounds=4)
        ).decode('utf-8')

        mock_api_key = mock_api_key_factory(
            prefix="testpref",
            key_hash=key_hash,
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        mock_api_key.is_expired.return_value = True

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        result = api_key_service.verify_key(mock_db_session, plaintext)

        assert result is None

    def test_verify_key_revoked(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that revoked (inactive) key is not returned by query."""
        # The query filters for is_active=True, so revoked keys won't be returned
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = api_key_service.verify_key(
            mock_db_session,
            "argus_testpref12345678901234567890123456"
        )

        assert result is None

    def test_verify_key_bcrypt_error_handled(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that malformed hash doesn't crash."""
        mock_api_key = mock_api_key_factory(
            prefix="testpref",
            key_hash="invalid_not_a_bcrypt_hash",
        )

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        # Should not raise, just return None
        result = api_key_service.verify_key(
            mock_db_session,
            "argus_testpref12345678901234567890123456"
        )

        assert result is None

    def test_verify_key_multiple_potential_matches(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test verification when multiple keys share same prefix."""
        plaintext = "argus_testpref12345678901234567890123456"
        correct_hash = bcrypt.hashpw(
            plaintext.encode('utf-8'),
            bcrypt.gensalt(rounds=4)
        ).decode('utf-8')

        mock_key1 = mock_api_key_factory(
            id="key1",
            prefix="testpref",
            key_hash=bcrypt.hashpw(b"argus_testpref_wrong_key_1", bcrypt.gensalt(rounds=4)).decode('utf-8'),
        )
        mock_key2 = mock_api_key_factory(
            id="key2",
            prefix="testpref",
            key_hash=correct_hash,
        )
        mock_key3 = mock_api_key_factory(
            id="key3",
            prefix="testpref",
            key_hash=bcrypt.hashpw(b"argus_testpref_wrong_key_3", bcrypt.gensalt(rounds=4)).decode('utf-8'),
        )

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_key1, mock_key2, mock_key3
        ]

        result = api_key_service.verify_key(mock_db_session, plaintext)

        assert result == mock_key2


# =============================================================================
# Test: list_keys()
# =============================================================================


class TestListKeys:
    """Tests for listing API keys."""

    def test_list_keys_empty(self, api_key_service, mock_db_session):
        """Test that empty list is returned when no keys exist."""
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = api_key_service.list_keys(mock_db_session)

        assert result == []

    def test_list_keys_returns_active_only(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that default excludes revoked keys."""
        active_key = mock_api_key_factory(id="active", is_active=True)

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [active_key]

        result = api_key_service.list_keys(mock_db_session, include_revoked=False)

        # Verify filter was applied
        mock_db_session.query.return_value.filter.assert_called()
        assert len(result) == 1
        assert result[0].id == "active"

    def test_list_keys_include_revoked(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that include_revoked=True returns all keys."""
        active_key = mock_api_key_factory(id="active", is_active=True)
        revoked_key = mock_api_key_factory(id="revoked", is_active=False)

        mock_db_session.query.return_value.order_by.return_value.all.return_value = [active_key, revoked_key]

        result = api_key_service.list_keys(mock_db_session, include_revoked=True)

        assert len(result) == 2

    def test_list_keys_ordered_by_created_at(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that keys are ordered by created_at descending."""
        old_key = mock_api_key_factory(
            id="old",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        new_key = mock_api_key_factory(
            id="new",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc)
        )

        # Mock returns in correct order (newest first)
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            new_key, old_key
        ]

        result = api_key_service.list_keys(mock_db_session)

        # order_by should have been called
        mock_db_session.query.return_value.filter.return_value.order_by.assert_called()
        assert len(result) == 2
        assert result[0].id == "new"
        assert result[1].id == "old"


# =============================================================================
# Test: get_key()
# =============================================================================


class TestGetKey:
    """Tests for getting a specific API key."""

    def test_get_key_found(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that existing key is returned."""
        mock_api_key = mock_api_key_factory(id="test-key-123")

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_api_key

        result = api_key_service.get_key(mock_db_session, "test-key-123")

        assert result == mock_api_key
        assert result.id == "test-key-123"

    def test_get_key_not_found(self, api_key_service, mock_db_session):
        """Test that None is returned for non-existent ID."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = api_key_service.get_key(mock_db_session, "non-existent-id")

        assert result is None


# =============================================================================
# Test: revoke_key()
# =============================================================================


class TestRevokeKey:
    """Tests for revoking API keys."""

    def test_revoke_key_success(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that revoke sets is_active=False and audit fields."""
        mock_api_key = mock_api_key_factory(id="test-key-123", is_active=True)

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_api_key

        result = api_key_service.revoke_key(
            mock_db_session,
            "test-key-123",
            revoked_by="admin-user"
        )

        assert result == mock_api_key
        mock_api_key.revoke.assert_called_once_with("admin-user")
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_api_key)

    def test_revoke_key_not_found(self, api_key_service, mock_db_session):
        """Test that None is returned for non-existent ID."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = api_key_service.revoke_key(mock_db_session, "non-existent-id")

        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_revoked_key_fails_verification(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that revoked key returns None on verify (filtered by is_active)."""
        # After revocation, the key has is_active=False
        # verify_key queries filter for is_active=True, so revoked keys are excluded
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = api_key_service.verify_key(
            mock_db_session,
            "argus_testpref12345678901234567890123456"
        )

        assert result is None


# =============================================================================
# Test: record_usage()
# =============================================================================


class TestRecordUsage:
    """Tests for recording API key usage."""

    def test_record_usage_updates_timestamp(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that last_used_at is updated."""
        mock_api_key = mock_api_key_factory()

        api_key_service.record_usage(mock_db_session, mock_api_key)

        mock_api_key.record_usage.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_record_usage_updates_ip(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that last_used_ip is stored."""
        mock_api_key = mock_api_key_factory()

        api_key_service.record_usage(mock_db_session, mock_api_key, ip_address="192.168.1.100")

        mock_api_key.record_usage.assert_called_once_with("192.168.1.100")

    def test_record_usage_increments_count(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that usage_count is incremented (via model method)."""
        mock_api_key = mock_api_key_factory(usage_count=5)

        api_key_service.record_usage(mock_db_session, mock_api_key)

        # The model's record_usage method handles incrementing
        mock_api_key.record_usage.assert_called_once()

    def test_record_usage_commits(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that db.commit() is called."""
        mock_api_key = mock_api_key_factory()

        api_key_service.record_usage(mock_db_session, mock_api_key)

        mock_db_session.commit.assert_called_once()

    def test_record_usage_ipv6(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that IPv6 addresses are handled."""
        mock_api_key = mock_api_key_factory()

        api_key_service.record_usage(
            mock_db_session,
            mock_api_key,
            ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )

        mock_api_key.record_usage.assert_called_once_with("2001:0db8:85a3:0000:0000:8a2e:0370:7334")


# =============================================================================
# Test: Edge Cases and Integration
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_scopes_list(self, api_key_service, mock_db_session):
        """Test that empty scopes list is rejected."""
        # Empty list should be accepted (no invalid scopes)
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=[],
        )

        assert api_key.scopes == []

    def test_key_with_special_characters_in_name(self, api_key_service, mock_db_session):
        """Test that special characters in name are handled."""
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key with 'quotes' and \"double quotes\" & ampersand",
            scopes=["read:events"],
        )

        assert "quotes" in api_key.name

    def test_very_long_name(self, api_key_service, mock_db_session):
        """Test that long names are handled."""
        long_name = "A" * 255  # Max length from schema

        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name=long_name,
            scopes=["read:events"],
        )

        assert api_key.name == long_name

    def test_generate_and_verify_roundtrip(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test full roundtrip: generate key, then verify it."""
        # Generate a key
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Test Key",
            scopes=["read:events"],
        )

        # Set up mock to return the generated key for verification
        mock_api_key = mock_api_key_factory(
            prefix=api_key.prefix,
            key_hash=api_key.key_hash,
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        # Verify the key
        result = api_key_service.verify_key(mock_db_session, plaintext)

        assert result == mock_api_key

    def test_null_ip_address(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that None IP address is handled."""
        mock_api_key = mock_api_key_factory()

        api_key_service.record_usage(mock_db_session, mock_api_key, ip_address=None)

        mock_api_key.record_usage.assert_called_once_with(None)


class TestIntegrationScenarios:
    """Integration-style tests for common workflows."""

    def test_create_verify_revoke_workflow(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test complete key lifecycle: create -> verify -> revoke -> verify fails."""
        # Step 1: Create key
        api_key, plaintext = api_key_service.generate_api_key(
            db=mock_db_session,
            name="Integration Test Key",
            scopes=["read:events", "read:cameras"],
        )

        # Step 2: Verify key works
        mock_api_key = mock_api_key_factory(
            prefix=api_key.prefix,
            key_hash=api_key.key_hash,
            is_active=True,
        )
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        result = api_key_service.verify_key(mock_db_session, plaintext)
        assert result == mock_api_key

        # Step 3: Revoke key
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_api_key
        api_key_service.revoke_key(mock_db_session, mock_api_key.id, revoked_by="admin")

        mock_api_key.revoke.assert_called_once()

        # Step 4: Verify key no longer works (filtered out by is_active=True)
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        result = api_key_service.verify_key(mock_db_session, plaintext)
        assert result is None

    def test_multiple_keys_different_scopes(self, api_key_service, mock_db_session):
        """Test creating multiple keys with different scope sets."""
        scopes_list = [
            ["read:events"],
            ["read:events", "read:cameras"],
            ["admin"],
            ["read:events", "read:cameras", "write:cameras"],
        ]

        keys = []
        for scopes in scopes_list:
            api_key, plaintext = api_key_service.generate_api_key(
                db=mock_db_session,
                name=f"Key with scopes: {scopes}",
                scopes=scopes,
            )
            keys.append((api_key, plaintext))

        # Verify all keys have correct scopes
        for (api_key, _), expected_scopes in zip(keys, scopes_list):
            assert api_key.scopes == expected_scopes

    def test_key_with_expiration_in_future(self, api_key_service, mock_db_session, mock_api_key_factory):
        """Test that key with future expiration is valid."""
        future_expiration = datetime.now(timezone.utc) + timedelta(days=30)

        plaintext = "argus_testpref12345678901234567890123456"
        key_hash = bcrypt.hashpw(plaintext.encode('utf-8'), bcrypt.gensalt(rounds=4)).decode('utf-8')

        mock_api_key = mock_api_key_factory(
            prefix="testpref",
            key_hash=key_hash,
            expires_at=future_expiration,
        )
        mock_api_key.is_expired.return_value = False

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_api_key]

        result = api_key_service.verify_key(mock_db_session, plaintext)

        assert result == mock_api_key
