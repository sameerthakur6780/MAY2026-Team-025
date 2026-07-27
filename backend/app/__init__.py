from flask import Flask, jsonify

from config import Config
from app.extensions import bcrypt, cors, db, jwt, limiter, migrate


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}},
        supports_credentials=True,
    )
    limiter.init_app(app)

    @app.errorhandler(429)
    def ratelimit_handler(exc):
        return jsonify({"error": "rate_limited", "message": str(exc.description)}), 429

    @app.errorhandler(413)
    def payload_too_large_handler(exc):
        return jsonify({"error": "file_too_large", "message": "Upload exceeds the maximum allowed size"}), 413

    from app.services.auth_service import AuthError
    from app.utils.errors import ApiError

    @app.errorhandler(ApiError)
    @app.errorhandler(AuthError)
    def handle_api_error(exc):
        return jsonify({"error": exc.code, "message": str(exc)}), exc.status_code

    from app.utils import jwt_callbacks  # noqa: F401  registers JWT loader callbacks

    from app.routes.assignments import assignments_bp
    from app.routes.attendance import attendance_bp
    from app.routes.auth import auth_bp
    from app.routes.classes import classes_bp
    from app.routes.health import health_bp
    from app.routes.parents import parents_bp
    from app.routes.resources import resources_bp
    from app.routes.students import students_bp
    from app.routes.subjects import subjects_bp
    from app.routes.teachers import teachers_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(parents_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(attendance_bp)

    from app.cli import create_admin
    app.cli.add_command(create_admin)

    from app import models  # noqa: F401  registers models with SQLAlchemy metadata

    return app