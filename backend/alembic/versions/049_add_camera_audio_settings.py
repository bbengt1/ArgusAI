"""Add camera audio settings columns

Revision ID: 049_add_camera_audio_settings
Revises: 048_add_audio_event_fields
Create Date: 2025-12-17

Story P6-3.3: Add Audio Settings to Camera Configuration
- audio_event_types: JSON array of event types to detect per camera
- audio_threshold: Per-camera confidence threshold override (nullable, uses global default if null)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '049_add_camera_audio_settings'
down_revision: Union[str, None] = '048_add_audio_event_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add audio_event_types and audio_threshold columns to cameras table."""
    # Add audio_event_types as TEXT (JSON array) - stores which audio events to detect
    # Valid values: glass_break, gunshot, scream, doorbell
    # Null or empty array means detect all types
    op.add_column('cameras', sa.Column('audio_event_types', sa.Text(), nullable=True))

    # Add audio_threshold as FLOAT - per-camera confidence threshold override
    # Null means use global threshold from system_settings
    # Valid range: 0.0 to 1.0
    op.add_column('cameras', sa.Column('audio_threshold', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove audio_event_types and audio_threshold columns."""
    op.drop_column('cameras', 'audio_threshold')
    op.drop_column('cameras', 'audio_event_types')
