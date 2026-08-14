import sqlite3
from datetime import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
# Single in-process scheduler for scheduled notifications (see
# notification_service.py). Same reasoning as before for skipping Celery:
# one lightweight in-process worker is enough at this project's scale, no
# broker to run/operate. Tradeoff worth knowing: its job store is in-memory,
# so a restart forgets pending jobs -- notification_service.py re-registers
# them from the `notifications` table (the durable source of truth) on
# startup to cover that. It also isn't safe to run in more than one worker
# process at a time (each would redeliver the same scheduled notification);
# fine for this project's single-process deployment, but would need a
# shared job store (or moving to Celery) before scaling out.
# timezone pinned to UTC explicitly -- notification_service.py always deals
# in UTC (see _utcnow()), and letting APScheduler fall back to the server's
# local zone would make `scheduled_at` times ambiguous depending on where
# this ends up deployed.
scheduler = BackgroundScheduler(timezone=timezone.utc)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
