"""Tests for the Agentic RAG system."""

import pytest

from app.services.rag.agents import (
    ConfidenceValidationAgent,
    ContextBuilderAgent,
    IntentClassificationAgent,
    MetadataFilterAgent,
    TokenGovernor,
)


class TestIntentClassification:
    def test_gst_query(self):
        agent = IntentClassificationAgent()
        result = agent.classify("What is the GST rate on software services?")
        assert result["category"] == "gst"

    def test_income_tax_query(self):
        agent = IntentClassificationAgent()
        result = agent.classify("How to file ITR for FY 2025-26?")
        assert result["category"] == "income_tax"

    def test_esop_query(self):
        agent = IntentClassificationAgent()
        result = agent.classify("How are ESOP gains taxed in India?")
        assert result["category"] == "esop_rsu"

    def test_general_query(self):
        agent = IntentClassificationAgent()
        result = agent.classify("Hello, how can you help?")
        assert result["category"] == "general"

    def test_complexity_estimation(self):
        agent = IntentClassificationAgent()
        assert agent._estimate_complexity("what is gst") == "simple"
        assert agent._estimate_complexity("explain the implications of transfer pricing on cross-border transactions") == "complex"


class TestMetadataFilter:
    def test_basic_filter(self):
        agent = MetadataFilterAgent()
        filters = agent.generate_filters(
            "GST rate on IT services",
            {"category": "gst"}
        )
        assert filters["category"] == "gst"

    def test_time_sensitive(self):
        agent = MetadataFilterAgent()
        filters = agent.generate_filters(
            "What are the latest GST changes in 2026?",
            {"category": "gst"}
        )
        assert "date_range" in filters


class TestTokenGovernor:
    def test_within_limits(self):
        gov = TokenGovernor()
        result = gov.enforce_limits({
            "system_prompt": "You are a tax advisor.",
            "context": "Some context here.",
            "user_query": "What is GST?",
        })
        total = sum(gov._count_tokens(v) for v in result.values()) + gov.LIMITS["answer"]
        assert total <= gov.LIMITS["total"]

    def test_truncation(self):
        gov = TokenGovernor()
        long_text = " ".join(["word"] * 1000)
        result = gov.enforce_limits({
            "system_prompt": "Short.",
            "context": long_text,
            "user_query": "Short query.",
        })
        context_tokens = gov._count_tokens(result["context"])
        assert context_tokens <= gov.LIMITS["context"]


class TestConfidenceValidation:
    def test_high_confidence(self):
        agent = ConfidenceValidationAgent()
        chunks = [{"fused_score": 0.015}]  # RRF scores are typically small
        answer = "GST rate on software is 18%. [Source 1] This applies to all IT services."
        confidence = agent.calculate_confidence("GST rate?", chunks, answer)
        assert 0 <= confidence <= 1

    def test_no_chunks(self):
        agent = ConfidenceValidationAgent()
        assert agent.calculate_confidence("query", [], "answer") == 0

    def test_escalation_threshold(self):
        agent = ConfidenceValidationAgent()
        assert agent.should_escalate(0.5) is True
        assert agent.should_escalate(0.8) is False
