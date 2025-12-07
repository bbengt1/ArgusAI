"""Add analysis_mode column to cameras table (Story P3-3.1)

Revision ID: 017
Revises: 2d5158847bc1
Create Date: 2025-12-06

Story P3-3.1: Add analysis_mode field to Camera model to enable per-camera
configuration of AI analysis mode (single_frame, multi_frame, video_native).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017'
down_revision = '2d5158847bc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add analysis_mode column to cameras table with default 'single_frame'"""

    # Add analysis_mode column with default value for existing records
    op.add_column('cameras', sa.Column(
        'analysis_mode',
        sa.String(length=20),
        nullable=False,
        server_default='single_frame'
    ))

    # Create index for efficient filtering by analysis mode
    op.create_index('ix_cameras_analysis_mode', 'cameras', ['analysis_mode'], unique=False)

    # Add CHECK constraint for valid values
    # Note: SQLite supports CHECK constraints but Alembic batch operations may be needed
    # For SQLite, the constraint is enforced at application level via SQLAlchemy model
    # This constraint is added for documentation and for PostgreSQL deployments
    with op.batch_alter_table('cameras') as batch_op:
        batch_op.create_check_constraint(
            'check_analysis_mode',
            "analysis_mode IN ('single_frame', 'multi_frame', 'video_native')"
        )


def downgrade() -> None:
    """Remove analysis_mode column from cameras table"""

    # Drop CHECK constraint first
    with op.batch_alter_table('cameras') as batch_op:
        batch_op.drop_constraint('check_analysis_mode', type_='check')

    # Drop index
    op.drop_index('ix_cameras_analysis_mode', table_name='cameras')

    # Drop column
    op.drop_column('cameras', 'analysis_mode')
