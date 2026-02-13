"""Authentication and authorization endpoints."""

from datetime import datetime

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import Schema, fields, validate

from app import db, limiter
from app.models.user import Organization, OrgMembership, User

auth_bp = Blueprint("auth", __name__)


# --- Schemas ---

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.String(validate=validate.Length(max=15))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


register_schema = RegisterSchema()
login_schema = LoginSchema()


# --- Endpoints ---

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5/minute")
def register():
    """Register a new user account."""
    data = request.get_json()
    errors = register_schema.validate(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    password_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

    user = User(
        email=data["email"].lower(),
        password_hash=password_hash,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
        auth_provider="email",
        tier="free",
        role="user",
    )
    db.session.add(user)

    # Create default personal organization
    org = Organization(name=f"{user.first_name}'s Organization", tier="free")
    db.session.add(org)
    db.session.flush()

    membership = OrgMembership(user_id=user.id, org_id=org.id, role="owner", is_default=True)
    db.session.add(membership)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "tier": user.tier,
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json()
    errors = login_schema.validate(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    user = User.query.filter_by(email=data["email"].lower()).first()
    if not user or not user.password_hash:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(data["password"].encode(), user.password_hash.encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "tier": user.tier,
            "role": user.role,
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    })


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    orgs = []
    for m in user.memberships.all():
        orgs.append({
            "id": m.organization.id,
            "name": m.organization.name,
            "role": m.role,
            "is_default": m.is_default,
        })

    return jsonify({
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "tier": user.tier,
        "role": user.role,
        "organizations": orgs,
        "created_at": user.created_at.isoformat(),
    })
