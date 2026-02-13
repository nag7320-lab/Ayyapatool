# AYPA TAXAI - Agentic RAG System Specifications

## Part 2: Detailed Technical Specifications

**Document Version:** 1.0
**Date:** February 13, 2026

---

## 1. Overview

The Agentic RAG system is the core intelligence layer of Aypa TaxAI, featuring:

- 7 specialized agents in a pipeline architecture
- Hybrid search (BM25 + FAISS Vector with RRF fusion)
- 384-dim embeddings with INT8 quantization (75% storage savings)
- Multi-layer caching (embedding, chunk, answer)
- Token governance (1300 token hard limit)
- Streaming responses via SSE
- <2s end-to-end response time

## 2. Agent Architecture

```
User Query → Agent 1 (Intent) → Agent 2 (Filters) → Agent 3 (Hybrid Search)
          → Agent 4 (RRF Re-Ranking) → Agent 5 (Context Builder)
          → Agent 6 (Answer Generation) → Agent 7 (Confidence) → Response
```

### Agent 1: Intent Classification
- Categorizes queries into 10 tax domains (GST, Income Tax, Transfer Pricing, etc.)
- Rates complexity: simple, medium, complex
- Fast-path keyword matching + LLM fallback

### Agent 2: Metadata Filtering
- Generates search filters based on intent
- Time-sensitive query detection
- Document type filtering (circulars, notifications, case laws)

### Agent 3: Hybrid Retrieval
- **BM25 Search:** Keyword matching with tokenization, stopword handling
- **Vector Search:** FAISS with IVF+PQ quantization
- Parallel execution via ThreadPoolExecutor
- Top-10 results from each engine

### Agent 4: Re-Ranking (Reciprocal Rank Fusion)
- Formula: `Score = 0.4 × BM25_weight/(k + rank) + 0.6 × Vector_weight/(k + rank)`
- RRF constant k = 60
- Output: Top-3 chunks only

### Agent 5: Context Builder
- Extracts top-3 chunks with citations
- Formats for LLM consumption
- Max 600 tokens context window

### Agent 6: Answer Generation
- Primary LLM: Gemini 1.5 Flash (cost-optimized)
- Fallback: Gemini 1.5 Pro (complex queries)
- Temperature: 0.1 (factual responses)
- Max 300 tokens output
- Streaming via SSE

### Agent 7: Confidence Validation
- Multi-factor scoring: similarity (40%), support (25%), length (15%), citations (20%)
- Threshold: 0.7
- Below threshold: "Speak to Expert" escalation

## 3. Embedding Strategy

| Property | Value |
|----------|-------|
| Model | sentence-transformers/all-MiniLM-L6-v2 |
| Dimensions | 384 |
| Quantization | INT8 |
| Storage/Million | ~1.5GB (vs ~6GB for ada-002) |
| Inference Speed | ~400 sentences/sec (CPU) |

### Chunking Configuration
- Chunk size: 500 tokens
- Overlap: 100 tokens
- Min chunk: 100 tokens
- Hierarchical: Section → Subsection → Paragraph
- Deduplication: MD5 hash + Jaccard similarity (threshold 0.9)

## 4. Knowledge Base

### Categories (10 domains)
1. GST (circulars, notifications, case laws, FAQs, guides)
2. Income Tax (IT Act, circulars, forms)
3. Transfer Pricing
4. NRI Taxation (DTAA, FEMA)
5. Expatriate Taxation
6. Corporate Law (Companies Act, MCA)
7. STPI/SEZ
8. ESOP/RSU
9. International Tax
10. Internal SOPs

### Target: 10GB+ documents, 1M+ embeddings

## 5. Caching Strategy

| Layer | TTL | Purpose |
|-------|-----|---------|
| Query Embeddings | 1 hour | Avoid recomputation |
| Retrieved Chunks | 5 min | Avoid search overhead |
| Final Answers | 5 min | Serve identical queries |

Target cache hit rate: >60%

## 6. Token Governance

| Component | Budget |
|-----------|--------|
| System Prompt | 300 tokens |
| Context | 600 tokens |
| User Query | 100 tokens |
| Answer | 300 tokens |
| **Total** | **1300 tokens** |

## 7. Performance Targets

| Metric | Target |
|--------|--------|
| First Token Latency | <1s |
| Full Response Time | <2s |
| Embedding Inference | <50ms |
| Vector Search | <100ms (1M vectors) |
| BM25 Search | <50ms |
| Cache Hit Rate | >60% |
| Confidence Score | >0.8 avg |

## 8. API

### POST /api/chat/message
- SSE streaming endpoint
- JWT authenticated, rate limited (100/hour)
- Events: `intent`, `chunk`, `citation`, `done`, `error`

### POST /api/knowledge/upload
- Admin-only document upload
- Queued processing via Celery
- Supports PDF, DOCX, TXT

---

*Implementation: See `backend/app/services/rag/`*
