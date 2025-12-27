"""Add entity_id and entity_match_mode to alert_rules (Story P12-1.1)

Revision ID: 053_add_entity_alert_rule_fields
Revises: 052_add_entity_adjustments_table
Create Date: 2025-12-26

Story P12-1.1: Add Entity Field to AlertRule Model

This migration adds simplified entity-based filtering to alert rules:
- entity_id: FK to recognized_entities for single entity selection
- entity_match_mode: 'any' (default), 'specific', or 'unknown' (stranger detection)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '053_add_entity_alert_rule_fields'
down_revision = '052_add_entity_adjustments_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add entity_id and entity_match_mode columns to alert_rules."""
    # Add entity_id column with FK to recognized_entities
    op.add_column(
        'alert_rules',
        sa.Column('entity_id', sa.String(36), nullable=True)
    )

    # Add entity_match_mode column with default 'any'
    op.add_column(
        'alert_rules',
        sa.Column(
            'entity_match_mode',
            sa.String(20),
            nullable=False,
            server_default='any'
        )
    )

    # Create foreign key constraint
    # Note: SQLite doesn't fully support FK constraints in ALTER TABLE,
    # but we add it for documentation and PostgreSQL compatibility
    try:
        op.create_foreign_key(
            'fk_alert_rules_entity_id',
            'alert_rules',
            'recognized_entities',
            ['entity_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # SQLite doesn't support adding FK constraints to existing tables
        pass

    # Create index on entity_id for efficient queries
    op.create_index(
        'idx_alert_rules_entity_id',
        'alert_rules',
        ['entity_id']
    )


def downgrade():
    """Remove entity_id and entity_match_mode columns from alert_rules."""
    # Drop index
    op.drop_index('idx_alert_rules_entity_id', 'alert_rules')

    # Drop foreign key constraint (may not exist in SQLite)
    try:
        op.drop_constraint('fk_alert_rules_entity_id', 'alert_rules', type_='foreignkey')
    except Exception:
        pass

    # Drop columns
    op.drop_column('alert_rules', 'entity_match_mode')
    op.drop_column('alert_rules', 'entity_id')
