import logging
import os
from datetime import timedelta

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


DEFAULT_DB_PATH = os.path.join(BASE_DIR, "instance", "smartbatch.db")


def _bool_env(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _require_env(name):
    """For secrets where a hardcoded fallback would be an actual security
    hole (e.g. every deployment silently signing sessions/JWTs with the same
    known "dev" string until someone notices). Raises at import time --
    loudly, at startup, in the deploy log -- rather than booting into a
    silently-insecure state. Render (and any other host) must set these via
    its dashboard/environment, not this file; backend/.env covers local dev
    (see .env.example)."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. This must be provided via environment variable -- there is no "
            f"default, because the only alternative would be an insecure hardcoded value. Set it in "
            f"Render's dashboard (Environment tab) for deployed environments, or in backend/.env locally."
        )
    return value


class Config:
    SECRET_KEY = _require_env("SECRET_KEY")
    # Render's disk is ephemeral (wiped on every redeploy/restart) -- that's
    # fine here since scripts/seed_demo_data.py is meant to be re-run after
    # every restart anyway. DATABASE_URL overrides this with a real
    # connection string (e.g. a managed Postgres) if one is ever added.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + DEFAULT_DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Comma-separated list of allowed browser origins for the frontend.
    # Local dev falls back to the Vite/CRA defaults below; Render's
    # dashboard should set this to the deployed Vercel URL once it exists
    # (e.g. "https://your-app.vercel.app"), comma-separated with any others
    # that need access (a Vercel preview URL, a second environment, etc.).
    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000,http://localhost:5173").split(",")
        if origin.strip()
    ]

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = _bool_env("JWT_COOKIE_SECURE", default=True)
    JWT_COOKIE_SAMESITE = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"

    # SUPABASE_URL is the current/preferred name; PROJECT_URL is kept as a
    # fallback only because it's what this project's existing .env already
    # uses -- set SUPABASE_URL on Render for a name that actually matches
    # the other two SUPABASE_* vars.
    SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("PROJECT_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_BUCKET_NAME = os.environ.get("SUPABASE_BUCKET_NAME", "secure-uploads")

    MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"}
    RESOURCE_SIGNED_URL_EXPIRY_SECONDS = 300

    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES + 1 * 1024 * 1024

    FACE_IMAGE_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    FACE_MODEL_NAME = os.environ.get("FACE_MODEL_NAME", "VGG-Face")
    FACE_DETECTOR_BACKEND = os.environ.get("FACE_DETECTOR_BACKEND", "opencv")
    # Cosine similarity in [0, 1] (VGG-Face, opencv detector). Verified against
    # a real end-to-end run (3 enrolled students + 1 unenrolled person, see
    # backend/test_cases.md rows 196-202 and backend/tests/manual_facial_recognition_check.py):
    # real correct matches scored 0.650-0.803, the highest incorrect match
    # scored 0.147 -- a 0.503 gap. HIGH was lowered from 0.60 to 0.55 to give
    # auto-marking more headroom on borderline-but-genuine matches (the
    # weakest real match, 0.650, only cleared 0.60 by 0.05); this costs
    # nothing on the false-positive side since 0.55 is still 0.403 above the
    # highest incorrect score observed. LOW=0.40 already had a wide margin
    # (0.253) below the real false-positive ceiling and is unchanged.
    # Small sample (n=3 / n=1 negative) -- re-tune if more real photos surface
    # different numbers.
    FACE_HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get("FACE_HIGH_CONFIDENCE_THRESHOLD", "0.55"))
    FACE_LOW_CONFIDENCE_THRESHOLD = float(os.environ.get("FACE_LOW_CONFIDENCE_THRESHOLD", "0.40"))

    # Email (Flask-Mail / SMTP -- see app/services/email.py for the tradeoff
    # against a transactional provider). Defaults point at Mailtrap-style
    # local/sandbox SMTP so an unconfigured dev env fails loudly (connection
    # refused) instead of silently pretending to send.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", default=True)
    MAIL_USE_SSL = _bool_env("MAIL_USE_SSL", default=False)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "SmartBatch <no-reply@smartbatch.test>")
    # Flask-Mail suppresses real sends whenever TESTING is set (see
    # flask_mail.Mail.init_mail) -- this only matters outside pytest, e.g. a
    # local dev server without SMTP creds configured yet.
    MAIL_SUPPRESS_SEND = _bool_env("MAIL_SUPPRESS_SEND", default=False)

    # Scheduler for NotificationService.schedule(). Off by default in tests
    # (see tests/conftest.py) so pytest never starts a background thread.
    SCHEDULER_ENABLED = _bool_env("SCHEDULER_ENABLED", default=True)

    # Razorpay (see app/services/razorpay_service.py for why this is plain
    # `requests` calls rather than the razorpay PyPI package). KEY_SECRET
    # signs API requests (create_order); WEBHOOK_SECRET is a *separate*
    # secret configured in the Razorpay dashboard's webhook settings, used
    # only to verify inbound webhook signatures -- never send it anywhere.
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    # Fee generation: FEE_GENERATION_DAY_OF_MONTH is when the "create next
    # month's StudentFee for every active FeePlan" job runs (a few days
    # before the next cycle starts); FEE_DUE_DAY_OF_MONTH is which day of
    # that cycle's month the fee is due on (clamped to the month's actual
    # length, e.g. day 31 in February). Both exist as env vars only so a
    # deployment can tune the billing calendar without a code change.
    FEE_GENERATION_DAY_OF_MONTH = int(os.environ.get("FEE_GENERATION_DAY_OF_MONTH", "25"))
    FEE_DUE_DAY_OF_MONTH = int(os.environ.get("FEE_DUE_DAY_OF_MONTH", "10"))


def validate_mail_config(app):
    """Called once from create_app(), after app.config.from_object(), so an
    unconfigured mail setup is caught at startup instead of surfacing as an
    opaque connection/auth error the first time something tries to send.

    There's no separate Dev/Prod Config subclass in this file (see Config
    above -- a single class, env-var-driven throughout); `app.debug` is
    already this codebase's stand-in for "am I a local dev server" (see the
    reloader guard in notification_service.init_scheduler), so it's reused
    here as the same signal: warn and keep booting on a debug/test server
    (you may be working on something that never sends mail), but fail loudly
    -- same philosophy as _require_env -- everywhere else (Render or any
    other non-debug deployment), where a silently broken mailer could go
    unnoticed for a long time.
    """
    if app.config.get("MAIL_SUPPRESS_SEND"):
        return  # no real send will be attempted -- nothing to validate
    if app.config.get("MAIL_USERNAME") and app.config.get("MAIL_PASSWORD"):
        return  # configured

    message = (
        "MAIL_USERNAME/MAIL_PASSWORD are not set and MAIL_SUPPRESS_SEND is not enabled -- any "
        "real send will fail with a connection/auth error. Set both in backend/.env (a Mailtrap "
        "sandbox inbox works for local dev -- see .env.example), or set MAIL_SUPPRESS_SEND=true "
        "if this environment should never send real email."
    )
    if app.debug or app.testing:
        logger.warning(message)
    else:
        raise RuntimeError(message)
