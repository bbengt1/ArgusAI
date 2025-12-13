"""add_anomaly_score_to_events

Story P4-7.2: Anomaly Scoring

Adds anomaly_score column to events table for tracking how unusual
each event is compared to the camera's baseline activity patterns.
Score range is 0.0 (completely normal) to 1.0 (highly anomalous).

Revision ID: 040_add_anomaly_score
Revises: 039_add_object_type_distribution
Create Date: 2025-12-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040_add_anomaly_score'
down_revision = '039_add_object_type_distribution'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add anomaly_score column to events table."""
    op.add_column(
        'events',
        sa.Column('anomaly_score', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    """Remove anomaly_score column from events table."""
    op.drop_column('events', 'anomaly_score')
