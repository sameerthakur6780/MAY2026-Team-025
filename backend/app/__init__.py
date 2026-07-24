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

    from app.utils import jwt_callbacks  # noqa: F401  registers JWT loader callbacks

    from app.routes.auth import auth_bp
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    from app.cli import create_admin
    app.cli.add_command(create_admin)

    from app import models  # noqa: F401  registers models with SQLAlchemy metadata

    return app
