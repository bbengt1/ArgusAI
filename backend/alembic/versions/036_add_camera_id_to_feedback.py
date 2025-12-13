"""Add camera_id to event_feedback for aggregate statistics (Story P4-5.2)

Revision ID: 036_add_camera_id_to_feedback
Revises: 035_add_event_feedback
Create Date: 2025-12-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '036_add_camera_id_to_feedback'
down_revision: Union[str, None] = '035_add_event_feedback'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add camera_id column to event_feedback table for aggregate statistics.

    Uses batch mode for SQLite compatibility (no ALTER TABLE constraints support).
    """
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('event_feedback', schema=None) as batch_op:
        # Add camera_id column
        batch_op.add_column(sa.Column('camera_id', sa.String(), nullable=True))

        # Create foreign key constraint (handled by batch mode for SQLite)
        batch_op.create_foreign_key(
            'fk_event_feedback_camera_id',
            'cameras',
            ['camera_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Create index for efficient aggregate queries
        batch_op.create_index('ix_event_feedback_camera_id', ['camera_id'])

    # Backfill existing feedback records with camera_id from their events
    # Using raw SQL for efficiency and SQLite compatibility
    op.execute("""
        UPDATE event_feedback
        SET camera_id = (
            SELECT events.camera_id
            FROM events
            WHERE events.id = event_feedback.event_id
        )
        WHERE camera_id IS NULL
    """)


def downgrade() -> None:
    """Remove camera_id column from event_feedback table."""
    with op.batch_alter_table('event_feedback', schema=None) as batch_op:
        batch_op.drop_index('ix_event_feedback_camera_id')
        batch_op.drop_constraint('fk_event_feedback_camera_id', type_='foreignkey')
        batch_op.drop_column('camera_id')
