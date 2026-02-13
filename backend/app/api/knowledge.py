"""Knowledge base management API endpoints (admin only)."""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db, limiter
from app.models.rag import Document
from app.models.user import User

knowledge_bp = Blueprint("knowledge", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def _require_admin():
    """Check if current user is admin."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role not in ("admin", "super_admin"):
        return None
    return user


@knowledge_bp.route("/documents", methods=["GET"])
@jwt_required()
def list_documents():
    """List all knowledge base documents."""
    user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    category = request.args.get("category")
    status = request.args.get("status", "active")
    page = request.args.get("page", 1, type=int)

    query = Document.query
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "sub_category": doc.sub_category,
                "document_type": doc.document_type,
                "status": doc.status,
                "processing_status": doc.processing_status,
                "chunks_count": doc.chunks_count,
                "file_size_mb": doc.file_size_mb,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in pagination.items
        ],
        "total": pagination.total,
        "page": pagination.page,
    })


@knowledge_bp.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("10/minute")
def upload_document():
    """Upload a document to the knowledge base."""
    user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    category = request.form.get("category")
    if not category:
        return jsonify({"error": "Category is required"}), 400

    import os
    from flask import current_app

    # Save file
    kb_path = current_app.config.get("KNOWLEDGE_BASE_PATH", "knowledge_base")
    save_dir = os.path.join(kb_path, category)
    os.makedirs(save_dir, exist_ok=True)

    import uuid
    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(save_dir, safe_filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path) / (1024 * 1024)

    # Parse metadata
    import json
    metadata = {}
    if request.form.get("metadata"):
        try:
            metadata = json.loads(request.form["metadata"])
        except json.JSONDecodeError:
            pass

    doc = Document(
        title=metadata.get("title", file.filename),
        category=category,
        sub_category=metadata.get("sub_category"),
        document_type=metadata.get("document_type"),
        issued_by=metadata.get("issued_by"),
        keywords=metadata.get("keywords", []),
        file_path=file_path,
        file_size_mb=round(file_size, 2),
        file_type=extension,
        processing_status="pending",
        uploaded_by=user.id,
    )
    db.session.add(doc)
    db.session.commit()

    # In production, queue processing via Celery:
    # process_document.delay(doc.id)

    return jsonify({
        "document_id": doc.id,
        "status": "pending",
        "message": "Document uploaded. Processing will begin shortly.",
    }), 202


@knowledge_bp.route("/documents/<doc_id>", methods=["DELETE"])
@jwt_required()
def delete_document(doc_id):
    """Archive a knowledge base document."""
    user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    doc.status = "archived"
    db.session.commit()

    return jsonify({"message": "Document archived", "id": doc.id})


@knowledge_bp.route("/stats", methods=["GET"])
@jwt_required()
def knowledge_stats():
    """Get knowledge base statistics."""
    user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    from sqlalchemy import func

    total_docs = Document.query.filter_by(status="active").count()
    total_chunks = db.session.query(func.sum(Document.chunks_count)).filter(
        Document.status == "active"
    ).scalar() or 0

    by_category = (
        db.session.query(Document.category, func.count(Document.id))
        .filter(Document.status == "active")
        .group_by(Document.category)
        .all()
    )

    return jsonify({
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "by_category": {cat: count for cat, count in by_category},
    })
