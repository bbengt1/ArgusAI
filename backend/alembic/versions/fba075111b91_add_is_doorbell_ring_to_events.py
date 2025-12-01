"""add_is_doorbell_ring_to_events

Revision ID: fba075111b91
Revises: 013
Create Date: 2025-12-01 11:24:21.292267

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fba075111b91'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_doorbell_ring column with default FALSE for backwards compatibility
    # Story P2-4.1: Doorbell ring event detection support
    op.add_column(
        'events',
        sa.Column('is_doorbell_ring', sa.Boolean(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('events', 'is_doorbell_ring')
