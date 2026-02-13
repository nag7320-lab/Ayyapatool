"""RAG system models: documents, chunks, chat sessions."""

import uuid
from datetime import datetime

from app import db


class Document(db.Model):
    """Knowledge base document metadata."""

    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    sub_category = db.Column(db.String(50))
    document_type = db.Column(db.String(50))  # notification, circular, case_law, faq, guide
    issued_by = db.Column(db.String(100))
    issue_date = db.Column(db.Date)
    effective_date = db.Column(db.Date)

    # Versioning
    amendment_of = db.Column(db.String(36), db.ForeignKey("documents.id"))
    status = db.Column(db.String(20), default="active")  # active, superseded, archived

    # Keywords
    keywords = db.Column(db.JSON, default=list)

    # File info
    file_path = db.Column(db.String(500), nullable=False)
    file_size_mb = db.Column(db.Float)
    file_type = db.Column(db.String(10))

    # Processing
    chunks_count = db.Column(db.Integer, default=0)
    processing_status = db.Column(
        db.String(20), default="pending"
    )  # pending, processing, completed, failed
    processing_error = db.Column(db.Text)

    indexed_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)

    uploaded_by = db.Column(db.String(36), db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    chunks = db.relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.title[:50]}>"


class Chunk(db.Model):
    """Document chunks with embeddings metadata."""

    __tablename__ = "chunks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id"), nullable=False)

    text = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer)  # Position in document
    level = db.Column(db.Integer, default=1)  # 1=section, 2=subsection, 3=paragraph
    section_ref = db.Column(db.String(100))
    page_number = db.Column(db.Integer)
    tokens = db.Column(db.Integer)

    # Linking for context
    prev_chunk_id = db.Column(db.String(36))
    next_chunk_id = db.Column(db.String(36))

    # Hash for deduplication
    content_hash = db.Column(db.String(32), index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    document = db.relationship("Document", back_populates="chunks")


class ChatSession(db.Model):
    """User chat sessions."""

    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="chat_sessions")
    messages = db.relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(db.Model):
    """Individual chat messages."""

    __tablename__ = "chat_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("chat_sessions.id"), nullable=False)

    role = db.Column(db.String(10), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)

    # RAG metadata
    intent_category = db.Column(db.String(50))
    intent_complexity = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    sources = db.Column(db.JSON, default=list)
    escalated = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    session = db.relationship("ChatSession", back_populates="messages")


class QueryLog(db.Model):
    """Analytics log for all RAG queries."""

    __tablename__ = "query_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"))
    query = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    complexity = db.Column(db.String(20))

    # Performance
    response_time_ms = db.Column(db.Integer)
    cache_hit = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    escalated = db.Column(db.Boolean, default=False)

    # Chunks used
    chunks_retrieved = db.Column(db.Integer)
    top_chunk_score = db.Column(db.Float)

    # LLM
    llm_model = db.Column(db.String(50))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
