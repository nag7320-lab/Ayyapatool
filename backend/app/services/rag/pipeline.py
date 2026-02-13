"""Complete Agentic RAG pipeline orchestrator."""

import json
import logging
import time
from typing import Generator, Optional

from app.services.rag.agents import (
    AnswerGenerationAgent,
    ConfidenceValidationAgent,
    ContextBuilderAgent,
    IntentClassificationAgent,
    MetadataFilterAgent,
    TokenGovernor,
)
from app.services.rag.cache import RAGCacheManager
from app.services.rag.search import HybridSearchEngine

logger = logging.getLogger(__name__)

# Disclaimer appended to every AI response
DISCLAIMER = (
    "\n\n---\n"
    "This information is for general guidance only and should not be considered as "
    "professional tax or legal advice. Please consult a qualified professional for "
    "your specific situation."
)


class RAGPipeline:
    """
    Orchestrates the 7-agent RAG pipeline:
    1. Intent Classification
    2. Metadata Filtering
    3. Hybrid Retrieval (BM25 + Vector, parallel)
    4. Re-Ranking (RRF)
    5. Context Building
    6. Answer Generation (streaming)
    7. Confidence Validation
    """

    def __init__(self, config: dict, redis_client=None, llm_client=None):
        self.config = config

        # Agents
        self.intent_agent = IntentClassificationAgent()
        self.filter_agent = MetadataFilterAgent()
        self.context_agent = ContextBuilderAgent()
        self.answer_agent = AnswerGenerationAgent()
        self.confidence_agent = ConfidenceValidationAgent()
        self.token_governor = TokenGovernor()

        # Search engine
        self.search_engine = HybridSearchEngine(
            bm25_weight=config.get("RAG_BM25_WEIGHT", 0.4),
            vector_weight=config.get("RAG_VECTOR_WEIGHT", 0.6),
            rrf_k=config.get("RAG_RRF_K", 60),
        )

        # Cache
        self.cache = None
        if redis_client:
            self.cache = RAGCacheManager(redis_client, config)

        # LLM client
        self.llm_client = llm_client

    def process_query_stream(
        self, query: str, category: Optional[str] = None, user_id: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Process a user query through the full RAG pipeline with SSE streaming.
        Yields JSON-encoded SSE data events.
        """
        start_time = time.time()

        try:
            # Step 1: Intent classification
            if category:
                intent = {"category": category, "complexity": "medium", "confidence": 0.9}
            else:
                intent = self.intent_agent.classify(query, self.llm_client)
            yield self._sse_event("intent", intent)

            # Step 2: Metadata filtering
            filters = self.filter_agent.generate_filters(query, intent)

            # Step 3: Check cache for chunks
            chunks = None
            if self.cache:
                chunks = self.cache.get_cached_chunks(query, filters)

            # Step 4: Hybrid search if no cache hit
            if not chunks:
                chunks = self.search_engine.search(query, filters, top_k=3)
                if self.cache and chunks:
                    self.cache.cache_chunks(query, filters, chunks)

            if not chunks:
                yield self._sse_event("chunk", {
                    "content": "I couldn't find relevant information in our knowledge base for your query. "
                    "Please try rephrasing or contact our tax advisors for assistance."
                })
                yield self._sse_event("done", {"confidence": 0.0, "sources": []})
                return

            # Step 5: Build context
            context, context_tokens = self.context_agent.build_context(chunks, query)

            # Step 6: Enforce token limits
            components = self.token_governor.enforce_limits({
                "system_prompt": self.answer_agent.SYSTEM_PROMPT,
                "context": context,
                "user_query": query,
            })

            # Step 7: Generate streaming answer
            full_answer = ""
            if self.llm_client:
                for text_chunk in self.answer_agent.generate_answer(
                    query, components["context"], self.llm_client, stream=True
                ):
                    full_answer += text_chunk
                    yield self._sse_event("chunk", {"content": text_chunk})
            else:
                # Fallback: return context summary if no LLM available
                fallback = f"Based on our knowledge base:\n\n{context[:500]}"
                full_answer = fallback
                yield self._sse_event("chunk", {"content": fallback})

            # Append disclaimer
            yield self._sse_event("chunk", {"content": DISCLAIMER})
            full_answer += DISCLAIMER

            # Step 8: Confidence validation
            confidence = self.confidence_agent.calculate_confidence(
                query, chunks, full_answer
            )

            sources = [
                {
                    "title": c.get("metadata", {}).get("title", "Unknown"),
                    "date": c.get("metadata", {}).get("issue_date", ""),
                }
                for c in chunks
            ]

            result = {
                "confidence": confidence,
                "sources": sources,
                "response_time_ms": int((time.time() - start_time) * 1000),
            }

            if self.confidence_agent.should_escalate(confidence):
                result["escalation_message"] = self.confidence_agent.get_escalation_message()

            yield self._sse_event("done", result)

            # Cache the answer
            if self.cache:
                import hashlib
                ctx_hash = hashlib.md5(context.encode()).hexdigest()
                self.cache.cache_answer(query, ctx_hash, full_answer, confidence)

        except Exception as e:
            logger.error(f"RAG pipeline error: {e}", exc_info=True)
            yield self._sse_event("error", {"message": "An error occurred processing your query. Please try again."})

    def process_query(
        self, query: str, category: Optional[str] = None
    ) -> dict:
        """Non-streaming version for testing and internal use."""
        events = list(self.process_query_stream(query, category))

        answer_parts = []
        result = {}
        for event_str in events:
            # Parse SSE data
            data_line = event_str.strip()
            if data_line.startswith("data: "):
                data = json.loads(data_line[6:])
                if data.get("type") == "chunk":
                    answer_parts.append(data.get("content", ""))
                elif data.get("type") == "done":
                    result = data
                elif data.get("type") == "error":
                    return {"error": data.get("message"), "answer": "", "confidence": 0}

        result["answer"] = "".join(answer_parts)
        return result

    @staticmethod
    def _sse_event(event_type: str, data: dict) -> str:
        """Format as SSE data line."""
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload)}\n\n"
