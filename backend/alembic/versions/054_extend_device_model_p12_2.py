"""extend_device_model_p12_2

Revision ID: 054
Revises: 053_add_entity_alert_rule_fields
Create Date: 2025-12-26 14:00:00.000000

Story P12-2.1: Extend Device model with mobile registration fields
- Add device_model column for device hardware info
- Add pairing_confirmed column for pairing flow status
- Add updated_at column for tracking updates
- Add index on last_seen_at for inactive device queries
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '054'
down_revision = '053_add_entity_alert_rule_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add P12-2.1 device model extensions."""
    # Add device_model column
    op.add_column('devices', sa.Column('device_model', sa.String(100), nullable=True))

    # Add pairing_confirmed column with default false
    op.add_column('devices', sa.Column('pairing_confirmed', sa.Boolean(), nullable=False, server_default='0'))

    # Add updated_at column
    op.add_column('devices', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # Add index on last_seen_at for inactive device queries
    op.create_index('idx_devices_last_seen', 'devices', ['last_seen_at'])


def downgrade() -> None:
    """Remove P12-2.1 device model extensions."""
    op.drop_index('idx_devices_last_seen', 'devices')
    op.drop_column('devices', 'updated_at')
    op.drop_column('devices', 'pairing_confirmed')
    op.drop_column('devices', 'device_model')
