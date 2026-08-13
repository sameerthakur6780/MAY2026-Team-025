"""make user phone required

Revision ID: 5afc1a251071
Revises: c52b6ccecccd
Create Date: 2026-08-13 17:26:31.422363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5afc1a251071'
down_revision = 'c52b6ccecccd'
branch_labels = None
depends_on = None


users = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("phone", sa.String),
)


def _backfill_null_phones(conn):
    """Give every pre-existing NULL phone a deterministic placeholder so the
    NOT NULL constraint below doesn't fail on rows created back when phone
    was optional (self-signup, and the create-admin CLI before this change).
    Placeholders are 10 digits starting with 9, matching the app's Indian
    phone format so they don't fail validation if ever re-submitted -- but
    they're not real numbers, and every one of these accounts should have
    its actual phone number collected and corrected out-of-band.
    """
    rows = conn.execute(sa.select(users.c.id).where(users.c.phone.is_(None))).fetchall()
    for (user_id,) in rows:
        placeholder = f"9{user_id:09d}"
        conn.execute(users.update().where(users.c.id == user_id).values(phone=placeholder))


def upgrade():
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    # `PRAGMA foreign_keys` only takes effect outside of a transaction, and
    # pysqlite auto-opens one on the first DML statement -- so this has to
    # run before the backfill's UPDATEs, not just before the batch op.
    # SQLite has no real ALTER COLUMN: batch mode recreates the whole table
    # (create new, copy rows, drop old, rename), and teachers/parents/
    # students rows still hold foreign keys into `users` while it's briefly
    # gone. `PRAGMA defer_foreign_keys` looks like the fit for "mid-
    # transaction" but doesn't reliably survive a DROP+CREATE of the
    # referenced table, so this is the version that actually works.
    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")

    _backfill_null_phones(conn)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('phone',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    if is_sqlite:
        # Best-effort: by now we're mid-transaction (the backfill's UPDATEs
        # opened one), so this is very likely a no-op until it commits. The
        # app's own request-handling connections always get PRAGMA
        # foreign_keys=ON from the connect-time listener in extensions.py
        # regardless of this, so it's not relied on for correctness here.
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")


def downgrade():
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"
    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('phone',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)

    if is_sqlite:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
