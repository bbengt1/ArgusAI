"""Add event_feedback table for Story P4-5.1

Revision ID: 035_add_event_feedback
Revises: 034_add_delivery_status
Create Date: 2025-12-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '035_add_event_feedback'
down_revision: Union[str, None] = '034_add_delivery_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create event_feedback table for user feedback on AI descriptions."""
    op.create_table(
        'event_feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('rating', sa.String(20), nullable=False),
        sa.Column('correction', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_event_feedback_event_id')
    )
    op.create_index('ix_event_feedback_event_id', 'event_feedback', ['event_id'])


def downgrade() -> None:
    """Drop event_feedback table."""
    op.drop_index('ix_event_feedback_event_id', table_name='event_feedback')
    op.drop_table('event_feedback')
