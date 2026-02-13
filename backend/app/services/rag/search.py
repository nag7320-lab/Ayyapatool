"""Hybrid search engine: BM25 + FAISS vector with Reciprocal Rank Fusion."""

import logging
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class BM25SearchEngine:
    """BM25 keyword search engine."""

    IMPORTANT_TERMS = {"not", "no", "none", "nil"}
    STOPWORDS = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for"} - IMPORTANT_TERMS

    def __init__(self):
        self.index = None
        self.chunk_ids: list[str] = []
        self.chunk_data: dict[str, dict] = {}

    def build_index(self, chunks: list[dict]):
        """Build BM25 index from chunks."""
        from rank_bm25 import BM25Okapi

        tokenized_corpus = [self._tokenize(c["text"]) for c in chunks]
        self.index = BM25Okapi(tokenized_corpus)
        self.chunk_ids = [c["chunk_id"] for c in chunks]
        self.chunk_data = {c["chunk_id"]: c for c in chunks}

    def save_index(self, path: str):
        """Persist BM25 index to disk."""
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "index": self.index,
                    "chunk_ids": self.chunk_ids,
                    "chunk_data": self.chunk_data,
                },
                f,
            )

    def load_index(self, path: str):
        """Load BM25 index from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.index = data["index"]
            self.chunk_ids = data["chunk_ids"]
            self.chunk_data = data["chunk_data"]

    def search(
        self, query: str, filters: Optional[dict] = None, top_k: int = 10
    ) -> list[dict]:
        """Search using BM25."""
        if self.index is None:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.index.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk_id = self.chunk_ids[idx]
                result = {
                    "chunk_id": chunk_id,
                    "score": float(scores[idx]),
                    "rank": len(results) + 1,
                    **self.chunk_data.get(chunk_id, {}),
                }
                results.append(result)

        if filters:
            results = self._apply_filters(results, filters)

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text for BM25."""
        import re

        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        return [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]

    def _apply_filters(self, results: list[dict], filters: dict) -> list[dict]:
        """Apply metadata filters to results."""
        filtered = []
        for r in results:
            metadata = r.get("metadata", {})
            match = True
            for key, value in filters.items():
                if key == "category" and metadata.get("category") != value:
                    match = False
                    break
                if key == "document_type" and metadata.get("document_type") != value:
                    match = False
                    break
            if match:
                filtered.append(r)
        return filtered


class VectorSearchEngine:
    """FAISS vector similarity search engine."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.chunk_ids: list[str] = []
        self.chunk_data: dict[str, dict] = {}

    def build_index(self, chunks: list[dict], embeddings: np.ndarray):
        """Build FAISS index with IVF+PQ quantization."""
        import faiss

        self.chunk_ids = [c["chunk_id"] for c in chunks]
        self.chunk_data = {c["chunk_id"]: c for c in chunks}

        n_vectors = len(embeddings)

        if n_vectors < 100:
            # Simple flat index for small datasets
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings.astype(np.float32))
        else:
            # IVF+PQ for larger datasets
            nlist = min(100, n_vectors // 10)
            quantizer = faiss.IndexFlatL2(self.dimension)
            m = min(8, self.dimension)
            self.index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, m, 8)
            self.index.train(embeddings.astype(np.float32))
            self.index.add(embeddings.astype(np.float32))
            self.index.nprobe = min(10, nlist)

    def save_index(self, path: str):
        """Save FAISS index to disk."""
        import faiss

        if self.index is not None:
            faiss.write_index(self.index, path)
            meta_path = path + ".meta"
            with open(meta_path, "wb") as f:
                pickle.dump(
                    {"chunk_ids": self.chunk_ids, "chunk_data": self.chunk_data}, f
                )

    def load_index(self, path: str):
        """Load FAISS index from disk."""
        import faiss

        if os.path.exists(path):
            self.index = faiss.read_index(path)
            meta_path = path + ".meta"
            if os.path.exists(meta_path):
                with open(meta_path, "rb") as f:
                    meta = pickle.load(f)
                    self.chunk_ids = meta["chunk_ids"]
                    self.chunk_data = meta["chunk_data"]

    def search(
        self,
        query_embedding: np.ndarray,
        filters: Optional[dict] = None,
        top_k: int = 10,
    ) -> list[dict]:
        """Vector similarity search."""
        if self.index is None:
            return []

        distances, indices = self.index.search(
            query_embedding.reshape(1, -1).astype(np.float32), top_k
        )

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.chunk_ids):
                similarity = 1 / (1 + dist)
                chunk_id = self.chunk_ids[idx]
                result = {
                    "chunk_id": chunk_id,
                    "score": float(similarity),
                    "rank": len(results) + 1,
                    **self.chunk_data.get(chunk_id, {}),
                }
                results.append(result)

        if filters:
            results = self._apply_filters(results, filters)

        return results

    def _apply_filters(self, results: list[dict], filters: dict) -> list[dict]:
        """Apply metadata filters."""
        filtered = []
        for r in results:
            metadata = r.get("metadata", {})
            match = True
            for key, value in filters.items():
                if key == "category" and metadata.get("category") != value:
                    match = False
                    break
            if match:
                filtered.append(r)
        return filtered


class HybridSearchEngine:
    """
    Parallel hybrid search with Reciprocal Rank Fusion (RRF).
    Combines BM25 keyword search and FAISS vector search.
    """

    def __init__(
        self,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60,
    ):
        self.bm25_engine = BM25SearchEngine()
        self.vector_engine = VectorSearchEngine()
        self.embedding_pipeline = None  # Set externally
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k

    def search(
        self, query: str, filters: Optional[dict] = None, top_k: int = 3
    ) -> list[dict]:
        """Parallel hybrid search with RRF fusion."""
        if self.embedding_pipeline is None:
            from app.services.rag.embeddings import EmbeddingPipeline

            self.embedding_pipeline = EmbeddingPipeline()

        query_embedding = self.embedding_pipeline.encode_query(query)

        # Parallel execution
        with ThreadPoolExecutor(max_workers=2) as executor:
            bm25_future = executor.submit(
                self.bm25_engine.search, query, filters, top_k=10
            )
            vector_future = executor.submit(
                self.vector_engine.search, query_embedding, filters, top_k=10
            )

        bm25_results = bm25_future.result()
        vector_results = vector_future.result()

        # Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(bm25_results, vector_results)

        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self, bm25_results: list[dict], vector_results: list[dict]
    ) -> list[dict]:
        """
        Combine results using RRF.
        Score = sum(weight / (k + rank))
        """
        scores: dict[str, float] = {}
        chunk_data: dict[str, dict] = {}

        for result in bm25_results:
            cid = result["chunk_id"]
            scores[cid] = scores.get(cid, 0) + self.bm25_weight / (
                self.rrf_k + result["rank"]
            )
            chunk_data[cid] = result

        for result in vector_results:
            cid = result["chunk_id"]
            scores[cid] = scores.get(cid, 0) + self.vector_weight / (
                self.rrf_k + result["rank"]
            )
            if cid not in chunk_data:
                chunk_data[cid] = result

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        final = []
        for chunk_id, score in sorted_results:
            data = chunk_data[chunk_id].copy()
            data["fused_score"] = score
            final.append(data)

        return final
