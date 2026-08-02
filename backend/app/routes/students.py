from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt
from marshmallow import ValidationError

from app.schemas.auth_schema import SignupSchema
from app.schemas.student_schema import StudentUpdateSchema
from app.services.student_service import (
    create_student,
    delete_student,
    get_student_scoped,
    list_students_query,
    serialize_student,
    update_student,
    upload_profile_image,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

students_bp = Blueprint("students", __name__, url_prefix="/api/students")

_signup_schema = SignupSchema()
_update_schema = StudentUpdateSchema()


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@students_bp.get("")
@role_required("admin", "teacher", "parent")
def list_students():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    grade, err = _int_arg("grade")
    if err:
        return jsonify({"error": "validation_error", "message": {"grade": [err]}}), 400

    role = get_jwt()["role"]
    query = list_students_query(role, class_id=class_id, grade=grade)
    return jsonify(paginate_query(query, serialize_student)), 200


@students_bp.get("/<int:student_id>")
@role_required("admin", "teacher", "parent")
def get_student(student_id):
    role = get_jwt()["role"]
    student = get_student_scoped(student_id, role)
    return jsonify(serialize_student(student)), 200


@students_bp.post("")
@role_required("admin")
def create_student_route():
    raw = request.get_json(silent=True) or {}
    raw["role"] = "student"
    try:
        data = _signup_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    student = create_student(data)
    return jsonify(serialize_student(student)), 201


@students_bp.patch("/<int:student_id>")
@role_required("admin")
def update_student_route(student_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    student = update_student(student_id, data)
    return jsonify(serialize_student(student)), 200


@students_bp.delete("/<int:student_id>")
@role_required("admin")
def delete_student_route(student_id):
    delete_student(student_id)
    return "", 204


@students_bp.post("/<int:student_id>/profile-image")
@role_required("admin")
def upload_profile_image_route(student_id):
    file_storage = request.files.get("file")
    student = upload_profile_image(student_id, file_storage)
    return jsonify(serialize_student(student)), 200
