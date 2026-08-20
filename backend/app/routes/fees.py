from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.models.fee import FeeStatus
from app.services.fee_service import create_payment_order, list_fees_query, send_fee_reminder, serialize_student_fee
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

fees_bp = Blueprint("fees", __name__, url_prefix="/api/fees")

_STATUS_VALUES = {s.value for s in FeeStatus}


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@fees_bp.get("")
@role_required("admin", "parent")
def list_fees():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400

    status = request.args.get("status")
    if status is not None and status not in _STATUS_VALUES:
        return (
            jsonify(
                {"error": "validation_error", "message": {"status": [f"must be one of {sorted(_STATUS_VALUES)}"]}}
            ),
            400,
        )

    role = get_jwt()["role"]
    query = list_fees_query(role, class_id=class_id, status=status)
    return jsonify(paginate_query(query, serialize_student_fee)), 200


@fees_bp.post("/<int:fee_id>/create-order")
@role_required("admin", "parent")
def create_order_route(fee_id):
    role = get_jwt()["role"]
    order = create_payment_order(fee_id, role)
    return jsonify(order), 201


@fees_bp.post("/<int:fee_id>/remind")
@role_required("admin")
def remind_route(fee_id):
    fee = send_fee_reminder(fee_id)
    return jsonify(serialize_student_fee(fee)), 200