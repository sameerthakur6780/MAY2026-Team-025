"""add sending notification status and announcement type

Revision ID: 1713503429e3
Revises: 979646623346
Create Date: 2026-08-20 14:19:15.567030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1713503429e3'
down_revision = '979646623346'
branch_labels = None
depends_on = None


def upgrade():
    # SENDING has existed on the NotificationStatus model since
    # _claim_for_sending() was written, but the table's original migration
    # only ever created PENDING/SENT/FAILED -- every real send has been one
    # `UPDATE ... SET status='SENDING'` away from an invalid-enum-value error
    # on Postgres (SQLite never enforced this, so local dev never noticed).
    # ANNOUNCEMENT is new, for the admin broadcast feature.
    op.execute("ALTER TYPE notificationstatus ADD VALUE IF NOT EXISTS 'SENDING'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ANNOUNCEMENT'")


def downgrade():
    # Postgres has no ALTER TYPE ... DROP VALUE -- removing an enum value
    # requires rebuilding the type from scratch, not worth it for a downgrade
    # path that's never actually run against this project's databases.
    pass
