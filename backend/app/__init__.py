"""
Aypa TaxAI - Backend Application Factory
Enterprise-grade AI-powered tax advisory and compliance platform.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
import redis

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO()

redis_client = None


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # Load configuration
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(f"app.config.{config_name.capitalize()}Config")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")

    # Initialize Redis
    global redis_client
    redis_client = redis.from_url(
        app.config.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register JWT callbacks
    _register_jwt_callbacks(app)

    return app


def _register_blueprints(app):
    """Register all API blueprints."""
    from app.api.auth import auth_bp
    from app.api.chat import chat_bp
    from app.api.invoice import invoice_bp
    from app.api.tax import tax_bp
    from app.api.payroll import payroll_bp
    from app.api.knowledge import knowledge_bp
    from app.api.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(invoice_bp, url_prefix="/api/invoices")
    app.register_blueprint(tax_bp, url_prefix="/api/tax")
    app.register_blueprint(payroll_bp, url_prefix="/api/payroll")
    app.register_blueprint(knowledge_bp, url_prefix="/api/knowledge")


def _register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(400)
    def bad_request(e):
        return {"error": "Bad request", "message": str(e)}, 400

    @app.errorhandler(401)
    def unauthorized(e):
        return {"error": "Unauthorized", "message": "Authentication required"}, 401

    @app.errorhandler(403)
    def forbidden(e):
        return {"error": "Forbidden", "message": "Insufficient permissions"}, 403

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found", "message": "Resource not found"}, 404

    @app.errorhandler(429)
    def rate_limited(e):
        return {"error": "Rate limited", "message": "Too many requests"}, 429

    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error", "message": "An unexpected error occurred"}, 500


def _register_jwt_callbacks(app):
    """Register JWT error callbacks."""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"error": "Token expired", "message": "Please log in again"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {"error": "Invalid token", "message": str(error)}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {"error": "Missing token", "message": "Authorization header required"}, 401
