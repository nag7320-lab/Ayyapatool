"""Agentic RAG system: 7 specialized agents for the RAG pipeline."""

import json
import logging
from datetime import datetime, timedelta
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class IntentClassificationAgent:
    """
    Agent 1: Classify user query into category and complexity.
    Uses few-shot prompting with Gemini Flash.
    """

    CATEGORIES = [
        "gst",
        "income_tax",
        "transfer_pricing",
        "nri_taxation",
        "expatriate_taxation",
        "corporate_law",
        "stpi",
        "esop_rsu",
        "international_tax",
        "general",
    ]

    # Keyword-based fast classification fallback
    KEYWORD_MAP = {
        "gst": ["gst", "gstin", "igst", "cgst", "sgst", "gstr", "input tax credit", "itc", "e-way bill"],
        "income_tax": ["income tax", "itr", "tds", "form 16", "80c", "80d", "tax slab", "advance tax"],
        "transfer_pricing": ["transfer pricing", "arm's length", "apa", "safe harbour"],
        "nri_taxation": ["nri", "non-resident", "dtaa", "fema", "remittance"],
        "expatriate_taxation": ["expatriate", "expat", "foreign national", "visa"],
        "corporate_law": ["companies act", "mca", "roc", "incorporation", "director"],
        "stpi": ["stpi", "sez", "export", "eis"],
        "esop_rsu": ["esop", "rsu", "stock option", "vesting"],
        "international_tax": ["foreign tax credit", "dtaa", "cross border", "pe"],
    }

    def classify(self, query: str, llm_client=None) -> dict:
        """Classify intent using keyword matching first, then LLM if needed."""
        # Fast path: keyword matching
        query_lower = query.lower()
        for category, keywords in self.KEYWORD_MAP.items():
            if any(kw in query_lower for kw in keywords):
                complexity = self._estimate_complexity(query_lower)
                return {
                    "category": category,
                    "complexity": complexity,
                    "confidence": 0.85,
                }

        # LLM classification
        if llm_client:
            return self._llm_classify(query, llm_client)

        return {"category": "general", "complexity": "medium", "confidence": 0.5}

    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity from length and keywords."""
        complex_indicators = [
            "how to", "explain", "compare", "difference", "implications",
            "what if", "scenario", "multiple", "combination",
        ]
        if len(query.split()) > 20 or any(ind in query for ind in complex_indicators):
            return "complex"
        if len(query.split()) > 10:
            return "medium"
        return "simple"

    def _llm_classify(self, query: str, llm_client) -> dict:
        """Use LLM for classification when keywords don't match."""
        prompt = f"""Classify this tax query into ONE category:
{', '.join(self.CATEGORIES)}

Rate complexity as: simple, medium, or complex.

Query: "{query}"

Respond ONLY with JSON: {{"category": "...", "complexity": "...", "confidence": 0.0-1.0}}"""

        try:
            response = llm_client.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {"category": "general", "complexity": "medium", "confidence": 0.5}


class MetadataFilterAgent:
    """
    Agent 2: Generate metadata filters based on intent.
    Narrows search space before retrieval.
    """

    TIME_KEYWORDS = ["current", "latest", "new", "recent", "now", "2025", "2026"]

    def generate_filters(self, query: str, intent: dict) -> dict:
        """Create metadata filters to narrow search scope."""
        filters = {"category": intent["category"]}

        # Date filter for time-sensitive queries
        if self._is_time_sensitive(query):
            filters["date_range"] = {
                "start": (datetime.now() - timedelta(days=730)).isoformat(),
                "end": datetime.now().isoformat(),
            }

        # Document type filters
        query_lower = query.lower()
        if "circular" in query_lower:
            filters["document_type"] = "circular"
        elif "notification" in query_lower:
            filters["document_type"] = "notification"
        elif any(w in query_lower for w in ["case", "judgment", "tribunal"]):
            filters["document_type"] = "case_law"

        return filters

    def _is_time_sensitive(self, query: str) -> bool:
        return any(kw in query.lower() for kw in self.TIME_KEYWORDS)


class ContextBuilderAgent:
    """
    Agent 5: Build LLM context from retrieved chunks.
    Enforces max 600 token context window.
    """

    MAX_CONTEXT_TOKENS = 600

    def build_context(self, chunks: list[dict], query: str) -> tuple[str, int]:
        """Format top chunks into LLM context with citations."""
        context_parts = []
        total_tokens = 0

        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            title = metadata.get("title", "Unknown")
            section = chunk.get("section_ref", "")
            date = metadata.get("issue_date", "")

            chunk_text = (
                f"[Source {i}: {title}"
                f"{', Section ' + section if section else ''}"
                f"{', Date: ' + date if date else ''}]\n"
                f"{chunk.get('text', '')}"
            )

            chunk_tokens = self._count_tokens(chunk_text)
            if total_tokens + chunk_tokens > self.MAX_CONTEXT_TOKENS:
                break

            context_parts.append(chunk_text)
            total_tokens += chunk_tokens

        return "\n\n".join(context_parts), total_tokens

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Approximate token count."""
        return int(len(text.split()) * 1.3)


class AnswerGenerationAgent:
    """
    Agent 6: Generate grounded answers using LLM.
    Supports streaming via SSE.
    """

    SYSTEM_PROMPT = """You are a professional tax advisor assistant for Aypa TaxAI.

