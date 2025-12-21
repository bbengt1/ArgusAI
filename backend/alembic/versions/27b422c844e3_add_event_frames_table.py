"""add_event_frames_table

Revision ID: 27b422c844e3
Revises: bdbfb90b1d66
Create Date: 2025-12-20 18:28:36.654102

Story P8-2.1: Store All Analysis Frames During Event Processing
Creates event_frames table to store metadata for frames used in AI analysis.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27b422c844e3'
down_revision = 'bdbfb90b1d66'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create event_frames table for storing AI analysis frame metadata
    op.create_table(
        'event_frames',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('frame_path', sa.String(500), nullable=False),
        sa.Column('timestamp_offset_ms', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'frame_number', name='uq_event_frame_number')
    )
    # Create index on event_id for efficient lookups
    op.create_index('idx_event_frames_event_id', 'event_frames', ['event_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_event_frames_event_id', table_name='event_frames')
    op.drop_table('event_frames')
