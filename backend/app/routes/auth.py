from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
    get_csrf_token,
    get_jwt,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from marshmallow import ValidationError

from app.extensions import limiter
from app.schemas.auth_schema import LoginSchema, SignupSchema
from app.services.auth_service import AuthError, authenticate, create_managed_account
from app.utils.decorators import role_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_login_schema = LoginSchema()
_signup_schema = SignupSchema()


def _user_payload(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "phone": user.phone,
    }


def _validation_error_response(exc):
    return jsonify({"error": "validation_error", "message": exc.messages}), 400


@auth_bp.post("/signup")
@role_required("admin")
def signup():
    """Admin-only: creates a teacher, parent, or student account. Students
    never self-register."""
    raw = request.get_json(silent=True) or {}
    try:
        data = _signup_schema.load(raw)
    except ValidationError as exc:
        return _validation_error_response(exc)

    try:
        user = create_managed_account(data)
    except AuthError as exc:
        return jsonify({"error": exc.code, "message": str(exc)}), exc.status_code

    return jsonify(_user_payload(user)), 201


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    raw = request.get_json(silent=True) or {}
    try:
        data = _login_schema.load(raw)
    except ValidationError as exc:
        return _validation_error_response(exc)

    email = data["email"].strip().lower()

    try:
        user = authenticate(email, data["password"])
    except AuthError as exc:
        return jsonify({"error": exc.code, "message": str(exc)}), exc.status_code

    claims = {"role": user.role.value}
    access_token = create_access_token(identity=user, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user, additional_claims=claims)

    # The CSRF cookie flask-jwt-extended sets is only JS-readable by a page
    # same-origin with this backend -- true for local dev (same "localhost"
    # host), false in production where the frontend (Vercel) and this API
    # (Render) are different domains. Echoing it in the body too lets the
    # frontend hold it in memory and attach it as a header itself, instead
    # of depending on a document.cookie read that silently returns nothing
    # cross-origin (see apiClient.js).
    # The access and refresh tokens each carry their own independent csrf
    # claim (flask-jwt-extended requires the matching one per endpoint --
    # /refresh checks against the refresh token's, not the access token's),
    # so both need to reach the frontend, not just one.
    resp = jsonify(
        {
            **_user_payload(user),
            "csrf_access_token": get_csrf_token(access_token),
            "csrf_refresh_token": get_csrf_token(refresh_token),
        }
    )
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = current_user
    claims = {"role": user.role.value}
    access_token = create_access_token(identity=user, additional_claims=claims)

    resp = jsonify({"message": "Access token refreshed", "csrf_access_token": get_csrf_token(access_token)})
    set_access_cookies(resp, access_token)
    return resp, 200


@auth_bp.post("/logout")
def logout():
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp, 200


@auth_bp.get("/me")
@jwt_required()
def me():
    # Repopulates the frontend's in-memory csrf_access_token after a page
    # reload (it only lives in JS memory, not localStorage) -- get_jwt()
    # already has the current access token's csrf claim decoded, no need to
    # mint anything new for it here.
    return jsonify({**_user_payload(current_user), "csrf_access_token": get_jwt().get("csrf")}), 200
