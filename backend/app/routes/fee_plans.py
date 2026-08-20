from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.schemas.fee_schema import FeePlanCreateSchema, FeePlanUpdateSchema
from app.services.fee_service import (
    create_fee_plan,
    delete_fee_plan,
    get_fee_plan_or_404,
    list_fee_plans_query,
    serialize_fee_plan,
    update_fee_plan,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

fee_plans_bp = Blueprint("fee_plans", __name__, url_prefix="/api/fee-plans")

_create_schema = FeePlanCreateSchema()
_update_schema = FeePlanUpdateSchema()


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@fee_plans_bp.get("")
@role_required("admin")
def list_fee_plans():
    student_id, err = _int_arg("student_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"student_id": [err]}}), 400

    query = list_fee_plans_query(student_id=student_id)
    return jsonify(paginate_query(query, serialize_fee_plan)), 200


@fee_plans_bp.get("/<int:plan_id>")
@role_required("admin")
def get_fee_plan(plan_id):
    plan = get_fee_plan_or_404(plan_id)
    return jsonify(serialize_fee_plan(plan)), 200


@fee_plans_bp.post("")
@role_required("admin")
def create_fee_plan_route():
    raw = request.get_json(silent=True) or {}
    try:
        data = _create_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    plan = create_fee_plan(data)
    return jsonify(serialize_fee_plan(plan)), 201


@fee_plans_bp.patch("/<int:plan_id>")
@role_required("admin")
def update_fee_plan_route(plan_id):
    raw = request.get_json(silent=True) or {}
    try:
        data = _update_schema.load(raw, partial=True)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    plan = update_fee_plan(plan_id, data)
    return jsonify(serialize_fee_plan(plan)), 200


@fee_plans_bp.delete("/<int:plan_id>")
@role_required("admin")
def delete_fee_plan_route(plan_id):
    delete_fee_plan(plan_id)
    return "", 204