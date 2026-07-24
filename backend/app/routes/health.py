from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    db_status = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    return jsonify({
        "status": "ok",
        "db": db_status,
    })
