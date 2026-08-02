from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.models.academic import Subject
from app.schemas.subject_schema import SubjectSchema
from app.services.subject_service import (
    create_subject,
    delete_subject,
    get_subject_or_404,
    serialize_subject,
    update_subject,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

subjects_bp = Blueprint("subjects", __name__, url_prefix="/api/subjects")

_subject_schema = SubjectSchema()


@subjects_bp.get("")
@role_required("admin", "teacher", "parent", "student")
def list_subjects():
    query = Subject.query.order_by(Subject.name)
    return jsonify(paginate_query(query, serialize_subject)), 200


@subjects_bp.get("/<int:subject_id>")
@role_required("admin", "teacher", "parent", "student")
def get_subject(subject_id):
    subject = get_subject_or_404(subject_id)
    return jsonify(serialize_subject(subject)), 200


@subjects_bp.post("")
@role_required("admin")
def create_subject_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _subject_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    subject = create_subject(data)
    return jsonify(serialize_subject(subject)), 201


@subjects_bp.patch("/<int:subject_id>")
@role_required("admin")
def update_subject_route(subject_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _subject_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    subject = update_subject(subject_id, data)
    return jsonify(serialize_subject(subject)), 200


@subjects_bp.delete("/<int:subject_id>")
@role_required("admin")
def delete_subject_route(subject_id):
    delete_subject(subject_id)
    return "", 204
