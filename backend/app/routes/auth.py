from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
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

    resp = jsonify(_user_payload(user))
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = current_user
    claims = {"role": user.role.value}
    access_token = create_access_token(identity=user, additional_claims=claims)

    resp = jsonify({"message": "Access token refreshed"})
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
    return jsonify(_user_payload(current_user)), 200
