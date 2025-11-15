"""Create cameras table

Revision ID: 001
Revises: 
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create cameras table with all required fields and constraints"""
    op.create_table(
        'cameras',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=10), nullable=False),
        sa.Column('rtsp_url', sa.String(length=500), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('password', sa.String(length=500), nullable=True),
        sa.Column('device_index', sa.Integer(), nullable=True),
        sa.Column('frame_rate', sa.Integer(), nullable=False, default=5),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('motion_sensitivity', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('motion_cooldown', sa.Integer(), nullable=False, default=60),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("type IN ('rtsp', 'usb')", name='check_camera_type'),
        sa.CheckConstraint('frame_rate >= 1 AND frame_rate <= 30', name='check_frame_rate'),
        sa.CheckConstraint("motion_sensitivity IN ('low', 'medium', 'high')", name='check_sensitivity'),
        sa.CheckConstraint('motion_cooldown >= 0 AND motion_cooldown <= 300', name='check_cooldown'),
    )
    
    # Create index on is_enabled for faster queries
    op.create_index('idx_cameras_is_enabled', 'cameras', ['is_enabled'])


def downgrade() -> None:
    """Drop cameras table and index"""
    op.drop_index('idx_cameras_is_enabled', table_name='cameras')
    op.drop_table('cameras')
