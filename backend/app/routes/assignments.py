from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.schemas.assignment_schema import AssignmentSchema
from app.services.assignment_service import (
    create_assignment,
    delete_assignment,
    list_assignments_query,
    serialize_assignment,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

assignments_bp = Blueprint("assignments", __name__, url_prefix="/api/assignments")

_assignment_schema = AssignmentSchema()


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@assignments_bp.get("")
@role_required("admin")
def list_assignments():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    teacher_id, err = _int_arg("teacher_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"teacher_id": [err]}}), 400

    query = list_assignments_query(class_id=class_id, teacher_id=teacher_id)
    return jsonify(paginate_query(query, serialize_assignment)), 200


@assignments_bp.post("")
@role_required("admin")
def create_assignment_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _assignment_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    assignment = create_assignment(data)
    return jsonify(serialize_assignment(assignment)), 201


@assignments_bp.delete("/<int:assignment_id>")
@role_required("admin")
def delete_assignment_route(assignment_id):
    delete_assignment(assignment_id)
    return "", 204
