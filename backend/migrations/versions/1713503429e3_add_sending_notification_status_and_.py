"""add sending notification status and announcement type

Revision ID: 1713503429e3
Revises: 979646623346
Create Date: 2026-08-20 14:19:15.567030

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1713503429e3"
down_revision = "979646623346"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE notificationstatus ADD VALUE IF NOT EXISTS 'SENDING'"
        )
        op.execute(
            "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ANNOUNCEMENT'"
        )


def downgrade():
    pass