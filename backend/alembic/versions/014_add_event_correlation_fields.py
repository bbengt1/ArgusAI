"""Add correlation fields to events table

Story P2-4.3: Multi-camera event correlation service

Adds:
- correlation_group_id: UUID linking correlated events across cameras
- correlated_event_ids: JSON array of related event UUIDs
- Index on correlation_group_id for efficient group lookups

Revision ID: 014
Revises: fba075111b91
Create Date: 2025-12-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014_correlation'
down_revision = 'fba075111b91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add correlation columns to events table."""
    # Add correlation_group_id column with index
    op.add_column(
        'events',
        sa.Column('correlation_group_id', sa.String(), nullable=True)
    )
    op.create_index(
        'idx_events_correlation_group_id',
        'events',
        ['correlation_group_id']
    )

    # Add correlated_event_ids column (JSON array as TEXT for SQLite)
    op.add_column(
        'events',
        sa.Column('correlated_event_ids', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove correlation columns from events table."""
    op.drop_index('idx_events_correlation_group_id', table_name='events')
    op.drop_column('events', 'correlation_group_id')
    op.drop_column('events', 'correlated_event_ids')
