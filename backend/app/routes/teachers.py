from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.auth_schema import SignupSchema
from app.schemas.teacher_schema import TeacherUpdateSchema
from app.services.teacher_service import (
    create_teacher,
    delete_teacher,
    get_teacher_or_404,
    serialize_teacher,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

teachers_bp = Blueprint("teachers", __name__, url_prefix="/api/teachers")

_signup_schema = SignupSchema()
_update_schema = TeacherUpdateSchema()


@teachers_bp.get("")
@role_required("admin")
def list_teachers():
    query = Teacher.query.join(Teacher.user).order_by(User.full_name)
    return jsonify(paginate_query(query, serialize_teacher)), 200


@teachers_bp.get("/<int:teacher_id>")
@role_required("admin")
def get_teacher(teacher_id):
    teacher = get_teacher_or_404(teacher_id)
    return jsonify(serialize_teacher(teacher)), 200


@teachers_bp.post("")
@role_required("admin")
def create_teacher_route():
    raw = request.get_json(silent=True) or {}
    raw["role"] = "teacher"
    try:
        data = _signup_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    teacher = create_teacher(data)
    return jsonify(serialize_teacher(teacher)), 201


@teachers_bp.patch("/<int:teacher_id>")
@role_required("admin")
def update_teacher_route(teacher_id):
    raw = request.get_json(silent=True) or {}
    try:
        _update_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    teacher = get_teacher_or_404(teacher_id)
    return jsonify(serialize_teacher(teacher)), 200


@teachers_bp.delete("/<int:teacher_id>")
@role_required("admin")
def delete_teacher_route(teacher_id):
    delete_teacher(teacher_id)
    return "", 204
