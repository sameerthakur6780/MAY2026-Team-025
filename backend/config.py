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

    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

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
