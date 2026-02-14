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
| Infrastructure | Docker, Terraform, AWS |

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
│   ├── terraform/        # AWS production infrastructure (ECS, RDS, etc.)
│   └── terraform-lite/   # AWS minimal-cost setup (single EC2)
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

## Deploy to AWS (Minimal Cost - ~$10-15/month)

One-command deployment to a single EC2 instance running docker-compose.

### Prerequisites

1. **AWS Account** with CLI configured: `aws configure`
2. **Terraform** installed: [Install Terraform](https://developer.hashicorp.com/terraform/install)
3. **Google Gemini API key** (optional): [Get API Key](https://aistudio.google.com/apikey)

### Option A: One-Command Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Ask for your config (region, instance size, API keys)
- Generate secure passwords automatically
- Provision an EC2 instance on AWS
- Install Docker and deploy the full app
- Output the URL and SSH access details

### Option B: Manual Terraform Deploy

```bash
cd infrastructure/terraform-lite
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

After deploy, SSH in and monitor the setup:
```bash
ssh -i aypa-key.pem ec2-user@<public-ip>
tail -f /var/log/aypa-setup.log         # Monitor setup progress
sudo docker compose -f /opt/aypa/docker-compose.yml logs -f  # App logs
```

### Instance Sizing

| Instance | vCPU | RAM | Monthly Cost | Best For |
|----------|------|-----|-------------|----------|
| t2.micro | 1 | 1 GB | **FREE** (if eligible) | Quick demo |
| t3.micro | 2 | 1 GB | ~$8/month | Light testing |
| t3.small | 2 | 2 GB | ~$15/month | **Recommended for testing** |
| t3.medium | 2 | 4 GB | ~$30/month | Heavier testing with AI |

### To Stop Billing

```bash
cd infrastructure/terraform-lite
terraform destroy    # Removes everything
```

### Upgrading to Production

When ready for production scale, use the full infrastructure setup:
```bash
cd infrastructure/terraform
terraform init && terraform apply
```
This provisions VPC, ECS Fargate, RDS, ElastiCache, ALB, S3, auto-scaling.

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
