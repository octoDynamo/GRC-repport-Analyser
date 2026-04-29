<div align="center">

# 🛡️ GRC AI Analyzer

**Automated Governance, Risk & Compliance Report Analysis Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-mistral--large-FF7000?style=for-the-badge&logo=mistral&logoColor=white)](https://mistral.ai)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> An intelligent, AI-powered platform that automatically analyzes GRC (Governance, Risk & Compliance) reports, identifies risks, evaluates regulatory compliance, and generates prioritized action plans — all through a modern web interface.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Getting Started](#-getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Start Infrastructure (Docker)](#3-start-infrastructure-docker)
  - [4. Set Up the Backend](#4-set-up-the-backend)
  - [5. Set Up the Frontend](#5-set-up-the-frontend)
- [API Reference](#-api-reference)
- [Data Models](#-data-models)
- [AI Pipeline](#-ai-pipeline)
- [Environment Variables Reference](#-environment-variables-reference)
- [Development Guide](#-development-guide)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**GRC AI Analyzer** is a final-year engineering project (PFE) that addresses the challenge of manual GRC report analysis. Organizations dealing with Governance, Risk & Compliance documentation — ISO 27001, GDPR, Morocco's Law 09-08 — typically require significant human expertise and time to process these documents.

This platform automates the full analysis pipeline:

1. **Document ingestion** — Upload PDF, DOCX, or XLSX reports
2. **AI extraction** — Mistral AI reads, understands, and extracts structured GRC data
3. **Risk scoring** — Automatic scoring using Probability × Impact matrices
4. **Compliance audit** — Simultaneous evaluation against ISO 27001, GDPR, and Law 09-08
5. **Action plans** — Prioritized recommendations (Quick Wins, Medium-term, Long-term)
6. **RAG Chat** — An intelligent assistant that answers questions based solely on the analyzed report
7. **Export** — Download analysis results as PDF or Excel reports

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 **Multi-format Upload** | Supports PDF, DOCX, and XLSX document formats |
| 🤖 **AI Risk Extraction** | Identifies risks (CYBER, OPERATIONAL, FINANCIAL, LEGAL, STRATEGIC) with automatic scoring |
| ✅ **Compliance Audit** | Evaluates conformity against ISO 27001, GDPR, and Morocco's Law 09-08 simultaneously |
| 📊 **Interactive Dashboard** | Risk matrices, compliance radar charts, and trend visualizations |
| 💬 **RAG Chat Assistant** | Ask natural language questions contextualized to the specific analyzed report |
| 📁 **Action Plan Generation** | Generates prioritized recommendations with effort/impact scoring |
| 📥 **Report Export** | Download full analysis as PDF (ReportLab) or Excel (XlsxWriter) |
| 🔐 **JWT Authentication** | Secure user authentication with token-based sessions |
| 🗂️ **Report History** | Browse, filter, and revisit all previously analyzed reports |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Browser                         │
│              React 18 + Vite + TypeScript + Tailwind CSS        │
│         (Dashboard · Reports · Analysis · Login pages)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP / REST (Axios)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                           │
│                    (Python 3.11 · Uvicorn)                      │
│  ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐  │
│  │  /auth    │ │  /rapports  │ │ /analyses │ │  /chat      │  │
│  │  /export  │ │  /recomm..  │ └───────────┘ └─────────────┘  │
│  └───────────┘ └─────────────┘                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    AI Layer                              │   │
│  │  Mistral Client → Prompts → Document Parser → RAG Engine │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────┬──────────────┬─────────────────┬────────────────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌──────────────┐ ┌──────────┐   ┌───────────────┐
│  PostgreSQL  │ │  MinIO   │   │   ChromaDB    │
│  (Metadata & │ │(Document │   │ (Vector Store │
│   Analysis  )│ │ Storage) │   │   for RAG)    │
└──────────────┘ └──────────┘   └───────────────┘
```

### Component Roles

| Component | Role |
|---|---|
| **FastAPI** | REST API server, business logic orchestration, JWT auth |
| **PostgreSQL** | Persistent storage for users, reports, analyses, risks, compliance, recommendations |
| **MinIO** | S3-compatible object storage for uploaded document files |
| **ChromaDB** | Vector database for storing document embeddings (RAG pipeline) |
| **Mistral AI** | LLM for document understanding, risk extraction, and chat responses |
| **Sentence-Transformers** | Local embeddings model for document chunking and vectorization |

---

## 🧰 Tech Stack

### Backend
| Library | Version | Purpose |
|---|---|---|
| `fastapi` | ≥ 0.115 | Async REST framework |
| `uvicorn` | ≥ 0.30 | ASGI server |
| `sqlalchemy[asyncio]` | ≥ 2.0 | Async ORM |
| `asyncpg` | ≥ 0.29 | PostgreSQL async driver |
| `alembic` | ≥ 1.13 | Database migrations |
| `pydantic` / `pydantic-settings` | ≥ 2.9 | Data validation & config |
| `python-jose` | ≥ 3.3 | JWT token generation |
| `passlib[bcrypt]` | ≥ 1.7 | Password hashing |
| `mistralai` | ≥ 1.1 | Mistral AI API client |
| `sentence-transformers` | ≥ 3.0 | Local text embeddings |
| `chromadb` | ≥ 0.5 | Vector store client |
| `minio` | ≥ 7.2 | S3-compatible storage client |
| `pypdf2`, `python-docx`, `openpyxl`, `PyMuPDF` | Latest | Document parsing (PDF/DOCX/XLSX) |
| `reportlab` | ≥ 4.2 | PDF export generation |
| `xlsxwriter` | ≥ 3.2 | Excel export generation |
| `loguru` | ≥ 0.7 | Structured logging |

### Frontend
| Library | Version | Purpose |
|---|---|---|
| `react` | 18 | UI framework |
| `vite` | ≥ 7.0 | Build tool & dev server |
| `typescript` | ~5.9 | Type safety |
| `tailwindcss` | ≥ 4.2 | Utility-first styling |
| `zustand` | ≥ 5.0 | Lightweight global state |
| `axios` | ≥ 1.13 | HTTP client |
| `react-router-dom` | ≥ 7.0 | Client-side routing |
| `recharts` | ≥ 3.7 | Charts & data visualization |
| `@radix-ui/*` | Latest | Accessible UI primitives |
| `lucide-react` | Latest | Icon library |
| `date-fns` | ≥ 4.0 | Date formatting utilities |

### Infrastructure
| Service | Image | Purpose |
|---|---|---|
| PostgreSQL | `postgres:15-alpine` | Relational database |
| MinIO | `minio/minio:latest` | Object storage |
| ChromaDB | `chromadb/chroma:latest` | Vector store |

---

## 📁 Project Structure

```
grc-ai-analyzer/
├── docker-compose.yml          # Infrastructure services (PostgreSQL, MinIO, ChromaDB)
├── .env                        # Environment variables (not committed to VCS)
│
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── alembic.ini             # Alembic migration configuration
│   ├── alembic/
│   │   └── versions/           # Database migration scripts
│   └── app/
│       ├── config.py           # Application settings (Pydantic Settings)
│       ├── database.py         # Async SQLAlchemy engine & session
│       ├── models/             # SQLAlchemy ORM models
│       │   ├── utilisateur.py  # User model
│       │   ├── rapport.py      # Report model
│       │   ├── analyse.py      # Analysis model
│       │   ├── risque.py       # Risk model
│       │   ├── conformite.py   # Compliance model
│       │   └── recommandation.py # Recommendation model
│       ├── schemas/            # Pydantic request/response schemas
│       ├── core/
│       │   ├── security.py     # JWT creation & password hashing
│       │   └── deps.py         # FastAPI dependency injection
│       ├── api/
│       │   └── v1/
│       │       ├── auth.py     # Authentication endpoints
│       │       ├── rapports.py # Report upload & management
│       │       ├── analyses.py # Analysis trigger & retrieval
│       │       ├── chat.py     # RAG chat endpoint
│       │       ├── recommandations.py # Recommendations CRUD
│       │       └── export.py   # PDF/Excel export endpoints
│       ├── services/           # Business logic services
│       └── ai/
│           ├── mistral_client.py # Mistral AI API wrapper
│           ├── parsers/        # PDF, DOCX, XLSX document parsers
│           ├── prompts/        # LLM prompt templates
│           └── rag/
│               └── vector_store.py # ChromaDB vector store operations
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.tsx            # React app entry point
        ├── App.tsx             # Root component
        ├── router.tsx          # React Router configuration
        ├── index.css           # Global styles
        ├── pages/
        │   ├── Login.tsx       # Authentication page
        │   ├── Dashboard.tsx   # Overview & statistics
        │   ├── Reports.tsx     # Report list & upload
        │   └── Analysis.tsx    # Detailed analysis view + RAG chat
        ├── components/         # Reusable UI components
        ├── services/           # API service layer (Axios)
        ├── store/              # Zustand global state stores
        ├── types/              # TypeScript type definitions
        └── lib/                # Utility functions
```

---

## ✅ Prerequisites

Before starting, ensure you have the following installed:

| Tool | Version | Download |
|---|---|---|
| **Docker** & Docker Compose | Latest | [docker.com](https://www.docker.com/get-started) |
| **Python** | ≥ 3.11 | [python.org](https://www.python.org/downloads/) |
| **Node.js** | ≥ 18 LTS | [nodejs.org](https://nodejs.org) |
| **npm** | ≥ 9 | Bundled with Node.js |
| **Mistral AI API Key** | — | [console.mistral.ai](https://console.mistral.ai) |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/grc-ai-analyzer.git
cd grc-ai-analyzer
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

> **Required:** Set your `MISTRAL_API_KEY`. All other values work out-of-the-box for local development.

Open `.env` and update:

```env
MISTRAL_API_KEY=your_actual_mistral_api_key_here
SECRET_KEY=your_strong_random_secret_key_here
```

> ⚠️ **Security Note:** Never commit your `.env` file to version control. The `.gitignore` should already exclude it.

### 3. Start Infrastructure (Docker)

Launch PostgreSQL, MinIO, and ChromaDB using Docker Compose:

```bash
docker-compose up -d
```

Verify all services are healthy:

```bash
docker-compose ps
```

Expected output — all services should show `healthy` or `running`:

```
NAME              STATUS
grc_postgres      running (healthy)
grc_minio         running (healthy)
grc_minio_init    exited (0)        ← one-time bucket initializer
grc_chromadb      running (healthy)
```

**Service ports:**

| Service | Port | URL |
|---|---|---|
| PostgreSQL | 5433 | `postgresql://localhost:5433/grc_db` |
| MinIO S3 API | 9000 | `http://localhost:9000` |
| MinIO Console | 9001 | `http://localhost:9001` |
| ChromaDB | 8001 | `http://localhost:8001` |

### 4. Set Up the Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv ../venv

# Windows
..\venv\Scripts\activate

# macOS / Linux
source ../venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI development server
uvicorn main:app --reload --port 8000
```

The API will be available at:
- **Swagger UI (interactive docs):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### 5. Create a Default User Account

Before logging into the application, you must create a user account via the interactive API documentation:
1. Navigate to **http://localhost:8000/docs**
2. Expand the `POST /api/v1/auth/register` section and click **Try it out**.
3. Provide your desired email and password in the JSON body:
   ```json
   {
     "nom": "Admin",
     "email": "admin@entreprise.com",
     "password": "password123",
     "role": "ANALYSTE"
   }
   ```
4. Click **Execute** (you should receive an HTTP 201 response).

### 6. Set Up the Frontend

Open a new terminal window:

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the Vite development server
npm run dev
```

The application will be available at: **http://localhost:3000**

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Register a new user | ❌ |
| `POST` | `/auth/login` | Obtain JWT access token | ❌ |
| `GET` | `/auth/me` | Get current user profile | ✅ |

### Reports

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/rapports` | List all reports for the user | ✅ |
| `POST` | `/rapports/upload` | Upload a new GRC document (PDF/DOCX/XLSX) | ✅ |
| `GET` | `/rapports/{id}` | Get report details | ✅ |
| `DELETE` | `/rapports/{id}` | Delete a report | ✅ |

### Analyses

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/analyses/{rapport_id}/trigger` | Start AI analysis on a report | ✅ |
| `GET` | `/analyses/{rapport_id}` | Get full analysis results | ✅ |
| `GET` | `/analyses/{rapport_id}/risks` | Get identified risks | ✅ |
| `GET` | `/analyses/{rapport_id}/compliance` | Get compliance scores | ✅ |

### Chat (RAG)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/chat/{rapport_id}` | Ask a question about a specific report | ✅ |

### Recommendations

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/recommandations/{rapport_id}` | List recommendations for a report | ✅ |
| `PATCH` | `/recommandations/{id}/status` | Update recommendation status | ✅ |

### Export

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/export/{rapport_id}/pdf` | Download analysis as PDF | ✅ |
| `GET` | `/export/{rapport_id}/excel` | Download analysis as Excel | ✅ |

---

## 🗄️ Data Models

```
Utilisateur (User)
├── id, email, nom, prenom
├── hashed_password
└── is_active, created_at

Rapport (Report)
├── id, titre, description
├── type_document (PDF/DOCX/XLSX)
├── fichier_url (MinIO path)
├── statut (PENDING/PROCESSING/COMPLETED/ERROR)
└── utilisateur_id → Utilisateur

Analyse (Analysis)
├── id, rapport_id → Rapport
├── statut, created_at, completed_at
└── resume (AI-generated summary)

Risque (Risk)
├── id, analyse_id → Analyse
├── categorie (CYBER/OPERATIONNEL/FINANCIER/LEGAL/STRATEGIQUE)
├── titre, description
├── probabilite (1-5), impact (1-5)
└── score = probabilite × impact, niveau (FAIBLE/MOYEN/ELEVE/CRITIQUE)

Conformite (Compliance)
├── id, analyse_id → Analyse
├── framework (ISO_27001/RGPD/LOI_09_08)
├── score (0.0 - 100.0)
└── details, gaps

Recommandation (Recommendation)
├── id, analyse_id → Analyse
├── titre, description
├── priorite (CRITIQUE/HAUTE/MOYENNE/FAIBLE)
├── horizon (QUICK_WIN/MOYEN_TERME/LONG_TERME)
└── statut (EN_ATTENTE/EN_COURS/TERMINE)
```

---

## 🤖 AI Pipeline

The analysis follows a multi-stage AI pipeline:

```
Document Upload
      │
      ▼
┌─────────────────────┐
│   Document Parser   │  ← PyMuPDF / python-docx / openpyxl
│  Text Extraction    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Text Chunking &    │  ← sentence-transformers (local embeddings)
│  Vectorization      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ChromaDB Storage   │  ← Persist vectors per rapport_id
└──────────┬──────────┘
           │
           ├──────────────────────────────────────────┐
           ▼                                          ▼
┌─────────────────────┐                  ┌────────────────────────┐
│   Mistral AI Call   │                  │     RAG Chat Query     │
│  (Risk Extraction,  │                  │  Vector search →       │
│   Compliance Audit, │                  │  Context injection →   │
│   Action Plan)      │                  │  Mistral response      │
└──────────┬──────────┘                  └────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  DB Persistence     │  ← PostgreSQL: Risques, Conformites, Recommandations
└─────────────────────┘
```

**Compliance frameworks evaluated:**
- 🔒 **ISO 27001** — Information security management system controls
- 🇪🇺 **GDPR (RGPD)** — EU General Data Protection Regulation
- 🇲🇦 **Law 09-08** — Morocco's personal data protection law

---

## ⚙️ Environment Variables Reference

| Variable | Default | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://grc_user:grc_secret@localhost:5433/grc_db` | ✅ | Async PostgreSQL connection string |
| `MISTRAL_API_KEY` | — | ✅ | Your Mistral AI API key |
| `MISTRAL_MODEL` | `mistral-large-latest` | ❌ | Mistral model to use |
| `MINIO_ENDPOINT` | `localhost:9000` | ✅ | MinIO S3 endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | ✅ | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin` | ✅ | MinIO secret key |
| `MINIO_BUCKET` | `grc-reports` | ✅ | MinIO bucket name |
| `MINIO_SECURE` | `false` | ❌ | Use HTTPS for MinIO |
| `CHROMA_HOST` | `localhost` | ✅ | ChromaDB host |
| `CHROMA_PORT` | `8001` | ✅ | ChromaDB port |
| `SECRET_KEY` | — | ✅ | JWT signing secret key |
| `ALGORITHM` | `HS256` | ❌ | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | ❌ | JWT token lifetime |
| `FRONTEND_URL` | `http://localhost:3000` | ✅ | Frontend URL (CORS) |
| `APP_NAME` | `GRC AI Analyzer` | ❌ | Application name |
| `APP_VERSION` | `1.0.0` | ❌ | Application version |
| `DEBUG` | `true` | ❌ | Enable debug mode |

---

## 🛠️ Development Guide

### Running Database Migrations

```bash
# Create a new migration after model changes
cd backend
alembic revision --autogenerate -m "describe_your_change"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Backend Code Organization

- **`app/models/`** — Define SQLAlchemy ORM models here. All models are registered in `__init__.py`.
- **`app/schemas/`** — Define Pydantic schemas for request body validation and response serialization.
- **`app/services/`** — Business logic lives here, not in the API routes.
- **`app/api/v1/`** — Thin route handlers that call services.
- **`app/ai/`** — All AI-related code: Mistral client, document parsers, prompt templates, and RAG pipeline.

### Frontend Code Organization

- **`src/pages/`** — Top-level page components mapped to routes.
- **`src/components/`** — Reusable UI components (buttons, cards, charts, etc.).
- **`src/services/`** — Axios API call functions, one file per resource.
- **`src/store/`** — Zustand state stores for global application state.
- **`src/types/`** — Shared TypeScript interfaces and type definitions.

### Building for Production

```bash
# Frontend production build
cd frontend
npm run build
# Output in ./dist

# Backend — use gunicorn with uvicorn workers in production
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🐳 Deployment

### Docker Deployment (Recommended)

For production, containerize both the backend and frontend and add them to `docker-compose.yml`:

```yaml
# Add to docker-compose.yml for a full containerized deployment:

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      chromadb:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### Environment Checklist for Production

- [ ] Change `SECRET_KEY` to a cryptographically strong random value
- [ ] Change MinIO credentials from the defaults (`minioadmin`)
- [ ] Set `DEBUG=false`
- [ ] Set `MINIO_SECURE=true` and configure TLS
- [ ] Use a strong PostgreSQL password
- [ ] Set `FRONTEND_URL` to your actual production domain
- [ ] Configure a reverse proxy (nginx) in front of FastAPI

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

---

<div align="center">

Final Year Engineering Project (PFE)

**GRC AI Analyzer** — Automating Governance, Risk & Compliance with AI

</div>
