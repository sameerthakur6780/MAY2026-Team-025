"""POST /api/auth/signup, /login, /logout, /refresh, GET /api/auth/me."""

from conftest import PASSWORD, create_admin_user, create_parent, create_student, create_teacher, login_as


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


def test_login_success_sets_cookies_and_returns_profile(client):
    user = create_admin_user(email="loginok@test.com")
    resp = client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"id": user.id, "full_name": user.full_name, "email": user.email, "role": "admin", "phone": None}
    set_cookie_headers = resp.headers.getlist("Set-Cookie")
    assert any("access_token_cookie" in h for h in set_cookie_headers)
    assert any("csrf_access_token" in h for h in set_cookie_headers)
    assert any("refresh_token_cookie" in h for h in set_cookie_headers)
    assert any("csrf_refresh_token" in h for h in set_cookie_headers)


def test_login_wrong_password_401(client):
    user = create_admin_user(email="wrongpw@test.com")
    resp = client.post("/api/auth/login", json={"email": user.email, "password": "nope"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "invalid_credentials"


def test_login_unknown_email_401(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": PASSWORD})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "invalid_credentials"


def test_login_malformed_email_validation_error(client):
    resp = client.post("/api/auth/login", json={"email": "not-an-email", "password": PASSWORD})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "email" in body["message"]


def test_login_missing_password_validation_error(client):
    resp = client.post("/api/auth/login", json={"email": "someone@test.com"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "password" in body["message"]


def test_login_rate_limited_after_five_attempts_per_minute(client):
    user = create_admin_user(email="ratelimited@test.com")
    for _ in range(5):
        resp = client.post("/api/auth/login", json={"email": user.email, "password": "wrong"})
        assert resp.status_code == 401
    resp = client.post("/api/auth/login", json={"email": user.email, "password": "wrong"})
    assert resp.status_code == 429
    assert resp.get_json()["error"] == "rate_limited"


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


def test_logout_clears_session_so_me_then_401s(client):
    user = create_admin_user(email="logout@test.com")
    authed = login_as(client, user.email)
    assert authed.get("/api/auth/me").status_code == 200

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.get_json()["message"]

    assert client.get("/api/auth/me").status_code == 401


def test_logout_without_a_session_still_succeeds(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "authentication_required"


def test_me_returns_current_users_profile(admin):
    resp = admin.get("/api/auth/me")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["role"] == "admin"


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------


def test_refresh_without_any_session_401(client):
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401


def test_refresh_issues_a_new_access_cookie(client):
    from conftest import extract_cookie

    user = create_admin_user(email="refresh@test.com")
    login_resp = client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD})
    refresh_csrf = extract_cookie(login_resp, "csrf_refresh_token")

    resp = client.post("/api/auth/refresh", headers={"X-CSRF-TOKEN": refresh_csrf})
    assert resp.status_code == 200
    assert any("access_token_cookie" in h for h in resp.headers.getlist("Set-Cookie"))

    # the refreshed access cookie is actually usable
    assert client.get("/api/auth/me").status_code == 200


def test_refresh_rejects_access_token_csrf_value(client):
    """The refresh endpoint's CSRF check must be bound to the refresh
    cookie's own CSRF value, not the access token's -- otherwise a leaked
    access-token CSRF value would be enough to mint new access tokens."""
    user = create_admin_user(email="refreshcsrf@test.com")
    authed = login_as(client, user.email)
    resp = client.post("/api/auth/refresh", headers={"X-CSRF-TOKEN": authed.csrf_token})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------------------


def test_signup_requires_authentication(client):
    resp = client.post(
        "/api/auth/signup",
        json={"role": "teacher", "full_name": "New Teacher", "email": "nt@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 401


def test_signup_forbidden_for_non_admin_roles(teacher):
    authed, _ = teacher
    resp = authed.post(
        "/api/auth/signup",
        json={"role": "teacher", "full_name": "New Teacher", "email": "nt2@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "forbidden"


def test_signup_creates_teacher_account(admin):
    resp = admin.post(
        "/api/auth/signup",
        json={"role": "teacher", "full_name": "New Teacher", "email": "newteacher@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["role"] == "teacher"
    assert body["email"] == "newteacher@test.com"
    assert "password" not in body and "password_hash" not in body


def test_signup_creates_parent_account(admin):
    resp = admin.post(
        "/api/auth/signup",
        json={
            "role": "parent",
            "full_name": "New Parent",
            "email": "newparent@test.com",
            "password": PASSWORD,
            "occupation": "Engineer",
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["role"] == "parent"


def test_signup_creates_student_account_with_admission_no(admin):
    resp = admin.post(
        "/api/auth/signup",
        json={
            "role": "student",
            "full_name": "New Student",
            "email": "newstudent@test.com",
            "password": PASSWORD,
            "admission_no": "ADM-1001",
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["role"] == "student"


def test_signup_student_without_admission_no_is_validation_error(admin):
    resp = admin.post(
        "/api/auth/signup",
        json={"role": "student", "full_name": "No Admission", "email": "noadm@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "admission_no" in body["message"]


def test_signup_rejects_admin_role(admin):
    """CREATABLE_ROLES excludes admin -- admins are never created through
    this endpoint."""
    resp = admin.post(
        "/api/auth/signup",
        json={"role": "admin", "full_name": "Sneaky Admin", "email": "sneaky@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_signup_short_password_is_validation_error(admin):
    resp = admin.post(
        "/api/auth/signup",
        json={"role": "teacher", "full_name": "Short PW", "email": "shortpw@test.com", "password": "abc"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "password" in body["message"]


def test_signup_missing_required_fields_is_validation_error(admin):
    resp = admin.post("/api/auth/signup", json={"role": "teacher"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "full_name" in body["message"]
    assert "email" in body["message"]
    assert "password" in body["message"]


def test_signup_duplicate_email_is_conflict(admin):
    create_teacher(email="dupe@test.com")
    resp = admin.post(
        "/api/auth/signup",
        json={"role": "parent", "full_name": "Dup Parent", "email": "dupe@test.com", "password": PASSWORD},
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "email_taken"
