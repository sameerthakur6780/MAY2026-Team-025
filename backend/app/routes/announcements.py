from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.schemas.announcement_schema import BroadcastSchema
from app.services.announcement_service import send_broadcast
from app.utils.decorators import role_required

announcements_bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")

_broadcast_schema = BroadcastSchema()


@announcements_bp.post("/broadcast")
@role_required("admin")
def broadcast_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _broadcast_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    recipient_count = send_broadcast(data["title"], data["message"], data["class_id"], data["priority"])
    return jsonify({"recipient_count": recipient_count}), 201
