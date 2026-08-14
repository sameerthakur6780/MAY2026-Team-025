from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user
from marshmallow import Schema, ValidationError, fields, validate

from app.services.assistant_service import ask_assistant, ingest_resource_pdf
from app.utils.decorators import role_required
from app.utils.errors import ApiError

assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


class AskSchema(Schema):
    query = fields.String(required=True, validate=validate.Length(min=1, max=2000))
    subject = fields.String(load_default=None)
    chapter = fields.String(load_default=None)


class IngestSchema(Schema):
    force = fields.Boolean(load_default=False)


_ask_schema = AskSchema()
_ingest_schema = IngestSchema()


@assistant_bp.post("/ask")
@role_required("student")
def ask():
    try:
        data = _ask_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    result = ask_assistant(
        current_user.id,
        data["query"],
        subject=data.get("subject"),
        chapter=data.get("chapter"),
    )
    return jsonify(result.model_dump()), 200


@assistant_bp.post("/ingest/<int:resource_id>")
@role_required("admin", "teacher")
def ingest_resource(resource_id):
    try:
        data = _ingest_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    try:
        result = ingest_resource_pdf(resource_id, force=data.get("force", False))
    except ApiError as exc:
        return jsonify({"error": exc.code, "message": str(exc)}), exc.status_code
    except Exception as exc:
        return jsonify({"error": "ingest_failed", "message": str(exc)}), 502

    return jsonify(result.model_dump()), 200
