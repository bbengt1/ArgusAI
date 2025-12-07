"""add_analysis_mode_and_frame_count_to_events

Revision ID: 2d5158847bc1
Revises: 9312c504c570
Create Date: 2025-12-06 11:30:19.470000

Story P3-2.6: Add analysis_mode and frame_count_used columns to events table
for tracking multi-frame analysis mode and number of frames used in AI analysis.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d5158847bc1'
down_revision = '9312c504c570'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story P3-2.6: Add analysis_mode column (indexed for filtering)
    op.add_column('events', sa.Column('analysis_mode', sa.String(length=20), nullable=True))
    op.create_index('ix_events_analysis_mode', 'events', ['analysis_mode'], unique=False)

    # Story P3-2.6: Add frame_count_used column
    op.add_column('events', sa.Column('frame_count_used', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_index('ix_events_analysis_mode', table_name='events')
    op.drop_column('events', 'frame_count_used')
    op.drop_column('events', 'analysis_mode')
