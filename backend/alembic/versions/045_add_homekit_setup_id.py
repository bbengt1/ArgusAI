"""Add setup_id to homekit_config for HomeKit Setup URI (P5-1.2)

Revision ID: 045_add_homekit_setup_id
Revises: 044_add_homekit_models
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '045_add_homekit_setup_id'
down_revision = '044_add_homekit_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add setup_id column to homekit_config table."""
    op.add_column(
        'homekit_config',
        sa.Column('setup_id', sa.String(4), nullable=True)
    )


def downgrade() -> None:
    """Remove setup_id column from homekit_config table."""
    op.drop_column('homekit_config', 'setup_id')
