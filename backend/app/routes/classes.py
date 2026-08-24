from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt
from marshmallow import ValidationError
from sqlalchemy.orm import selectinload

from app.models.academic import SchoolClass
from app.schemas.class_schema import ClassSchema
from app.services.class_service import (
    create_class,
    delete_class,
    get_class_scoped,
    scoped_class_query,
    serialize_class,
    update_class,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

classes_bp = Blueprint("classes", __name__, url_prefix="/api/classes")

_class_schema = ClassSchema()


@classes_bp.get("")
@role_required("admin", "teacher", "parent")
def list_classes():
    role = get_jwt()["role"]
    # serialize_class computes len(school_class.students) per row -- eager-load
    # the collection in one query instead of an extra round trip per row.
    query = scoped_class_query(role).options(selectinload(SchoolClass.students)).order_by(SchoolClass.grade)
    return jsonify(paginate_query(query, serialize_class)), 200


@classes_bp.get("/<int:class_id>")
@role_required("admin", "teacher", "parent")
def get_class(class_id):
    role = get_jwt()["role"]
    school_class = get_class_scoped(class_id, role)
    return jsonify(serialize_class(school_class)), 200


@classes_bp.post("")
@role_required("admin")
def create_class_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _class_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    school_class = create_class(data)
    return jsonify(serialize_class(school_class)), 201


@classes_bp.patch("/<int:class_id>")
@role_required("admin")
def update_class_route(class_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _class_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    school_class = update_class(class_id, data)
    return jsonify(serialize_class(school_class)), 200


@classes_bp.delete("/<int:class_id>")
@role_required("admin")
def delete_class_route(class_id):
    delete_class(class_id)
    return "", 204