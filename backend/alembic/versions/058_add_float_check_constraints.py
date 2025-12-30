"""add_float_check_constraints

Revision ID: 058
Revises: 057
Create Date: 2025-12-30 12:00:00.000000

Story P14-5.6: Add Check Constraints on Float Columns
- Add check constraint on events.ai_confidence (0-100, nullable)
- Add check constraint on events.anomaly_score (0-1, nullable)
- Add check constraint on events.audio_confidence (0-1, nullable)
- Add check constraint on cameras.audio_threshold (0-1, nullable)

All constraints allow NULL values since these columns are optional.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '058'
down_revision = '057'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add check constraints to float columns in events and cameras tables."""

    # First, validate existing data before adding constraints
    # This will fail loudly if there's invalid data that needs manual correction
    connection = op.get_bind()

    # Check for invalid ai_confidence values (should be 0-100 or NULL)
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM events WHERE ai_confidence IS NOT NULL AND (ai_confidence < 0 OR ai_confidence > 100)"
    ))
    invalid_count = result.scalar()
    if invalid_count > 0:
        # Fix invalid values by clamping to valid range
        op.execute(sa.text(
            "UPDATE events SET ai_confidence = 0 WHERE ai_confidence IS NOT NULL AND ai_confidence < 0"
        ))
        op.execute(sa.text(
            "UPDATE events SET ai_confidence = 100 WHERE ai_confidence IS NOT NULL AND ai_confidence > 100"
        ))

    # Check for invalid anomaly_score values (should be 0-1 or NULL)
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM events WHERE anomaly_score IS NOT NULL AND (anomaly_score < 0 OR anomaly_score > 1)"
    ))
    invalid_count = result.scalar()
    if invalid_count > 0:
        op.execute(sa.text(
            "UPDATE events SET anomaly_score = 0 WHERE anomaly_score IS NOT NULL AND anomaly_score < 0"
        ))
        op.execute(sa.text(
            "UPDATE events SET anomaly_score = 1 WHERE anomaly_score IS NOT NULL AND anomaly_score > 1"
        ))

    # Check for invalid audio_confidence values (should be 0-1 or NULL)
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM events WHERE audio_confidence IS NOT NULL AND (audio_confidence < 0 OR audio_confidence > 1)"
    ))
    invalid_count = result.scalar()
    if invalid_count > 0:
        op.execute(sa.text(
            "UPDATE events SET audio_confidence = 0 WHERE audio_confidence IS NOT NULL AND audio_confidence < 0"
        ))
        op.execute(sa.text(
            "UPDATE events SET audio_confidence = 1 WHERE audio_confidence IS NOT NULL AND audio_confidence > 1"
        ))

    # Check for invalid audio_threshold values in cameras (should be 0-1 or NULL)
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM cameras WHERE audio_threshold IS NOT NULL AND (audio_threshold < 0 OR audio_threshold > 1)"
    ))
    invalid_count = result.scalar()
    if invalid_count > 0:
        op.execute(sa.text(
            "UPDATE cameras SET audio_threshold = 0 WHERE audio_threshold IS NOT NULL AND audio_threshold < 0"
        ))
        op.execute(sa.text(
            "UPDATE cameras SET audio_threshold = 1 WHERE audio_threshold IS NOT NULL AND audio_threshold > 1"
        ))

    # SQLite requires batch mode for adding constraints to existing tables
    # Add constraints to events table
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'check_ai_confidence_range',
            'ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 100)'
        )
        batch_op.create_check_constraint(
            'check_anomaly_score_range',
            'anomaly_score IS NULL OR (anomaly_score >= 0 AND anomaly_score <= 1)'
        )
        batch_op.create_check_constraint(
            'check_audio_confidence_range',
            'audio_confidence IS NULL OR (audio_confidence >= 0 AND audio_confidence <= 1)'
        )

    # Add constraint to cameras table
    with op.batch_alter_table('cameras', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'check_audio_threshold_range',
            'audio_threshold IS NULL OR (audio_threshold >= 0 AND audio_threshold <= 1)'
        )


def downgrade() -> None:
    """Remove check constraints from float columns."""
    # Remove constraints from events table
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('check_ai_confidence_range', type_='check')
        batch_op.drop_constraint('check_anomaly_score_range', type_='check')
        batch_op.drop_constraint('check_audio_confidence_range', type_='check')

    # Remove constraint from cameras table
    with op.batch_alter_table('cameras', schema=None) as batch_op:
        batch_op.drop_constraint('check_audio_threshold_range', type_='check')
