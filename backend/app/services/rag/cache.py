"""Multi-layer caching for the RAG pipeline."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class RAGCacheManager:
    """
    Three-layer caching for RAG pipeline:
    - Layer 1: Query Embeddings (1h TTL)
    - Layer 2: Retrieved Chunks (5min TTL)
    - Layer 3: Final Answers (5min TTL)
    """

    def __init__(self, redis_client, config=None):
        self.redis = redis_client
        self.embedding_ttl = config.get("CACHE_EMBEDDING_TTL", 3600) if config else 3600
        self.chunks_ttl = config.get("CACHE_CHUNKS_TTL", 300) if config else 300
        self.answer_ttl = config.get("CACHE_ANSWER_TTL", 300) if config else 300

    # --- Layer 1: Query Embeddings ---

    def cache_embedding(self, query: str, embedding: np.ndarray):
        """Cache query embedding to avoid recomputation."""
        key = f"rag:emb:{self._hash_query(query)}"
        try:
            value = json.dumps(embedding.tolist())
            self.redis.setex(key, self.embedding_ttl, value)
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")

    def get_cached_embedding(self, query: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding."""
        key = f"rag:emb:{self._hash_query(query)}"
        try:
            cached = self.redis.get(key)
            if cached:
                return np.array(json.loads(cached))
        except Exception as e:
            logger.warning(f"Failed to read cached embedding: {e}")
        return None

    # --- Layer 2: Retrieved Chunks ---

    def cache_chunks(self, query: str, filters: dict, chunks: list[dict]):
        """Cache retrieved chunks."""
        key = f"rag:chunks:{self._hash_query(query)}:{self._hash_filters(filters)}"
        try:
            serializable = [
                {
                    "chunk_id": c.get("chunk_id"),
                    "text": c.get("text"),
                    "metadata": c.get("metadata", {}),
                    "fused_score": c.get("fused_score", 0),
                    "section_ref": c.get("section_ref", ""),
                }
                for c in chunks
            ]
            self.redis.setex(key, self.chunks_ttl, json.dumps(serializable))
        except Exception as e:
            logger.warning(f"Failed to cache chunks: {e}")

    def get_cached_chunks(self, query: str, filters: dict) -> Optional[list[dict]]:
        """Retrieve cached chunks."""
        key = f"rag:chunks:{self._hash_query(query)}:{self._hash_filters(filters)}"
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to read cached chunks: {e}")
        return None

    # --- Layer 3: Final Answers ---

    def cache_answer(self, query: str, context_hash: str, answer: str, confidence: float):
        """Cache final answer."""
        key = f"rag:answer:{self._hash_query(query)}:{context_hash}"
        try:
            value = json.dumps({
                "answer": answer,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            })
            self.redis.setex(key, self.answer_ttl, value)
        except Exception as e:
            logger.warning(f"Failed to cache answer: {e}")

    def get_cached_answer(self, query: str, context_hash: str) -> Optional[dict]:
        """Retrieve cached answer."""
        key = f"rag:answer:{self._hash_query(query)}:{context_hash}"
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to read cached answer: {e}")
        return None

    # --- Cache management ---

    def invalidate_all(self):
        """Clear all RAG caches (e.g., on knowledge base update)."""
        try:
            for pattern in ["rag:emb:*", "rag:chunks:*", "rag:answer:*"]:
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self.redis.delete(*keys)
                    if cursor == 0:
                        break
            logger.info("RAG cache invalidated")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")

    # --- Utilities ---

    @staticmethod
    def _hash_query(query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    @staticmethod
    def _hash_filters(filters: dict) -> str:
        filter_str = json.dumps(filters, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()
