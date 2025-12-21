"""add_video_path_to_events

Revision ID: 8c3f2a9d5b1e
Revises: 27b422c844e3
Create Date: 2025-12-21

Story P8-3.2: Add Full Motion Video Download Toggle
Adds video_path column to events table for storing full motion videos.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c3f2a9d5b1e'
down_revision = '27b422c844e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add video_path column to events table
    op.add_column('events', sa.Column('video_path', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('events', 'video_path')
