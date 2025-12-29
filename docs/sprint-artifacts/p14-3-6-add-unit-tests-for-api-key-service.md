# Story P14-3.6: Add Unit Tests for api_key_service.py

Status: done

## Story

As a **developer**,
I want comprehensive unit tests for the APIKeyService,
so that key generation, validation, revocation, and security-critical authentication logic are regression-tested.

## Acceptance Criteria

1. **AC-1**: Test file `tests/test_services/test_api_key_service.py` exists with 10+ tests
2. **AC-2**: Line coverage for `api_key_service.py` reaches minimum 80% (security-critical)
3. **AC-3**: Key generation tested (format, uniqueness, prefix extraction)
4. **AC-4**: Key hashing and validation tested (bcrypt hash validates against plaintext)
5. **AC-5**: Key expiration checking tested (expired keys return None)
6. **AC-6**: Key revocation tested (revoked keys fail authentication)
7. **AC-7**: Prefix-based lookup tested (correct prefix matches key)
8. **AC-8**: `list_keys()` tested (with/without revoked keys)
9. **AC-9**: `get_key()` tested (found and not found cases)
10. **AC-10**: `record_usage()` tested (updates usage count, timestamp, IP)
11. **AC-11**: Invalid scope validation tested (raises ValueError)
12. **AC-12**: All tests use mocked database sessions

## Tasks / Subtasks

- [ ] Task 1: Set up test file structure (AC: 1, 12)
  - [ ] 1.1: Create `backend/tests/test_services/test_api_key_service.py`
  - [ ] 1.2: Add pytest imports and test class structure
  - [ ] 1.3: Create mock database session fixture
  - [ ] 1.4: Create APIKey model fixture factory

- [ ] Task 2: Implement generate_api_key() tests (AC: 3, 4, 11)
  - [ ] 2.1: `test_generate_key_format` - Key starts with "argus_" and has 38 total chars
  - [ ] 2.2: `test_generate_key_uniqueness` - Multiple keys are unique
  - [ ] 2.3: `test_generate_key_prefix_extraction` - Prefix is first 8 chars of random part
  - [ ] 2.4: `test_generate_key_bcrypt_hash` - Key hash validates against plaintext
  - [ ] 2.5: `test_generate_key_stores_in_db` - APIKey model added and committed
  - [ ] 2.6: `test_generate_key_invalid_scopes` - ValueError for invalid scopes
  - [ ] 2.7: `test_generate_key_valid_scopes` - All valid scopes accepted
  - [ ] 2.8: `test_generate_key_with_expiration` - expires_at stored correctly
  - [ ] 2.9: `test_generate_key_with_rate_limit` - rate_limit_per_minute stored

- [ ] Task 3: Implement verify_key() tests (AC: 4, 5, 6, 7)
  - [ ] 3.1: `test_verify_key_success` - Valid key returns APIKey model
  - [ ] 3.2: `test_verify_key_wrong_prefix_format` - Keys not starting with "argus_" return None
  - [ ] 3.3: `test_verify_key_short_key` - Keys with < 8 random chars return None
  - [ ] 3.4: `test_verify_key_no_matching_prefix` - Non-existent prefix returns None
  - [ ] 3.5: `test_verify_key_hash_mismatch` - Wrong key with same prefix returns None
  - [ ] 3.6: `test_verify_key_expired` - Expired key returns None
  - [ ] 3.7: `test_verify_key_revoked` - Revoked (inactive) key returns None
  - [ ] 3.8: `test_verify_key_bcrypt_error_handled` - Malformed hash doesn't crash

- [ ] Task 4: Implement list_keys() tests (AC: 8)
  - [ ] 4.1: `test_list_keys_empty` - Returns empty list when no keys
  - [ ] 4.2: `test_list_keys_returns_active_only` - Default excludes revoked
  - [ ] 4.3: `test_list_keys_include_revoked` - include_revoked=True returns all
  - [ ] 4.4: `test_list_keys_ordered_by_created_at` - Most recent first

- [ ] Task 5: Implement get_key() tests (AC: 9)
  - [ ] 5.1: `test_get_key_found` - Returns APIKey when exists
  - [ ] 5.2: `test_get_key_not_found` - Returns None for non-existent ID

- [ ] Task 6: Implement revoke_key() tests (AC: 6)
  - [ ] 6.1: `test_revoke_key_success` - Sets is_active=False, revoked_at, revoked_by
  - [ ] 6.2: `test_revoke_key_not_found` - Returns None for non-existent ID
  - [ ] 6.3: `test_revoked_key_fails_verification` - Revoked key returns None on verify

- [ ] Task 7: Implement record_usage() tests (AC: 10)
  - [ ] 7.1: `test_record_usage_updates_timestamp` - last_used_at updated
  - [ ] 7.2: `test_record_usage_updates_ip` - last_used_ip stored
  - [ ] 7.3: `test_record_usage_increments_count` - usage_count incremented
  - [ ] 7.4: `test_record_usage_commits` - db.commit() called

- [ ] Task 8: Implement singleton tests
  - [ ] 8.1: `test_get_api_key_service_returns_singleton` - Same instance returned