Guidelines:
1. Answer ONLY based on the provided context
2. Cite sources using [Source X] notation
3. Be precise and professional
4. If context is insufficient, say so clearly
5. Use bullet points for multiple points
6. Keep answers concise (max 200 words)
7. Include relevant section numbers, dates, notifications

NEVER:
- Make up information not in context
- Provide tax advice without citing sources
- Give definitive answers if context is unclear"""

    MAX_ANSWER_TOKENS = 300

    def generate_answer(
        self, query: str, context: str, llm_client, stream: bool = True
    ) -> Generator[str, None, None] | str:
        """Generate answer, optionally streaming."""
        prompt = f"""Context:
{context}

User Question: {query}

Answer (cite sources):"""

        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"

        if stream:
            return self._stream_answer(full_prompt, llm_client)
        else:
            return self._generate_full(full_prompt, llm_client)

    def _stream_answer(self, prompt: str, llm_client) -> Generator[str, None, None]:
        """Stream response chunks."""
        try:
            response = llm_client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.MAX_ANSWER_TOKENS,
                    "temperature": 0.1,
                },
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"I apologize, but I encountered an error processing your query. Please try again."

    def _generate_full(self, prompt: str, llm_client) -> str:
        """Generate complete answer."""
        try:
            response = llm_client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.MAX_ANSWER_TOKENS,
                    "temperature": 0.1,
                },
            )
            return response.text
        except Exception as e:
            logger.error(f"Full generation failed: {e}")
            return "I apologize, but I encountered an error. Please try again."


class ConfidenceValidationAgent:
    """
    Agent 7: Calculate confidence and determine escalation.
    """

    CONFIDENCE_THRESHOLD = 0.7

    def calculate_confidence(
        self,
        query: str,
        retrieved_chunks: list[dict],
        answer: str,
    ) -> float:
        """
        Multi-factor confidence scoring.
        Factors: chunk similarity, support count, answer length, citations.
        """
        if not retrieved_chunks:
            return 0.0

        # Factor 1: Top chunk score (0-1)
        top_score = retrieved_chunks[0].get("fused_score", 0)
        similarity_score = min(top_score * 100, 1.0)  # Normalize RRF scores

        # Factor 2: Number of supporting chunks
        support_score = min(len(retrieved_chunks) / 3, 1.0)

        # Factor 3: Answer length appropriateness
        answer_words = len(answer.split())
        length_score = 1.0 if 20 <= answer_words <= 200 else 0.5

        # Factor 4: Source citations
        citation_score = 1.0 if "[Source" in answer else 0.3

        confidence = (
            0.40 * similarity_score
            + 0.25 * support_score
            + 0.15 * length_score
            + 0.20 * citation_score
        )

        return round(min(confidence, 1.0), 2)

    def should_escalate(self, confidence: float) -> bool:
        """Determine if query should be escalated to human expert."""
        return confidence < self.CONFIDENCE_THRESHOLD

    @staticmethod
    def get_escalation_message() -> str:
        return (
            "This query involves complex considerations. "
            "Would you like to speak with one of our expert tax advisors? "
            "They can provide personalized guidance for your specific situation."
        )


class TokenGovernor:
    """
    Enforce strict token limits across the RAG pipeline.
    Hard limit: 1300 tokens total.
    """

    LIMITS = {
        "system_prompt": 300,
        "context": 600,
        "user_query": 100,
        "answer": 300,
        "total": 1300,
    }

    def enforce_limits(self, components: dict) -> dict:
        """Truncate components to stay within budget."""
        result = {}

        for key in ["system_prompt", "context", "user_query"]:
            if key in components:
                result[key] = self._truncate_to_tokens(
                    components[key], self.LIMITS[key]
                )

        # Verify total
        total = sum(self._count_tokens(v) for v in result.values()) + self.LIMITS["answer"]
        if total > self.LIMITS["total"]:
            # Reduce context to fit
            overshoot = total - self.LIMITS["total"]
            context_tokens = self._count_tokens(result.get("context", ""))
            result["context"] = self._truncate_to_tokens(
                result.get("context", ""), context_tokens - overshoot
            )

        return result

    @staticmethod
    def _count_tokens(text: str) -> int:
        return int(len(text.split()) * 1.3)

    @staticmethod
    def _truncate_to_tokens(text: str, max_tokens: int) -> str:
        words = text.split()
        max_words = int(max_tokens / 1.3)
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."
