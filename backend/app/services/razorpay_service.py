"""Minimal Razorpay integration: create an order and verify webhook
signatures. Uses `requests` (already a transitive dependency via the
supabase client) with plain HTTP calls rather than adding the `razorpay`
PyPI package -- the two things this project actually needs (POST /v1/orders,
and an HMAC-SHA256 check) don't need a whole SDK, and one fewer dependency
to pin/audit is worth more here than the SDK's convenience wrappers.
"""
import hashlib
import hmac
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_ORDERS_URL = "https://api.razorpay.com/v1/orders"


class RazorpayError(Exception):
    """Raised when the Razorpay API call itself fails (network error, or a
    non-2xx response)."""


def create_order(amount_rupees, receipt, notes=None):
    """Creates a Razorpay order for `amount_rupees` and returns the parsed
    JSON response (includes the order `id` the frontend checkout widget
    needs, and `amount` echoed back in paise).

    Razorpay's API takes amounts in the smallest currency unit (paise for
    INR), not rupees -- the *100 conversion happens here so every other
    layer of this codebase can keep dealing in whole rupees, matching how
    fee amounts are already stored and displayed elsewhere (e.g.
    NotificationService's "Rs. {amount}" reminder text).
    """
    key_id = current_app.config["RAZORPAY_KEY_ID"]
    key_secret = current_app.config["RAZORPAY_KEY_SECRET"]
    payload = {
        "amount": int(round(amount_rupees * 100)),
        "currency": "INR",
        "receipt": receipt,
        "notes": notes or {},
    }
    try:
        response = requests.post(_ORDERS_URL, json=payload, auth=(key_id, key_secret), timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Razorpay create_order failed")
        raise RazorpayError(str(exc)) from exc
    return response.json()


def verify_webhook_signature(request_body, signature, webhook_secret):
    """Recomputes the HMAC-SHA256 signature Razorpay sends in the
    X-Razorpay-Signature header over the raw request body, using the
    webhook secret configured in the Razorpay dashboard (a separate secret
    from the API key pair). Constant-time compare so a timing attack can't
    be used to guess the expected signature byte-by-byte.

    `request_body` must be the *exact* raw bytes Razorpay signed --
    re-serializing parsed JSON can reorder keys or change whitespace and
    produce a different signature even for byte-identical logical content,
    which is why the caller passes request.get_data() rather than
    re-dumping request.get_json().
    """
    if not signature or not webhook_secret:
        return False
    expected = hmac.new(webhook_secret.encode("utf-8"), request_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)