"""
Application configuration for different environments.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Railway uses postgres:// but SQLAlchemy requires postgresql://
    _db_url = os.getenv("DATABASE_URL", "postgresql://aypa:password@localhost:5432/aypa_taxai")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # AI / LLM
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Embedding
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    # RAG
    RAG_CHUNK_SIZE = 500
    RAG_CHUNK_OVERLAP = 100
    RAG_MAX_CONTEXT_TOKENS = 600
    RAG_MAX_ANSWER_TOKENS = 300
    RAG_TOTAL_TOKEN_LIMIT = 1300
    RAG_BM25_WEIGHT = 0.4
    RAG_VECTOR_WEIGHT = 0.6
    RAG_RRF_K = 60
    RAG_CONFIDENCE_THRESHOLD = 0.7

    # Caching TTLs (seconds)
    CACHE_EMBEDDING_TTL = 3600  # 1 hour
    CACHE_CHUNKS_TTL = 300  # 5 minutes
    CACHE_ANSWER_TTL = 300  # 5 minutes

    # File storage
    S3_BUCKET = os.getenv("S3_BUCKET", "aypa-taxai-documents")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
    ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "xls", "csv", "txt"}

    # Rate limits (per user)
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "redis://localhost:6379/1")

    # Tier limits
    TIER_LIMITS = {
        "free": {"invoices_per_month": 30, "ai_queries_per_month": 2, "employees": 0},
        "starter": {"invoices_per_month": 200, "ai_queries_per_month": 100, "employees": 0},
        "professional": {"invoices_per_month": 1000, "ai_queries_per_month": 500, "employees": 20},
        "enterprise": {"invoices_per_month": -1, "ai_queries_per_month": -1, "employees": 50},
    }

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Monitoring
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # Knowledge base path
    KNOWLEDGE_BASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base"
    )


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)


class StagingConfig(BaseConfig):
    """Staging configuration."""

    DEBUG = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False

    # Enforce secure settings
    JWT_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
