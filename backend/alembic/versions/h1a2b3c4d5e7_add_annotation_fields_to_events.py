"""Add annotation fields to events table

Story P15-5.1: AI Visual Annotations

Adds has_annotations and bounding_boxes fields to events table for
storing AI-generated bounding box coordinates.

Revision ID: h1a2b3c4d5e7
Revises: g1a2b3c4d5e6
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h1a2b3c4d5e7'
down_revision = 'g1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    """Add annotation fields to events table."""
    # Add has_annotations boolean field (default False)
    op.add_column('events', sa.Column('has_annotations', sa.Boolean(), nullable=False, server_default='0'))

    # Add bounding_boxes text field for JSON array storage
    op.add_column('events', sa.Column('bounding_boxes', sa.Text(), nullable=True))


def downgrade():
    """Remove annotation fields from events table."""
    op.drop_column('events', 'bounding_boxes')
    op.drop_column('events', 'has_annotations')
