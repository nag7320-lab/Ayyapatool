"""Health check endpoints."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Basic health check."""
    return jsonify({"status": "healthy", "service": "aypa-taxai-api", "version": "1.0.0"})


@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    """Readiness check - verifies database and cache connectivity."""
    checks = {"database": False, "cache": False}

    try:
        from app import db
        db.session.execute(db.text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        from app import redis_client
        if redis_client:
            redis_client.ping()
            checks["cache"] = True
    except Exception:
        pass

    all_healthy = all(checks.values())
    return jsonify({"status": "ready" if all_healthy else "degraded", "checks": checks}), 200 if all_healthy else 503
