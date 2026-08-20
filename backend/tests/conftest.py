"""Shared fixtures for the Sprint 1 API test suite.

Every test gets a fresh Flask app wired to an in-memory SQLite database
(StaticPool keeps the single :memory: connection alive across requests
within a test) -- the real sqlite file under instance/ is never touched.
Supabase Storage is replaced with an in-memory fake so no network calls
happen during resource-upload/download/delete tests.
"""

import itertools
from datetime import timedelta
from http.cookies import SimpleCookie

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import bcrypt
from app.extensions import db as _db
from app.models.academic import ClassSubjectTeacher, SchoolClass, Subject
from app.models.user import RoleEnum, User
from app.services.auth_service import create_managed_account

PASSWORD = "Password123"

_id_counter = itertools.count(1)


def next_id():
    return next(_id_counter)


def default_phone():
    """A deterministic, valid-format (10-digit, starts with 6-9) phone
    number for tests that don't care about the actual value."""
    return f"9{next_id():09d}"


class TestConfig:
    TESTING = True
    # Explicit, not just "unset": config.py's load_dotenv() pulls in the
    # dev .env's FLASK_DEBUG=1 as a process-wide env var, and Flask's own
    # app.debug falls back to that env var whenever DEBUG isn't set
    # explicitly here -- without this, tests would inherit debug=True from
    # whatever the developer's local .env happens to have, which trips
    # notification_service.py's reloader guard (it treats debug=True as "we
    # might be the Werkzeug reloader's parent watcher process" and skips
    # starting the scheduler).
    DEBUG = False
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_ORIGINS = ["http://localhost:5173"]
    RATELIMIT_STORAGE_URI = "memory://"

    JWT_SECRET_KEY = "test-jwt-secret-at-least-32-bytes-long"
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

    MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"}
    RESOURCE_SIGNED_URL_EXPIRY_SECONDS = 300
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES + 1 * 1024 * 1024

    FACE_IMAGE_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    FACE_MODEL_NAME = "VGG-Face"
    FACE_DETECTOR_BACKEND = "opencv"
    FACE_HIGH_CONFIDENCE_THRESHOLD = 0.60
    FACE_LOW_CONFIDENCE_THRESHOLD = 0.40

    MAIL_DEFAULT_SENDER = "SmartBatch <no-reply@smartbatch.test>"
    MAIL_SUPPRESS_SEND = True  # belt-and-suspenders on top of TESTING=True -- never a real SMTP call in tests
    SCHEDULER_ENABLED = False  # no background thread per test app instance

    RAZORPAY_KEY_ID = "test-key-id"
    RAZORPAY_KEY_SECRET = "test-key-secret"
    RAZORPAY_WEBHOOK_SECRET = "test-webhook-secret"
    FEE_GENERATION_DAY_OF_MONTH = 25
    FEE_DUE_DAY_OF_MONTH = 10


class FakeStorageService:
    """In-memory stand-in for SupabaseStorageService. No network I/O."""

    def __init__(self):
        self.store = {}

    def upload(self, path, file_bytes, content_type):
        self.store[path] = file_bytes
        return path

    def get_signed_url(self, path, expires_in, download_filename=None):
        return f"https://fake-storage.test/{path}?expires_in={expires_in}"

    def delete(self, path):
        self.store.pop(path, None)


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def fake_storage(app, monkeypatch):
    fake = FakeStorageService()
    monkeypatch.setattr("app.services.resource_service.get_storage_service", lambda: fake)
    return fake


_ip_counter = itertools.count(1)


@pytest.fixture()
def make_client(app, fake_storage):
    """Factory for fresh, independent test clients against the same app/db.

    Each gets a unique fake source IP so Flask-Limiter's per-IP login quota
    never leaks between clients (or between tests).
    """

    def _make():
        c = app.test_client()
        n = next(_ip_counter)
        c.environ_base["REMOTE_ADDR"] = f"10.{(n >> 8) & 255}.{n & 255}.1"
        return c

    return _make


@pytest.fixture()
def client(make_client):
    return make_client()


def extract_cookie(response, name):
    for header in response.headers.getlist("Set-Cookie"):
        cookie = SimpleCookie()
        cookie.load(header)
        if name in cookie:
            return cookie[name].value
    return None


