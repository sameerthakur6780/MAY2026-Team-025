from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.services.analytics_service import (
    get_admin_overview,
    get_attendance_trend,
    get_class_attendance,
    get_marks_trend,
)
from app.utils.decorators import role_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@analytics_bp.get("/overview")
@role_required("admin")
def overview():
    limit, err = _int_arg("limit")
    if err:
        return jsonify({"error": "validation_error", "message": {"limit": [err]}}), 400

    return jsonify(get_admin_overview(limit=limit or 3)), 200


@analytics_bp.get("/class-attendance")
@role_required("admin", "teacher")
def class_attendance():
    role = get_jwt()["role"]
    return jsonify(get_class_attendance(role)), 200


@analytics_bp.get("/attendance-trend")
@role_required("admin", "teacher", "parent", "student")
def attendance_trend():
    student_id, err = _int_arg("student_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"student_id": [err]}}), 400
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    months, err = _int_arg("months")
    if err:
        return jsonify({"error": "validation_error", "message": {"months": [err]}}), 400

    role = get_jwt()["role"]
    data = get_attendance_trend(role, student_id=student_id, class_id=class_id, months=months)
    return jsonify(data), 200


@analytics_bp.get("/marks-trend")
@role_required("admin", "parent", "student")
def marks_trend():
    student_id, err = _int_arg("student_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"student_id": [err]}}), 400
    months, err = _int_arg("months")
    if err:
        return jsonify({"error": "validation_error", "message": {"months": [err]}}), 400

    role = get_jwt()["role"]
    data = get_marks_trend(role, student_id=student_id, months=months)
    return jsonify(data), 200