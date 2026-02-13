# AYPA TAXAI - COMPLETE PRD SUITE

**Version:** 1.0
**Date:** February 13, 2026

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 1 | [Executive Summary & Architecture](01_EXECUTIVE_SUMMARY_AND_ARCHITECTURE.md) | Vision, target market, tech stack, design principles, NFRs |
| 2 | [Agentic RAG System Specs](02_AGENTIC_RAG_SYSTEM_SPECS.md) | 7-agent pipeline, hybrid search, embeddings, caching, token governance |
| 3 | [Invoice, Tax & Payroll Guide](03_INVOICE_TAX_PAYROLL_COMPLETE_GUIDE.md) | GST invoicing (6 types), tax calculators, payroll system |
| 4 | [Implementation & Deployment](04_IMPLEMENTATION_DEPLOYMENT_GUIDE.md) | 17-week plan, AWS deployment, CI/CD, monitoring |

---

## Quick Start

| Role | Start With |
|------|-----------|
| Product Managers | Document 1 (Executive Summary) |
| Engineers | Documents 1 → 4 → 2/3 |
| Designers | Document 1 (Design Principles) |
| Stakeholders | Document 1 (Summary & Metrics) |

---

## Key Highlights

- **Enterprise-Grade Agentic RAG** with hybrid search, 384-dim embeddings, <2s response
- **6 GST Invoice Types** with 12+ templates, bulk generation, GSTR-1 export
- **Income Tax Calculator** with old vs new regime comparison, Form 16 parsing
- **Full Payroll System** with PF, ESI, PT, TDS compliance for 20-50 employees
- **Production-Ready** with Docker, Terraform, CI/CD, 99.9% uptime target

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TailwindCSS, Framer Motion |
| Backend | Python 3.11+, Flask 3.0, Celery |
| AI | Gemini 1.5 Flash/Pro, sentence-transformers, FAISS, BM25 |
| Database | PostgreSQL 15, Redis 7, MinIO/S3 |
| Infrastructure | AWS ECS, Docker, Terraform, GitHub Actions |

## Support

**Company:** Aypa TaxAI
**Locations:** Hyderabad, Bangalore, Visakhapatnam
**Website:** aypa.taxai
