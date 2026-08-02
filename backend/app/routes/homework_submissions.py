from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt
from marshmallow import ValidationError

from app.schemas.submission_schema import GradeSchema
from app.services.homework_submission_service import (
    get_download_url,
    grade_submission,
    list_submissions_query,
    serialize_submission,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

homework_submissions_bp = Blueprint("homework_submissions", __name__, url_prefix="/api/homework-submissions")

_grade_schema = GradeSchema()

_ALL_ROLES = ("admin", "teacher", "parent", "student")
_VALID_STATUSES = ("pending", "graded")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


def _status_arg():
    raw = request.args.get("status")
    if raw is None:
        return None, None
    if raw not in _VALID_STATUSES:
        return None, f"status must be one of: {', '.join(_VALID_STATUSES)}"
    return raw, None


@homework_submissions_bp.get("")
@role_required(*_ALL_ROLES)
def list_submissions():
    homework_id, err = _int_arg("homework_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"homework_id": [err]}}), 400
    student_id, err = _int_arg("student_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"student_id": [err]}}), 400
    status, err = _status_arg()
    if err:
        return jsonify({"error": "validation_error", "message": {"status": [err]}}), 400

    role = get_jwt()["role"]
    query = list_submissions_query(role, homework_id=homework_id, student_id=student_id, status=status)
    return jsonify(paginate_query(query, serialize_submission)), 200


@homework_submissions_bp.get("/<int:submission_id>/download")
@role_required(*_ALL_ROLES)
def download_submission(submission_id):
    role = get_jwt()["role"]
    url, expires_in, _submission = get_download_url(submission_id, role)
    return jsonify({"url": url, "expires_in": expires_in}), 200


@homework_submissions_bp.patch("/<int:submission_id>/grade")
@role_required("admin", "teacher")
def grade_submission_route(submission_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _grade_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    submission = grade_submission(submission_id, data["marks"], data.get("feedback"), current_user.id)
    return jsonify(serialize_submission(submission)), 200
