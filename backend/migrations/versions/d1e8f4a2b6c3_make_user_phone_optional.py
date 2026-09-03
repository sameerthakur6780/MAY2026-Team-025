"""make user phone optional

Revision ID: d1e8f4a2b6c3
Revises: b4c7d9e2f1a3
Create Date: 2026-08-31 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d1e8f4a2b6c3"
down_revision = "b4c7d9e2f1a3"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"
    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "phone",
            existing_type=sa.VARCHAR(length=20),
            nullable=True,
        )

    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade():
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"
    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "phone",
            existing_type=sa.VARCHAR(length=20),
            nullable=False,
        )

    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
