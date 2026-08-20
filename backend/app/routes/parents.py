from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.orm import contains_eager, selectinload

from app.models.parent import Parent
from app.models.user import User
from app.schemas.auth_schema import SignupSchema
from app.schemas.parent_schema import ParentUpdateSchema
from app.services.parent_service import (
    create_parent,
    delete_parent,
    get_parent_or_404,
    serialize_parent,
    update_parent,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

parents_bp = Blueprint("parents", __name__, url_prefix="/api/parents")

_signup_schema = SignupSchema()
_update_schema = ParentUpdateSchema()


@parents_bp.get("")
@role_required("admin")
def list_parents():
    # serialize_parent touches user (already joined for ordering -- reuse it
    # via contains_eager instead of a second join) and students on every row.
    query = (
        Parent.query.join(Parent.user)
        .options(contains_eager(Parent.user), selectinload(Parent.students))
        .order_by(User.full_name)
    )
    return jsonify(paginate_query(query, serialize_parent)), 200


@parents_bp.get("/<int:parent_id>")
@role_required("admin")
def get_parent(parent_id):
    parent = get_parent_or_404(parent_id)
    return jsonify(serialize_parent(parent)), 200


@parents_bp.post("")
@role_required("admin")
def create_parent_route():
    raw = request.get_json(silent=True) or {}
    raw["role"] = "parent"
    try:
        data = _signup_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    parent = create_parent(data)
    return jsonify(serialize_parent(parent)), 201


@parents_bp.patch("/<int:parent_id>")
@role_required("admin")
def update_parent_route(parent_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    parent = update_parent(parent_id, data)
    return jsonify(serialize_parent(parent)), 200


@parents_bp.delete("/<int:parent_id>")
@role_required("admin")
def delete_parent_route(parent_id):
    delete_parent(parent_id)
    return "", 204
