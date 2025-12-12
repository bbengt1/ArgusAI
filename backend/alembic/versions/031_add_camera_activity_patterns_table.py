"""add_camera_activity_patterns_table

Story P4-3.5: Pattern Detection

Adds camera_activity_patterns table for storing pre-calculated time-based
activity patterns for cameras in the Temporal Context Engine.

Revision ID: 031_add_camera_activity_patterns
Revises: 030_add_recognized_entities
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031_add_camera_activity_patterns'
down_revision = '030_add_recognized_entities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create camera_activity_patterns table."""
    op.create_table(
        'camera_activity_patterns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('camera_id', sa.String(length=36), nullable=False),
        sa.Column('hourly_distribution', sa.Text(), nullable=False),  # JSON dict
        sa.Column('daily_distribution', sa.Text(), nullable=False),   # JSON dict
        sa.Column('peak_hours', sa.Text(), nullable=False),           # JSON array
        sa.Column('quiet_hours', sa.Text(), nullable=False),          # JSON array
        sa.Column('average_events_per_day', sa.Float(), nullable=False),
        sa.Column('calculation_window_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('camera_id', name='uq_camera_activity_patterns_camera_id'),
    )

    # Create indexes for efficient lookups
    op.create_index('idx_camera_activity_patterns_camera_id', 'camera_activity_patterns', ['camera_id'])
    op.create_index('idx_camera_activity_patterns_last_calculated', 'camera_activity_patterns', ['last_calculated_at'])


def downgrade() -> None:
    """Drop camera_activity_patterns table."""
    op.drop_index('idx_camera_activity_patterns_last_calculated', table_name='camera_activity_patterns')
    op.drop_index('idx_camera_activity_patterns_camera_id', table_name='camera_activity_patterns')
    op.drop_table('camera_activity_patterns')
