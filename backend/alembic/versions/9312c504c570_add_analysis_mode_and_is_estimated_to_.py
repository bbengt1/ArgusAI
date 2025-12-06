"""add_analysis_mode_and_is_estimated_to_ai_usage

Revision ID: 9312c504c570
Revises: f7f1243134d4
Create Date: 2025-12-06 06:00:19.664034

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9312c504c570'
down_revision = 'f7f1243134d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add analysis_mode column (Story P3-2.5)
    op.add_column(
        'ai_usage',
        sa.Column('analysis_mode', sa.String(20), nullable=True)
    )
    # Add is_estimated column (Story P3-2.5)
    op.add_column(
        'ai_usage',
        sa.Column('is_estimated', sa.Boolean(), nullable=False, server_default='0')
    )
    # Create index for analysis_mode (if not exists handled by SQLite)
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX IF NOT EXISTS ix_ai_usage_analysis_mode ON ai_usage (analysis_mode)")


def downgrade() -> None:
    op.drop_index('ix_ai_usage_analysis_mode', 'ai_usage')
    op.drop_column('ai_usage', 'is_estimated')
    op.drop_column('ai_usage', 'analysis_mode')
