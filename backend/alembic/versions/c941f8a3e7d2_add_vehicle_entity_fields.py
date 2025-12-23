"""add_vehicle_entity_fields

Story P9-4.1: Improve Vehicle Entity Extraction Logic

Add vehicle_color, vehicle_make, vehicle_model, and vehicle_signature columns
to recognized_entities table for signature-based vehicle matching.

Revision ID: c941f8a3e7d2
Revises: b875e9bd8602
Create Date: 2025-12-22 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c941f8a3e7d2'
down_revision = 'b875e9bd8602'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add vehicle-specific columns for signature-based matching
    op.add_column('recognized_entities',
        sa.Column('vehicle_color', sa.String(50), nullable=True)
    )
    op.add_column('recognized_entities',
        sa.Column('vehicle_make', sa.String(50), nullable=True)
    )
    op.add_column('recognized_entities',
        sa.Column('vehicle_model', sa.String(50), nullable=True)
    )
    op.add_column('recognized_entities',
        sa.Column('vehicle_signature', sa.String(150), nullable=True)
    )
    # Add index for efficient signature-based lookups
    op.create_index(
        'idx_recognized_entities_vehicle_signature',
        'recognized_entities',
        ['vehicle_signature']
    )


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_recognized_entities_vehicle_signature', table_name='recognized_entities')
    # Remove columns
    op.drop_column('recognized_entities', 'vehicle_signature')
    op.drop_column('recognized_entities', 'vehicle_model')
    op.drop_column('recognized_entities', 'vehicle_make')
    op.drop_column('recognized_entities', 'vehicle_color')