class AuthedClient:
    """Wraps a logged-in test client, auto-attaching the X-CSRF-TOKEN header
    (double-submitted from the csrf_access_token cookie, matching how the
    real frontend's apiClient behaves) on every state-changing request."""

    def __init__(self, raw_client, csrf_token):
        self.raw = raw_client
        self.csrf_token = csrf_token

    def get(self, *args, **kwargs):
        return self.raw.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._mutate("post", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._mutate("patch", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._mutate("delete", *args, **kwargs)

    def _mutate(self, method, *args, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers["X-CSRF-TOKEN"] = self.csrf_token
        return getattr(self.raw, method)(*args, headers=headers, **kwargs)


def login_as(raw_client, email, password=PASSWORD):
    resp = raw_client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.get_json()
    csrf = extract_cookie(resp, "csrf_access_token")
    assert csrf, "login succeeded but no csrf_access_token cookie was set"
    return AuthedClient(raw_client, csrf)


# ---------------------------------------------------------------------------
# Direct-DB fixture builders. These bypass HTTP for setup speed and call the
# same account-creation code path (create_managed_account) the real signup
# and /api/students|teachers|parents routes use, so password hashing and
# profile-row creation stay faithful to production behavior.
# ---------------------------------------------------------------------------


def create_admin_user(email=None, full_name="Test Admin", phone=None):
    email = email or f"admin{next_id()}@test.com"
    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(PASSWORD).decode("utf-8"),
        phone=phone or default_phone(),
        role=RoleEnum.ADMIN,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def create_teacher(email=None, full_name="Test Teacher", phone=None):
    email = email or f"teacher{next_id()}@test.com"
    user = create_managed_account(
        {
            "role": "teacher",
            "full_name": full_name,
            "email": email,
            "password": PASSWORD,
            "phone": phone or default_phone(),
        }
    )
    return user.teacher


def create_parent(email=None, full_name="Test Parent", phone=None, occupation=None, address=None):
    email = email or f"parent{next_id()}@test.com"
    user = create_managed_account(
        {
            "role": "parent",
            "full_name": full_name,
            "email": email,
            "password": PASSWORD,
            "phone": phone or default_phone(),
            "occupation": occupation,
            "address": address,
        }
    )
    return user.parent


def create_student(email=None, full_name="Test Student", phone=None, admission_no=None, class_id=None, parent_id=None):
    email = email or f"student{next_id()}@test.com"
    admission_no = admission_no or f"ADM{next_id()}"
    user = create_managed_account(
        {
            "role": "student",
            "full_name": full_name,
            "email": email,
            "password": PASSWORD,
            "phone": phone or default_phone(),
            "admission_no": admission_no,
            "class_id": class_id,
            "parent_id": parent_id,
        }
    )
    return user.student


def create_class(grade):
    school_class = SchoolClass(grade=grade)
    _db.session.add(school_class)
    _db.session.commit()
    return school_class


def create_subject(name):
    subject = Subject(name=name)
    _db.session.add(subject)
    _db.session.commit()
    return subject


def create_assignment(class_id, subject_id, teacher_id):
    row = ClassSubjectTeacher(class_id=class_id, subject_id=subject_id, teacher_id=teacher_id)
    _db.session.add(row)
    _db.session.commit()
    return row


# ---------------------------------------------------------------------------
# Convenience fixtures for the common single-actor case. Tests needing more
# than one simultaneously-authenticated actor (role-scoping checks, "teacher
# B can't touch teacher A's stuff") should use `make_client` + `login_as` +
# the create_* helpers directly instead.
# ---------------------------------------------------------------------------


@pytest.fixture()
def admin(make_client):
    user = create_admin_user()
    return login_as(make_client(), user.email)


@pytest.fixture()
def teacher(make_client):
    teacher_row = create_teacher()
    authed = login_as(make_client(), teacher_row.user.email)
    return authed, teacher_row


@pytest.fixture()
def parent(make_client):
    parent_row = create_parent()
    authed = login_as(make_client(), parent_row.user.email)
    return authed, parent_row


@pytest.fixture()
def student(make_client):
    student_row = create_student()
    authed = login_as(make_client(), student_row.user.email)
    return authed, student_row
