"""Add entity alert fields for Named Entity Alerts (Story P4-8.4)

Revision ID: 043_add_entity_alert_fields
Revises: 042_add_vehicle_embeddings
Create Date: 2025-12-13

Adds:
- is_vip, is_blocked to recognized_entities for VIP alerts and blocklist
- recognition_status, enriched_description, matched_entity_ids to events
- entity_ids, entity_names to alert_rules for entity-based rule matching
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '043_add_entity_alert_fields'
down_revision = '042_add_vehicle_embeddings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add entity alert fields to recognized_entities, events, and alert_rules."""

    # Add is_vip and is_blocked to recognized_entities
    op.add_column(
        'recognized_entities',
        sa.Column('is_vip', sa.Boolean(), nullable=False, server_default='0')
    )
    op.add_column(
        'recognized_entities',
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='0')
    )
    op.add_column(
        'recognized_entities',
        sa.Column('entity_metadata', sa.Text(), nullable=True)
    )

    # Create indexes for VIP and blocked entity queries
    op.create_index('idx_recognized_entities_is_vip', 'recognized_entities', ['is_vip'])
    op.create_index('idx_recognized_entities_is_blocked', 'recognized_entities', ['is_blocked'])

    # Add recognition status and enriched description to events
    op.add_column(
        'events',
        sa.Column('recognition_status', sa.String(20), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('enriched_description', sa.Text(), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('matched_entity_ids', sa.Text(), nullable=True)
    )

    # Create index for recognition status filtering
    op.create_index('idx_events_recognition_status', 'events', ['recognition_status'])

    # Add entity-based matching fields to alert_rules
    op.add_column(
        'alert_rules',
        sa.Column('entity_ids', sa.Text(), nullable=True)
    )
    op.add_column(
        'alert_rules',
        sa.Column('entity_names', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove entity alert fields."""

    # Remove alert_rules columns
    op.drop_column('alert_rules', 'entity_names')
    op.drop_column('alert_rules', 'entity_ids')

    # Remove events columns
    op.drop_index('idx_events_recognition_status', table_name='events')
    op.drop_column('events', 'matched_entity_ids')
    op.drop_column('events', 'enriched_description')
    op.drop_column('events', 'recognition_status')

    # Remove recognized_entities columns
    op.drop_index('idx_recognized_entities_is_blocked', table_name='recognized_entities')
    op.drop_index('idx_recognized_entities_is_vip', table_name='recognized_entities')
    op.drop_column('recognized_entities', 'entity_metadata')
    op.drop_column('recognized_entities', 'is_blocked')
    op.drop_column('recognized_entities', 'is_vip')
