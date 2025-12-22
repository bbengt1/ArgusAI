"""add_correction_type_to_event_feedback

Story P9-3.3: Package False Positive Feedback

Add correction_type column to event_feedback table for tracking specific
feedback types like 'not_package' for package false positives.

Revision ID: b875e9bd8602
Revises: 8c3f2a9d5b1e
Create Date: 2025-12-22 15:16:04.945009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b875e9bd8602'
down_revision = '8c3f2a9d5b1e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add correction_type column for specific feedback types
    op.add_column('event_feedback',
        sa.Column('correction_type', sa.String(50), nullable=True)
    )
    # Add index for efficient querying by correction type
    op.create_index('ix_event_feedback_correction_type', 'event_feedback', ['correction_type'])


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_event_feedback_correction_type', table_name='event_feedback')
    # Remove column
    op.drop_column('event_feedback', 'correction_type')
