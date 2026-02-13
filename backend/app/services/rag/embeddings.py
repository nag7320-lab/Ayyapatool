"""Embedding generation pipeline with INT8 quantization."""

import hashlib
import logging
import re
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Generate and manage embeddings for the knowledge base."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384
        self._model = None
        self._scale_factors = None

    @property
    def model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts into embeddings."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single query."""
        return self.model.encode(query, convert_to_numpy=True)

    def quantize_int8(self, embeddings: np.ndarray) -> tuple[np.ndarray, dict]:
        """
        Quantize float32 embeddings to int8.
        Storage reduction: ~75%.
        Returns quantized array and scale factors for reconstruction.
        """
        min_val = embeddings.min(axis=0)
        max_val = embeddings.max(axis=0)
        scale = (max_val - min_val) / 255.0
        scale[scale == 0] = 1.0  # Avoid division by zero

        embeddings_scaled = (embeddings - min_val) / scale - 128
        embeddings_int8 = embeddings_scaled.astype(np.int8)

        return embeddings_int8, {"min_val": min_val, "scale": scale}

    def dequantize_int8(
        self, embeddings_int8: np.ndarray, scale_factors: dict
    ) -> np.ndarray:
        """Reconstruct float32 embeddings from int8."""
        return (
            (embeddings_int8.astype(np.float32) + 128) * scale_factors["scale"]
            + scale_factors["min_val"]
        )

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100,
    ) -> list[dict]:
        """
        Hierarchical chunking with overlap.
        Returns list of chunk dictionaries.
        """
        separators = ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
        chunks = []
        current_chunks = self._recursive_split(text, separators, chunk_size)

        position = 0
        for chunk_text in current_chunks:
            tokens_approx = int(len(chunk_text.split()) * 1.3)
            if tokens_approx < min_chunk_size:
                continue

            chunk = {
                "text": chunk_text.strip(),
                "position": position,
                "tokens": tokens_approx,
                "content_hash": hashlib.md5(chunk_text.strip().encode()).hexdigest(),
            }
            chunks.append(chunk)
            position += 1

        # Set linking
        for i, chunk in enumerate(chunks):
            chunk["prev_chunk_id"] = chunks[i - 1].get("id") if i > 0 else None
            chunk["next_chunk_id"] = (
                chunks[i + 1].get("id") if i < len(chunks) - 1 else None
            )

        return chunks

    def _recursive_split(
        self, text: str, separators: list[str], chunk_size: int
    ) -> list[str]:
        """Recursively split text using a list of separators."""
        if not text:
            return []

        # Approximate token count
        if len(text.split()) * 1.3 <= chunk_size:
            return [text]

        # Try each separator
        for sep in separators:
            parts = text.split(sep)
            if len(parts) > 1:
                result = []
                current = ""
                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate.split()) * 1.3 > chunk_size and current:
                        result.append(current)
                        current = part
                    else:
                        current = candidate
                if current:
                    result.append(current)
                return result

        # Fallback: hard split by words
        words = text.split()
        max_words = int(chunk_size / 1.3)
        return [
            " ".join(words[i : i + max_words])
            for i in range(0, len(words), max_words)
        ]

    def deduplicate_chunks(
        self, chunks: list[dict], threshold: float = 0.9
    ) -> list[dict]:
        """Remove duplicate or near-duplicate chunks."""
        seen_hashes = set()
        unique = []

        for chunk in chunks:
            content_hash = chunk["content_hash"]

            if content_hash in seen_hashes:
                continue

            # Fuzzy dedup on recent chunks
            if not self._is_near_duplicate(chunk, unique[-100:], threshold):
                unique.append(chunk)
                seen_hashes.add(content_hash)

        return unique

    def _is_near_duplicate(
        self, chunk: dict, existing: list[dict], threshold: float
    ) -> bool:
        """Check Jaccard similarity on character 3-grams."""
        if not existing:
            return False

        chunk_shingles = self._get_shingles(chunk["text"], n=3)

        for ex in existing:
            ex_shingles = self._get_shingles(ex["text"], n=3)
            if not chunk_shingles or not ex_shingles:
                continue
            jaccard = len(chunk_shingles & ex_shingles) / len(
                chunk_shingles | ex_shingles
            )
            if jaccard > threshold:
                return True

        return False

    @staticmethod
    def _get_shingles(text: str, n: int = 3) -> set:
        """Get character n-grams."""
        text = text.lower()
        return {text[i : i + n] for i in range(len(text) - n + 1)}
