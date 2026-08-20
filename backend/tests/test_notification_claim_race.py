"""Proves NotificationService's atomic claim step (PENDING -> SENDING)
actually prevents two concurrent callers from both winning -- the mechanism
that makes delivery safe if the same pending notification is ever picked up
by two worker processes at once (see the single-worker note on `scheduler`
in app/extensions.py for what this does and doesn't cover).

Deliberately NOT using the rest of the suite's in-memory/StaticPool `app`
fixture: StaticPool hands out the *same* single connection to every caller,
which would serialize the two "workers" through one connection and prove
nothing about real concurrent DB access. This test uses a real on-disk
SQLite file with NullPool (a brand new connection per checkout) so the two
threads are genuinely independent database clients racing for the same
row, the way two separate OS processes actually would.
"""
import threading
from datetime import timedelta

from sqlalchemy.pool import NullPool

from app import create_app
from app.extensions import bcrypt, db
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import RoleEnum, User
from app.services.notification_service import _claim_for_sending


def _race_config(db_path):
    class RaceConfig:
        TESTING = True
        DEBUG = False
        SECRET_KEY = "race-secret"
        # A real file, not :memory: -- two threads need to be able to open
        # two independent connections to the *same* database, and a private
        # :memory: database only exists within the connection that created
        # it.
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        # NullPool: a fresh connection per checkout, never shared/reused.
        # `timeout` gives SQLite's own busy-wait a real window to let the
        # loser's UPDATE simply not match (0 rows) instead of raising
        # "database is locked" while the winner's transaction is committing.
        SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool, "connect_args": {"timeout": 30}}
        SQLALCHEMY_TRACK_MODIFICATIONS = False

        FRONTEND_ORIGINS = ["http://localhost:5173"]
        RATELIMIT_STORAGE_URI = "memory://"

        JWT_SECRET_KEY = "race-jwt-secret-at-least-32-bytes-long"
        JWT_TOKEN_LOCATION = ["cookies"]
        JWT_COOKIE_SECURE = False
        JWT_COOKIE_SAMESITE = "Lax"
        JWT_COOKIE_CSRF_PROTECT = True
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
        JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
        JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"

        SUPABASE_URL = "http://fake.invalid"
        SUPABASE_SERVICE_ROLE_KEY = "fake-key"
        SUPABASE_BUCKET_NAME = "fake-bucket"

        MAX_UPLOAD_SIZE_BYTES = 1024 * 1024
        ALLOWED_UPLOAD_EXTENSIONS = {"pdf"}
        RESOURCE_SIGNED_URL_EXPIRY_SECONDS = 300
        MAX_CONTENT_LENGTH = 2 * 1024 * 1024

        FACE_IMAGE_ALLOWED_EXTENSIONS = {"jpg"}
        FACE_MODEL_NAME = "VGG-Face"
        FACE_DETECTOR_BACKEND = "opencv"
        FACE_HIGH_CONFIDENCE_THRESHOLD = 0.55
        FACE_LOW_CONFIDENCE_THRESHOLD = 0.40

        MAIL_DEFAULT_SENDER = "SmartBatch <no-reply@smartbatch.test>"
        MAIL_SUPPRESS_SEND = True
        SCHEDULER_ENABLED = False

    return RaceConfig


def test_claim_for_sending_is_race_safe_across_real_connections(tmp_path):
    db_path = tmp_path / "claim_race.db"
    app = create_app(_race_config(db_path))

    with app.app_context():
        db.create_all()
        user = User(
            full_name="Race User",
            email="race@test.com",
            password_hash=bcrypt.generate_password_hash("Password123").decode("utf-8"),
            phone="9000000099",
            role=RoleEnum.ADMIN,
        )
        db.session.add(user)
        db.session.commit()

        notification = Notification(
            user_id=user.id,
            type=NotificationType.FEE_DUE_REMINDER,
            subject="Race test",
            body="Race body",
            status=NotificationStatus.PENDING,
        )
        db.session.add(notification)
        db.session.commit()
        notification_id = notification.id

    # Two threads, each its own app context (-> its own Flask-SQLAlchemy
    # session -> its own real sqlite3 connection, via NullPool), released by
    # the same barrier so both actually call _claim_for_sending() at once
    # rather than one finishing before the other starts.
    barrier = threading.Barrier(2)
    results = {}
    errors = {}

    def worker(name):
        try:
            with app.app_context():
                barrier.wait(timeout=5)
                results[name] = _claim_for_sending(notification_id)
        except Exception as exc:  # pragma: no cover -- surfaced via `errors` assertion below
            errors[name] = exc

    threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in (1, 2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert not any(t.is_alive() for t in threads), "a worker thread hung -- claim likely deadlocked"
    assert errors == {}, f"a worker raised instead of cleanly losing the race: {errors}"

    assert len(results) == 2
    outcomes = sorted(results.values())
    assert outcomes == [False, True], (
        f"expected exactly one winner and one loser, got {results} -- "
        "either both won (race not actually prevented) or both lost (claim broken)"
    )

    winners = [name for name, won in results.items() if won]
    assert len(winners) == 1

    with app.app_context():
        stored = Notification.query.get(notification_id)
        assert stored.status == NotificationStatus.SENDING

        # The claim is a plain UPDATE, not itself an audit log -- but the
        # single winner really did flip the row exactly once. A second call
        # after the fact (simulating a third late worker) must also lose,
        # since the row is no longer PENDING.
        assert _claim_for_sending(notification_id) is False