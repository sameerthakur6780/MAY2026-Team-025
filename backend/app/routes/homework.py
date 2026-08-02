from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt
from marshmallow import ValidationError

from app.schemas.homework_schema import HomeworkCreateSchema, HomeworkUpdateSchema
from app.services.homework_service import (
    create_homework,
    get_homework_scoped,
    list_homework_query,
    serialize_homework,
    update_homework,
)
from app.services.homework_submission_service import serialize_submission, submit_homework
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query
from app.utils.scoping import current_student

homework_bp = Blueprint("homework", __name__, url_prefix="/api/homework")

_create_schema = HomeworkCreateSchema()
_update_schema = HomeworkUpdateSchema()

_ALL_ROLES = ("admin", "teacher", "parent", "student")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@homework_bp.get("")
@role_required(*_ALL_ROLES)
def list_homework():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    subject_id, err = _int_arg("subject_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"subject_id": [err]}}), 400

    role = get_jwt()["role"]
    query = list_homework_query(role, class_id=class_id, subject_id=subject_id)
    return jsonify(paginate_query(query, serialize_homework)), 200


@homework_bp.get("/<int:homework_id>")
@role_required(*_ALL_ROLES)
def get_homework(homework_id):
    role = get_jwt()["role"]
    homework = get_homework_scoped(homework_id, role)
    return jsonify(serialize_homework(homework)), 200


@homework_bp.post("")
@role_required("admin", "teacher")
def create_homework_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _create_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    homework = create_homework(data, current_user.id)
    return jsonify(serialize_homework(homework)), 201


@homework_bp.patch("/<int:homework_id>")
@role_required("admin", "teacher")
def update_homework_route(homework_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    homework = update_homework(homework_id, data)
    return jsonify(serialize_homework(homework)), 200


@homework_bp.post("/<int:homework_id>/submissions")
@role_required("student")
def submit_homework_route(homework_id):
    file_storage = request.files.get("file")
    submission = submit_homework(homework_id, file_storage, current_student().id)
    return jsonify(serialize_submission(submission)), 201
