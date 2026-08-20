from flask import Blueprint, jsonify
from flask_jwt_extended import current_user

from app.services.notification_service import list_notifications_query, serialize_notification
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.get("")
@role_required("admin", "teacher", "parent", "student")
def list_notifications():
    query = list_notifications_query(current_user.id)
    return jsonify(paginate_query(query, serialize_notification)), 200
