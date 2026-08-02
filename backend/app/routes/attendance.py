from datetime import date as date_cls

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt
from marshmallow import ValidationError

from app.schemas.attendance_schema import AttendanceBulkSchema, AttendanceUpdateSchema
from app.schemas.facial_attendance_schema import FacialAttendanceSchema
from app.services.attendance_service import (
    bulk_mark_attendance,
    list_attendance_query,
    mark_attendance_facial,
    serialize_attendance,
    update_attendance,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

_bulk_schema = AttendanceBulkSchema()
_update_schema = AttendanceUpdateSchema()
_facial_schema = FacialAttendanceSchema()

_ALL_ROLES = ("admin", "teacher", "parent", "student")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


def _date_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return date_cls.fromisoformat(raw), None
    except ValueError:
        return None, f"{name} must be an ISO date (YYYY-MM-DD)"


@attendance_bp.get("")
@role_required(*_ALL_ROLES)
def list_attendance():
    student_id, err = _int_arg("student_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"student_id": [err]}}), 400
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    date_from, err = _date_arg("date_from")
    if err:
        return jsonify({"error": "validation_error", "message": {"date_from": [err]}}), 400
    date_to, err = _date_arg("date_to")
    if err:
        return jsonify({"error": "validation_error", "message": {"date_to": [err]}}), 400

    role = get_jwt()["role"]
    query = list_attendance_query(
        role, student_id=student_id, class_id=class_id, date_from=date_from, date_to=date_to
    )
    return jsonify(paginate_query(query, serialize_attendance)), 200


@attendance_bp.post("/bulk")
@role_required("admin", "teacher")
def bulk_mark():
    raw = request.get_json(silent=True) or {}
    try:
        data = _bulk_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    created, skipped_student_ids = bulk_mark_attendance(
        data["class_id"], data["date"], data["entries"], data["method"], current_user.id
    )
    return (
        jsonify(
            {
                "created": [serialize_attendance(a) for a in created],
                "skipped_student_ids": skipped_student_ids,
            }
        ),
        201,
    )


@attendance_bp.post("/facial")
@role_required("admin", "teacher")
def mark_attendance_facial_route():
    raw = request.form.to_dict()
    try:
        data = _facial_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    file_storage = request.files.get("image")
    result = mark_attendance_facial(data["class_id"], data["date"], file_storage, current_user.id)
    return jsonify(result), 200


@attendance_bp.patch("/<int:attendance_id>")
@role_required("admin", "teacher")
def update_attendance_route(attendance_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    attendance = update_attendance(attendance_id, data)
    return jsonify(serialize_attendance(attendance)), 200
