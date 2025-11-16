"""Add detection_schedule to cameras table

Revision ID: 004
Revises: 003
Create Date: 2025-11-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add detection_schedule JSON column to cameras table"""

    # Check if column already exists (from partial migration run)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('cameras')]

    if 'detection_schedule' not in columns:
        op.add_column('cameras', sa.Column('detection_schedule', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove detection_schedule column from cameras table"""

    op.drop_column('cameras', 'detection_schedule')
