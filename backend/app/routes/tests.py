from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt
from marshmallow import ValidationError

from app.schemas.test_schema import TestCreateSchema, TestUpdateSchema
from app.services.test_service import (
    create_test,
    get_test_scoped,
    list_tests_query,
    serialize_test,
    update_test,
)
from app.services.test_submission_service import serialize_submission, submit_test
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query
from app.utils.scoping import current_student

tests_bp = Blueprint("tests", __name__, url_prefix="/api/tests")

_create_schema = TestCreateSchema()
_update_schema = TestUpdateSchema()

_ALL_ROLES = ("admin", "teacher", "parent", "student")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@tests_bp.get("")
@role_required(*_ALL_ROLES)
def list_tests():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    subject_id, err = _int_arg("subject_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"subject_id": [err]}}), 400

    role = get_jwt()["role"]
    query = list_tests_query(role, class_id=class_id, subject_id=subject_id)
    return jsonify(paginate_query(query, serialize_test)), 200


@tests_bp.get("/<int:test_id>")
@role_required(*_ALL_ROLES)
def get_test(test_id):
    role = get_jwt()["role"]
    test = get_test_scoped(test_id, role)
    return jsonify(serialize_test(test)), 200


@tests_bp.post("")
@role_required("admin", "teacher")
def create_test_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _create_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    test = create_test(data, current_user.id)
    return jsonify(serialize_test(test)), 201


@tests_bp.patch("/<int:test_id>")
@role_required("admin", "teacher")
def update_test_route(test_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    test = update_test(test_id, data)
    return jsonify(serialize_test(test)), 200


@tests_bp.post("/<int:test_id>/submissions")
@role_required("student")
def submit_test_route(test_id):
    file_storage = request.files.get("file")
    submission = submit_test(test_id, file_storage, current_student().id)
    return jsonify(serialize_submission(submission)), 201
