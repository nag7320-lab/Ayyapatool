# Aypa TaxAI

**Smart Tax Solutions for Modern Businesses**

Enterprise-grade, AI-powered tax advisory and compliance platform for IT firms, startups, and SMEs across India.

## Features

- **AI Tax Advisor** - Agentic RAG system with hybrid search (BM25 + Vector), streaming responses
- **GST Invoice Generator** - 6 invoice types, 12+ templates, bulk generation, GSTR-1 export
- **Income Tax Calculator** - Old vs New regime comparison, Form 16 upload, professional reports
- **Payroll System** - India-compliant (PF, ESI, PT, TDS), 20-50 employees, Full & Final settlement

## Architecture

```
Frontend (Next.js 14) → API Gateway (Flask) → Services
                                                ├── Agentic RAG (7 agents)
                                                ├── Invoice Generator
                                                ├── Tax Calculator
                                                └── Payroll Engine
                                                    ↓
                                        PostgreSQL │ Redis │ FAISS │ S3
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS, Framer Motion |
| Backend | Python 3.11+, Flask 3.0, Celery, SQLAlchemy |
| AI/Search | Gemini 1.5, sentence-transformers, FAISS, BM25 |
| Database | PostgreSQL 15, Redis 7 |
| Infrastructure | Docker, Terraform, AWS, GitHub Actions |
| Deployment | Vercel (frontend), Railway (backend) — or AWS |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your environment
flask db upgrade
python wsgi.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker (Recommended)

```bash
docker-compose up -d
```

Visit: http://localhost:3000 (Frontend) | http://localhost:5000/api/health (API)

## Project Structure

```
Ayyapatool/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API blueprints
│   │   ├── models/       # Database models
│   │   ├── services/
│   │   │   ├── rag/      # Agentic RAG system (7 agents)
│   │   │   ├── invoice/  # GST invoice generator
│   │   │   ├── tax/      # Tax calculators
│   │   │   └── payroll/  # Payroll engine
│   │   └── utils/
│   ├── tests/
│   ├── knowledge_base/   # RAG knowledge base documents
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   ├── lib/          # API client, utilities
│   │   ├── store/        # Zustand state management
│   │   └── types/        # TypeScript interfaces
│   └── package.json
├── infrastructure/
│   ├── docker/           # Dockerfiles, nginx config
│   └── terraform/        # AWS infrastructure as code
├── docs/                 # PRD suite (4 documents)
├── docker-compose.yml
└── .github/workflows/    # CI/CD pipelines
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | User registration |
| POST | /api/auth/login | User login |
| POST | /api/chat/message | AI advisor (SSE streaming) |
| POST | /api/invoices/ | Create invoice |
| GET | /api/invoices/ | List invoices |
| GET | /api/invoices/:id/pdf | Download PDF |
| POST | /api/invoices/bulk | Bulk generation |
| GET | /api/invoices/gstr1-export | GSTR-1 export |
| POST | /api/tax/compute | Compute tax (both regimes) |
| POST | /api/tax/form16-upload | Parse Form 16 |
| POST | /api/payroll/run | Run payroll |
| GET | /api/payroll/payslips | List payslips |
| POST | /api/payroll/fnf | Full & Final settlement |

## Deploy to Vercel + Railway (Quick Test)

The fastest way to get the app live for testing — **no AWS required**.

### Step 1: Deploy Backend on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"** → Select this repo
3. Set the **Root Directory** to `backend`
4. Railway auto-detects the `Procfile`. Add these services:
   - Click **"+ New"** → **"Database"** → **PostgreSQL** (free tier available)
   - Click **"+ New"** → **"Database"** → **Redis** (free tier available)
5. Railway auto-sets `DATABASE_URL` and `REDIS_URL`. Add these environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-a-random-64-char-string>
   JWT_SECRET_KEY=<generate-another-random-64-char-string>
   GOOGLE_API_KEY=<your-gemini-api-key>
   CORS_ORIGINS=https://your-app.vercel.app
   ```
6. Click **Deploy** — Railway builds and runs the backend
7. Copy the Railway public URL (e.g., `https://aypa-backend-production.up.railway.app`)

**After deploy, initialize the database:**
```bash
# Using Railway CLI
npm install -g @railway/cli
railway login
railway link
railway run flask db upgrade
```

### Step 2: Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"** → Import this repo
3. Set **Root Directory** to `frontend`
4. Set **Framework Preset** to `Next.js`
5. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend-url.up.railway.app/api
   NEXT_PUBLIC_WS_URL=https://your-railway-backend-url.up.railway.app
   ```
6. Click **Deploy**

### Step 3: Connect & Test

1. Update Railway's `CORS_ORIGINS` to your Vercel URL: `https://your-app.vercel.app`
2. Visit your Vercel URL and test:
   - Register a new account
   - Try the AI Tax Advisor
   - Create a GST invoice
   - Run a tax comparison

### Estimated Costs (Testing)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Railway (Backend + DB + Redis) | $5 free credit/month | ~$5-10/month |
| Vercel (Frontend) | Free for hobby | $20/month (Pro) |
| Google Gemini API | Free tier (60 req/min) | Pay-as-you-go |
| **Total for testing** | **$0-5/month** | **~$25-30/month** |

### Upgrading to AWS Production

When you're ready to go live at scale, use the existing Terraform configs:
```bash
cd infrastructure/terraform
terraform init && terraform apply
```

See the [Implementation & Deployment Guide](docs/04_IMPLEMENTATION_DEPLOYMENT_GUIDE.md) for full AWS setup.

---

## Documentation

See the [PRD Suite](docs/PRD_INDEX.md) for complete product requirements:

1. [Executive Summary & Architecture](docs/01_EXECUTIVE_SUMMARY_AND_ARCHITECTURE.md)
2. [Agentic RAG System Specs](docs/02_AGENTIC_RAG_SYSTEM_SPECS.md)
3. [Invoice, Tax & Payroll Guide](docs/03_INVOICE_TAX_PAYROLL_COMPLETE_GUIDE.md)
4. [Implementation & Deployment](docs/04_IMPLEMENTATION_DEPLOYMENT_GUIDE.md)

## License

Proprietary - Aypa TaxAI

## Contact

**Company:** Aypa TaxAI
**Locations:** Hyderabad, Bangalore, Visakhapatnam
**Website:** aypa.taxai
