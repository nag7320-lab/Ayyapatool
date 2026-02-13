"""User, Organization, and membership models."""

import uuid
from datetime import datetime

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=True)  # Null for OAuth users
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))

    # Auth
    auth_provider = db.Column(db.String(20), default="email")  # email, google, linkedin
    auth_provider_id = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))

    # Subscription
    tier = db.Column(db.String(20), default="free")  # free, starter, professional, enterprise
    tier_valid_until = db.Column(db.DateTime)

    # Role
    role = db.Column(db.String(20), default="user")  # user, admin, super_admin

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    memberships = db.relationship("OrgMembership", back_populates="user", lazy="dynamic")
    chat_sessions = db.relationship("ChatSession", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(200))
    gstin = db.Column(db.String(15), index=True)
    pan = db.Column(db.String(10))
    entity_type = db.Column(db.String(50))  # pvt_ltd, llp, partnership, proprietorship, etc.

    # Address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(6))

    # Contact
    email = db.Column(db.String(255))
    phone = db.Column(db.String(15))
    website = db.Column(db.String(255))

    # Branding
    logo_url = db.Column(db.String(500))

    # Settings
    invoice_prefix = db.Column(db.String(10), default="INV")
    invoice_next_number = db.Column(db.Integer, default=1)
    financial_year_start = db.Column(db.Integer, default=4)  # April

    # Subscription (org-level billing)
    tier = db.Column(db.String(20), default="free")

    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    memberships = db.relationship("OrgMembership", back_populates="organization", lazy="dynamic")
    invoices = db.relationship("Invoice", back_populates="organization", lazy="dynamic")
    employees = db.relationship("Employee", back_populates="organization", lazy="dynamic")
    bank_details = db.relationship("BankDetail", back_populates="organization", lazy="dynamic")

    def __repr__(self):
        return f"<Organization {self.name}>"


class OrgMembership(db.Model):
    __tablename__ = "org_memberships"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    org_id = db.Column(db.String(36), db.ForeignKey("organizations.id"), nullable=False)
    role = db.Column(db.String(20), default="member")  # owner, admin, member, viewer
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="memberships")
    organization = db.relationship("Organization", back_populates="memberships")

    __table_args__ = (db.UniqueConstraint("user_id", "org_id", name="uq_user_org"),)
