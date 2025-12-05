"""add_fallback_reason_to_events

Revision ID: f7f1243134d4
Revises: 016_retry_flag
Create Date: 2025-12-05 16:16:03.090399

Story P3-1.4: Add fallback_reason column to track when clip download fails
and event falls back to snapshot-only analysis.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7f1243134d4'
down_revision = '016_retry_flag'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story P3-1.4: Add fallback_reason to events table
    op.add_column('events', sa.Column('fallback_reason', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('events', 'fallback_reason')
