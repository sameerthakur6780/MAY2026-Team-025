from flask import jsonify

from app.extensions import jwt
from app.models.user import User


@jwt.user_identity_loader
def user_identity_lookup(user):
    """Lets create_access_token/create_refresh_token be called with either
    a User instance or a raw id."""
    return str(getattr(user, "id", user))


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    return User.query.get(int(jwt_data["sub"]))


@jwt.user_lookup_error_loader
def user_lookup_error_callback(_jwt_header, _jwt_data):
    return jsonify({"error": "user_not_found", "message": "User no longer exists"}), 401


@jwt.unauthorized_loader
def missing_token_callback(reason):
    return jsonify({"error": "authentication_required", "message": reason}), 401


@jwt.invalid_token_loader
def invalid_token_callback(reason):
    # Fires for a malformed/tampered token, or a mismatched X-CSRF-TOKEN header.
    # A *missing* CSRF header instead goes through unauthorized_loader below.
    return jsonify({"error": "invalid_token", "message": reason}), 401


@jwt.expired_token_loader
def expired_token_callback(_jwt_header, _jwt_data):
    return jsonify({"error": "token_expired", "message": "Token has expired"}), 401