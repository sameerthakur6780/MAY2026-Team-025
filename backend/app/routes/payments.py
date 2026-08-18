"""Razorpay webhook receiver. Deliberately has no @role_required -- Razorpay's
servers call this, not a logged-in browser, so there's no JWT/CSRF to check.
The signature verification below is what stands in for auth here: without a
valid HMAC over the raw body, the request is rejected before any payload
field is trusted."""
import logging

from flask import Blueprint, current_app, jsonify, request

from app.services.fee_service import mark_fee_paid_from_webhook
from app.services.razorpay_service import verify_webhook_signature

logger = logging.getLogger(__name__)

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

_HANDLED_EVENTS = {"payment.captured", "order.paid"}


@payments_bp.post("/webhook")
def razorpay_webhook():
    signature = request.headers.get("X-Razorpay-Signature", "")
    raw_body = request.get_data()
    secret = current_app.config["RAZORPAY_WEBHOOK_SECRET"]

    if not verify_webhook_signature(raw_body, signature, secret):
        logger.warning("Rejected Razorpay webhook: signature verification failed")
        return jsonify({"error": "invalid_signature", "message": "Signature verification failed"}), 400

    payload = request.get_json(silent=True) or {}
    if payload.get("event") not in _HANDLED_EVENTS:
        # Razorpay expects a 2xx for events it isn't retried for -- ignoring
        # an event this integration doesn't act on is not an error.
        return jsonify({"status": "ignored"}), 200

    try:
        payment_entity = payload["payload"]["payment"]["entity"]
        order_id = payment_entity["order_id"]
        payment_id = payment_entity["id"]
    except (KeyError, TypeError):
        return jsonify({"error": "invalid_payload", "message": "Missing payment entity in webhook payload"}), 400

    fee = mark_fee_paid_from_webhook(order_id, payment_id)
    if fee is None:
        return jsonify({"status": "no_matching_fee"}), 200

    return jsonify({"status": "ok"}), 200