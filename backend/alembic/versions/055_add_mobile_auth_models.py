"""add_mobile_auth_models

Revision ID: 055
Revises: 054
Create Date: 2025-12-26 15:00:00.000000

Story P12-3.1: Create PairingCode and RefreshToken models
- PairingCode: Temporary 6-digit codes for device pairing
- RefreshToken: JWT refresh tokens with rotation support
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '055'
down_revision = '054'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pairing_codes and refresh_tokens tables."""
    # Create pairing_codes table
    op.create_table(
        'pairing_codes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('device_model', sa.String(100), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_pairing_codes_code', 'pairing_codes', ['code'])
    op.create_index('ix_pairing_codes_expires', 'pairing_codes', ['expires_at'])
    op.create_index('ix_pairing_codes_device', 'pairing_codes', ['device_id'])

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('device_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('token_family', sa.String(36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_tokens_hash', 'refresh_tokens', ['token_hash'])
    op.create_index('ix_refresh_tokens_device', 'refresh_tokens', ['device_id'])
    op.create_index('ix_refresh_tokens_user', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_family', 'refresh_tokens', ['token_family'])


def downgrade() -> None:
    """Drop pairing_codes and refresh_tokens tables."""
    op.drop_index('ix_refresh_tokens_family', 'refresh_tokens')
    op.drop_index('ix_refresh_tokens_user', 'refresh_tokens')
    op.drop_index('ix_refresh_tokens_device', 'refresh_tokens')
    op.drop_index('ix_refresh_tokens_hash', 'refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index('ix_pairing_codes_device', 'pairing_codes')
    op.drop_index('ix_pairing_codes_expires', 'pairing_codes')
    op.drop_index('ix_pairing_codes_code', 'pairing_codes')
    op.drop_table('pairing_codes')
