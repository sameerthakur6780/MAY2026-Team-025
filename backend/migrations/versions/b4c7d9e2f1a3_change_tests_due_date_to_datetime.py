"""change tests due_date from Date to DateTime

Revision ID: b4c7d9e2f1a3
Revises: f3b8c2d1e4a5
Create Date: 2026-08-30 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b4c7d9e2f1a3"
down_revision = "f3b8c2d1e4a5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.alter_column(
            "due_date",
            existing_type=sa.Date(),
            type_=sa.DateTime(),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.alter_column(
            "due_date",
            existing_type=sa.DateTime(),
            type_=sa.Date(),
            existing_nullable=False,
        )
