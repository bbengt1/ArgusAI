"""add_missing_database_indexes

Revision ID: 058
Revises: 057
Create Date: 2025-12-29 11:00:00.000000

Story P14-2.3: Add Missing Database Indexes
- Adds indexes for frequently queried columns to improve query performance
- Events: compound index on (source_type, timestamp) for Protect queries
- RecognizedEntities: index on name for LIKE queries
- Devices: index on pairing_confirmed for filtering
- APIKeys: indexes on created_by, revoked_by for audit queries
- PairingCodes: compound index on (device_id, expires_at) for cleanup
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '058'
down_revision = '057'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes to frequently queried columns."""
    # Events: compound index for source_type filtering with time range
    # Optimizes queries like: WHERE source_type = 'protect' ORDER BY timestamp DESC
    op.create_index(
        'idx_events_source_type_timestamp',
        'events',
        ['source_type', 'timestamp']
    )

    # RecognizedEntities: name index for LIKE queries in alert rules
    # Optimizes queries like: WHERE name LIKE 'John%'
    op.create_index(
        'idx_recognized_entities_name',
        'recognized_entities',
        ['name']
    )

    # Devices: pairing_confirmed for filtering active devices
    # Optimizes queries like: WHERE pairing_confirmed = true
    op.create_index(
        'idx_devices_pairing_confirmed',
        'devices',
        ['pairing_confirmed']
    )

    # APIKeys: audit indexes for tracking key creation and revocation
    # Optimizes queries like: WHERE created_by = 'user-id' or revoked_by = 'user-id'
    op.create_index(
        'idx_api_keys_created_by',
        'api_keys',
        ['created_by']
    )
    op.create_index(
        'idx_api_keys_revoked_by',
        'api_keys',
        ['revoked_by']
    )

    # PairingCodes: compound index for cleanup queries
    # Optimizes queries like: WHERE device_id = 'x' AND expires_at < NOW()
    op.create_index(
        'idx_pairing_codes_device_expires',
        'pairing_codes',
        ['device_id', 'expires_at']
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_pairing_codes_device_expires', 'pairing_codes')
    op.drop_index('idx_api_keys_revoked_by', 'api_keys')
    op.drop_index('idx_api_keys_created_by', 'api_keys')
    op.drop_index('idx_devices_pairing_confirmed', 'devices')
    op.drop_index('idx_recognized_entities_name', 'recognized_entities')
    op.drop_index('idx_events_source_type_timestamp', 'events')
