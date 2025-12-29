# Story P14-2.3: Add Missing Database Indexes

Status: done

## Story

As a performance engineer,
I want frequently queried columns to have indexes,
so that query performance is optimized for common access patterns.

## Acceptance Criteria

1. **AC-1**: Events table has compound index on `(source_type, timestamp)` for Protect queries
2. **AC-2**: RecognizedEntities has index on `name` for LIKE queries in alert rules
3. **AC-3**: Devices has index on `pairing_confirmed` for filtering inactive devices
4. **AC-4**: APIKeys has indexes on `created_by` and `revoked_by` columns
5. **AC-5**: PairingCodes has compound index on `(device_id, expires_at)` for cleanup queries
6. **AC-6**: Migration is reversible with proper `op.drop_index()` in downgrade

## Tasks / Subtasks

- [ ] Task 1: Create Alembic migration (AC: 1-6)
  - [ ] 1.1: Add compound index on events (source_type, timestamp)
  - [ ] 1.2: Add index on recognized_entities.name
  - [ ] 1.3: Add index on devices.pairing_confirmed
  - [ ] 1.4: Add indexes on api_keys (created_by, revoked_by)
  - [ ] 1.5: Add compound index on pairing_codes (device_id, expires_at)
  - [ ] 1.6: Implement downgrade to drop all indexes

- [ ] Task 2: Update model files with index definitions (for schema consistency)
  - [ ] 2.1: Update Event model __table_args__
  - [ ] 2.2: Update RecognizedEntity model __table_args__
  - [ ] 2.3: Update Device model __table_args__
  - [ ] 2.4: Update APIKey model __table_args__
  - [ ] 2.5: Update PairingCode model __table_args__

- [ ] Task 3: Run tests and verify functionality (AC: 6)
  - [ ] 3.1: Run `alembic upgrade head` to apply migration
  - [ ] 3.2: Run full test suite `pytest tests/ -v`

## Dev Notes

### Analysis of Current Indexes

**Events table:**
- Has: timestamp, camera_id, camera_timestamp compound, timestamp_desc
- Missing: source_type (for filtering Protect vs RTSP events)

**RecognizedEntities table:**
- Has: last_seen_at, entity_type, vehicle_signature
- Missing: name (for LIKE queries in alert rules)

**Devices table:**
- Has: user_id, device_id, platform, last_seen_at
- Missing: pairing_confirmed (for filtering active devices)

**APIKeys table:**
- Has: prefix
- Missing: created_by, revoked_by (for audit queries)

**PairingCodes table:**
- Has: code, expires_at, device_id (separate)
- Missing: Compound (device_id, expires_at) for cleanup queries

### Migration Script Pattern

```python
def upgrade():
    # Events: compound index for source_type filtering with time range
    op.create_index('idx_events_source_type_timestamp', 'events',
                    ['source_type', 'timestamp'])

    # RecognizedEntities: name index for LIKE queries
    op.create_index('idx_recognized_entities_name', 'recognized_entities', ['name'])

    # Devices: pairing_confirmed for filtering
    op.create_index('idx_devices_pairing_confirmed', 'devices', ['pairing_confirmed'])

    # APIKeys: audit indexes
    op.create_index('idx_api_keys_created_by', 'api_keys', ['created_by'])
    op.create_index('idx_api_keys_revoked_by', 'api_keys', ['revoked_by'])

    # PairingCodes: compound index for cleanup queries
    op.create_index('idx_pairing_codes_device_expires', 'pairing_codes',
                    ['device_id', 'expires_at'])

def downgrade():
    op.drop_index('idx_pairing_codes_device_expires', 'pairing_codes')
    op.drop_index('idx_api_keys_revoked_by', 'api_keys')
    op.drop_index('idx_api_keys_created_by', 'api_keys')
    op.drop_index('idx_devices_pairing_confirmed', 'devices')
    op.drop_index('idx_recognized_entities_name', 'recognized_entities')
    op.drop_index('idx_events_source_type_timestamp', 'events')
```

### Project Structure Notes

- Migration location: `backend/alembic/versions/`
- Models: `backend/app/models/`

### Testing Standards

From project architecture:
- Backend uses pytest with fixtures
- Run: `cd backend && pytest tests/ -v`
- Coverage: `pytest tests/ --cov=app --cov-report=html`

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P14-2.md#Story-P14-2.3]
- [Source: docs/epics-phase14.md#Story-P14-2.3]

## Dev Agent Record

### Context Reference

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

- Created migration 058 to add 6 indexes for frequently queried columns
- Events: compound index (source_type, timestamp) for Protect event filtering
- RecognizedEntities: name index for LIKE queries in alert rules
- Devices: pairing_confirmed index for filtering active devices
- APIKeys: created_by and revoked_by indexes for audit queries
- PairingCodes: compound index (device_id, expires_at) for cleanup queries
- Updated model files to include indexes in __table_args__ for schema consistency
- All 76 model tests pass

### File List

**Modified:**
- backend/app/models/event.py (added idx_events_source_type_timestamp)
- backend/app/models/recognized_entity.py (added idx_recognized_entities_name)
- backend/app/models/device.py (added idx_devices_pairing_confirmed)
- backend/app/models/api_key.py (added idx_api_keys_created_by, idx_api_keys_revoked_by)
- backend/app/models/pairing_code.py (added idx_pairing_codes_device_expires)

**Added:**
- backend/alembic/versions/058_add_missing_database_indexes.py

