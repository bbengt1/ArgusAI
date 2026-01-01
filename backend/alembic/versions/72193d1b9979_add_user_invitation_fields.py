"""add_user_invitation_fields

Revision ID: 72193d1b9979
Revises: h1a2b3c4d5e7
Create Date: 2026-01-01 12:00:51.910706

Story P16-1.1: Extend User Model for Multi-User Support
- Add invited_by foreign key to track who created each user
- Add invited_at timestamp to record invitation time
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72193d1b9979'
down_revision = 'h1a2b3c4d5e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story P16-1.1: Add invitation tracking fields to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invited_by', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('ix_users_invited_by', ['invited_by'], unique=False)
        batch_op.create_foreign_key(
            'fk_users_invited_by',
            'users',
            ['invited_by'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_invited_by', type_='foreignkey')
        batch_op.drop_index('ix_users_invited_by')
        batch_op.drop_column('invited_at')
        batch_op.drop_column('invited_by')
