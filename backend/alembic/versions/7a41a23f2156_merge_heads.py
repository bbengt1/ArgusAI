"""merge heads

Revision ID: 7a41a23f2156
Revises: 19df889882ef, c941f8a3e7d2
Create Date: 2025-12-22 19:01:57.894847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a41a23f2156'
down_revision = ('19df889882ef', 'c941f8a3e7d2')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
