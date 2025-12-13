"""Add vehicle_embeddings table (Story P4-8.3)

Revision ID: 042_add_vehicle_embeddings
Revises: 041_add_face_embeddings
Create Date: 2025-12-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '042_add_vehicle_embeddings'
down_revision = '041_add_face_embeddings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vehicle_embeddings table for vehicle recognition (Story P4-8.3)."""
    op.create_table(
        'vehicle_embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=False),
        sa.Column('bounding_box', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('vehicle_type', sa.String(50), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['recognized_entities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for efficient querying
    op.create_index('idx_vehicle_embeddings_event_id', 'vehicle_embeddings', ['event_id'])
    op.create_index('idx_vehicle_embeddings_entity_id', 'vehicle_embeddings', ['entity_id'])
    op.create_index('idx_vehicle_embeddings_model_version', 'vehicle_embeddings', ['model_version'])


def downgrade() -> None:
    """Drop vehicle_embeddings table."""
    op.drop_index('idx_vehicle_embeddings_model_version', table_name='vehicle_embeddings')
    op.drop_index('idx_vehicle_embeddings_entity_id', table_name='vehicle_embeddings')
    op.drop_index('idx_vehicle_embeddings_event_id', table_name='vehicle_embeddings')
    op.drop_table('vehicle_embeddings')
