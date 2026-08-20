"""add notification html_body column

Revision ID: e2a1f6b0c9d4
Revises: 1713503429e3
Create Date: 2026-08-20 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2a1f6b0c9d4'
down_revision = '1713503429e3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('html_body', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('html_body')