- [ ] Task 9: Run coverage and verify (AC: 2)
  - [ ] 9.1: Run `pytest tests/test_services/test_api_key_service.py --cov=app/services/api_key_service --cov-report=term-missing`
  - [ ] 9.2: Verify 80%+ line coverage achieved
  - [ ] 9.3: Add any missing tests for uncovered lines

## Dev Notes

### Architecture and Patterns

The `APIKeyService` class (~263 lines) provides:
1. **Key Generation**: `generate_api_key()` creates secure random keys with bcrypt hashing
2. **Key Verification**: `verify_key()` validates keys via prefix lookup + bcrypt comparison
3. **Key Management**: `list_keys()`, `get_key()`, `revoke_key()` for CRUD operations
4. **Usage Tracking**: `record_usage()` updates usage statistics

### Key Format

```
argus_<32-random-chars>
      ^       ^
      |       |
      |       +-- Random URL-safe base64 (32 chars)
      +---------- Fixed prefix for identification

Prefix: First 8 chars of random part, stored for fast lookup
Hash: Full key hashed with bcrypt (12 rounds)
```

### Valid Scopes

From `app/schemas/api_key.py`:
```python
VALID_SCOPES = {"read:events", "read:cameras", "write:cameras", "admin"}
```

### Key Methods to Test

| Method | Lines | Purpose | Test Focus |
|--------|-------|---------|------------|
| `generate_api_key()` | 37-108 | Create new key with hash | Format, uniqueness, hash, scopes |
| `verify_key()` | 110-161 | Validate key against hash | Prefix lookup, bcrypt check, expiration |
| `list_keys()` | 163-183 | List all/active keys | Filtering, ordering |
| `get_key()` | 185-196 | Get key by ID | Found/not found |
| `revoke_key()` | 198-233 | Deactivate key | Status update, audit fields |
| `record_usage()` | 235-250 | Track API usage | Timestamp, IP, count |

### Mock Database Session Pattern

```python
@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.filter.return_value.first.return_value = None
    return session
```

### Testing bcrypt Hash Validation

```python
def test_generate_key_bcrypt_hash(api_key_service, mock_db_session):
    """Test that generated key validates against stored hash."""
    import bcrypt

    api_key, plaintext = api_key_service.generate_api_key(
        db=mock_db_session,
        name="Test Key",
        scopes=["read:events"]
    )

    # Verify the plaintext validates against the hash
    assert bcrypt.checkpw(
        plaintext.encode('utf-8'),
        api_key.key_hash.encode('utf-8')
    )
```

### Testing Expiration

```python
from freezegun import freeze_time

@freeze_time("2025-01-01 12:00:00")
def test_verify_key_expired(api_key_service, mock_db_session, mock_api_key):
    """Test that expired key returns None."""
    # Set expiration in the past
    mock_api_key.expires_at = datetime(2024, 12, 31, tzinfo=timezone.utc)
    mock_api_key.is_expired.return_value = True

    result = api_key_service.verify_key(mock_db_session, "argus_test1234...")
    assert result is None
```

### Learnings from Previous Story

**From Story P14-3.5 (websocket_manager.py tests):**

- Used fresh service instance per test to avoid singleton state leakage
- Organized tests into logical test classes by functionality
- Used parametrization for scope validation tests
- Mocked external dependencies (database session)
- Achieved 100% coverage by testing all code paths

### Project Structure Notes

- Test file goes in: `backend/tests/test_services/test_api_key_service.py`
- Follows existing pattern from `test_websocket_manager.py` and `test_reprocessing_service.py`
- Create fresh APIKeyService instance per test (don't use global singleton)
- Use freezegun for time-dependent expiration tests

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P14-3.md#Story-P14-3.6]
- [Source: docs/epics-phase14.md#Story-P14-3.6]
- [Source: backend/app/services/api_key_service.py] - Target service (263 lines)
- [Source: backend/app/models/api_key.py] - APIKey model
- [Source: backend/app/schemas/api_key.py] - VALID_SCOPES definition
- [Source: docs/sprint-artifacts/p14-3-5-add-unit-tests-for-websocket-manager.md] - Previous story patterns

## Dev Agent Record

### Context Reference

N/A - YOLO mode execution

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - All tests passed on first run

### Completion Notes List

- Created 49 comprehensive unit tests for APIKeyService
- Achieved 100% line coverage (target was 80%)
- Tests organized into logical classes: Singleton, GenerateAPIKey, VerifyKey, ListKeys, GetKey, RevokeKey, RecordUsage, EdgeCases, IntegrationScenarios
- All acceptance criteria met or exceeded
- Used parametrization for scope validation tests (7 parametrized cases)
- No external dependencies needed - uses pytest and unittest.mock
- Tested security-critical paths: bcrypt hashing, key expiration, key revocation

### File List

- **NEW**: `backend/tests/test_services/test_api_key_service.py` (550 lines, 49 tests)
- **MODIFIED**: `docs/sprint-artifacts/sprint-status.yaml` (status updated to done)
- **MODIFIED**: `docs/sprint-artifacts/p14-3-6-add-unit-tests-for-api-key-service.md` (status updated)
