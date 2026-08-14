import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


DEFAULT_DB_PATH = os.path.join(BASE_DIR, "instance", "smartbatch.db")


def _bool_env(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + DEFAULT_DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000,http://localhost:5173").split(",")
        if origin.strip()
    ]

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = _bool_env("JWT_COOKIE_SECURE", default=True)
    JWT_COOKIE_SAMESITE = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"

    SUPABASE_URL = os.environ.get("PROJECT_URL")
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
