# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRC AI Analyzer is a full-stack platform that automates Governance, Risk & Compliance (GRC) report analysis using Mistral AI. Users upload PDF/DOCX/XLSX documents; the system extracts risks, evaluates compliance against ISO 27001, GDPR, and Morocco's Law 09-08, generates recommendations, and provides an RAG-powered chat interface over the analyzed report.

## Getting Started (fresh clone)

```bash
# 1. Copy and fill in your secrets
copy .env.example .env
# Edit .env: set MISTRAL_API_KEY and SECRET_KEY

# 2. Create the virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend\requirements.txt

# 3. Start infrastructure services (two options — pick one)
```

**Option A — Docker (recommended on Linux/Mac or if Docker port forwarding works):**
```bash
docker-compose up -d           # starts PostgreSQL:5434, MinIO:9000, ChromaDB:8001
# Then update .env DATABASE_URL to use port 5434 with password grc_secret
```

**Option B — Windows native (if Docker port forwarding is broken, as is common on Windows 11 + WSL2):**
```bash
# PostgreSQL: install locally, create grc_user + grc_db, run on port 5433
# MinIO: download binary once
curl -L -o C:\minio\minio.exe https://dl.min.io/server/minio/release/windows-amd64/minio.exe
# ChromaDB: already in requirements.txt (chroma CLI installed with pip)
```

**Shortcut — use the startup script (Windows native, Option B):**
```bat
start.bat        # starts MinIO + ChromaDB + runs migrations + starts uvicorn
```

```bash
# 4. Run database migrations (if not using start.bat)
cd backend
alembic upgrade head

# 5. Start the backend (if not using start.bat)
uvicorn main:app --reload --port 8000

# 6. Start the frontend
cd frontend
npm install
npm run dev      # http://localhost:5173
```

## Commands

### Backend
```bash
cd backend
alembic upgrade head                                    # Apply DB migrations
alembic revision --autogenerate -m "describe_change"   # Generate migration after model changes
alembic downgrade -1                                    # Roll back one migration
uvicorn main:app --reload --port 8000                  # Dev server → http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # Production build → ./dist
```

### Production backend
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Infrastructure Setup Notes

### Windows + WSL2 Docker issue
Docker Desktop on Windows 11 with WSL2 sometimes binds container ports but they are unreachable from the Windows host (port appears taken but connections time out). If `curl http://127.0.0.1:9000/minio/health/live` times out despite the Docker container showing healthy, use Option B (native services) instead:

- **PostgreSQL**: install locally, default or custom port (update `DATABASE_URL` in `.env`)
- **MinIO**: `C:\minio\minio.exe server C:\minio\data --address :9000 --console-address :9001`
- **ChromaDB**: `chroma run --path ./chroma_data --host 0.0.0.0 --port 8001`

The `start.bat` script automates all of the above.

### MinIO bucket
The `grc-reports` bucket is created automatically on first upload by `report_service.py`.

## Architecture

### Request Flow
```
Browser (React/Vite)
  → Axios HTTP → FastAPI (port 8000)
    → Services layer (business logic)
      → AI layer (Mistral + ChromaDB + sentence-transformers)
      → PostgreSQL (metadata, analysis results)
      → MinIO (raw document files)
```

### Key Architectural Decisions

**Analysis is a two-phase async pipeline** (`backend/app/services/analysis_service.py`):
- Phase 1 (`asyncio.gather`): ChromaDB indexing + risk extraction + all 3 compliance checks run *in parallel* via Mistral
- Phase 2 (`asyncio.gather`): Recommendations + executive summary run *in parallel*
- The analysis runs as a FastAPI `BackgroundTask` in a separate `AsyncSession` so it doesn't block the HTTP response

**Mistral API calls are serialized** by a global `asyncio.Semaphore(1)` in `mistral_client.py` to avoid 429 rate-limit errors.

**RAG pipeline** per analysis: document → chunks (1500 chars, 200 overlap) → `paraphrase-multilingual-MiniLM-L12-v2` embeddings → ChromaDB collection named `analyse_{id}`. RAG indexing failure is non-fatal — analysis proceeds without chat capability.

**Alembic uses psycopg2 (sync), FastAPI uses asyncpg (async)** — `alembic/env.py` rewrites the `DATABASE_URL` to use the sync driver. This is intentional to avoid Windows/WSL2 `WinError 121` issues. The `sqlalchemy.url` in `alembic.ini` is a placeholder — it is always overridden at runtime by `env.py` reading from `.env`.

**All API responses** follow a uniform envelope: `{"data": ..., "message": "...", "success": bool}`.

### Database Models (PostgreSQL)
- `Utilisateur` → `Rapport` (one user, many reports)
- `Rapport` → `Analyse` (one report, one active analysis)
- `Analyse` → `Risque[]`, `ResultatConformite[]`, `Recommandation[]`
- `Risque` ↔ `Recommandation` (optional FK `risque_id`)

Risk severity: `score = probabilite × impact` (1–5 each); thresholds: FAIBLE < 6, MOYEN < 12, ELEVE < 20, CRITIQUE ≥ 20.

Compliance frameworks stored as enum strings: `ISO27001`, `RGPD`, `LOI0908`.

### Backend Code Layout
- `app/config.py` — Pydantic Settings; `.env` is resolved relative to the file path (works from any CWD)
- `app/api/v1/` — Thin route handlers; business logic lives in `app/services/`
- `app/ai/prompts/` — Prompt builders for each extraction type (risk, compliance, recommendation, summary)
- `app/ai/parsers/document_parser.py` — PDF (PyMuPDF), DOCX (python-docx), XLSX (openpyxl) → plain text + chunking
- `app/ai/rag/vector_store.py` — ChromaDB client (HTTP mode) and sentence-transformer embeddings (lazy-loaded singletons)
- `app/core/deps.py` — `get_current_user` dependency (JWT → DB lookup); `require_admin` for admin-only routes

### Frontend Code Layout
- `src/services/api.ts` — Axios instance with JWT interceptor; one function per API resource
- `src/store/` — Zustand stores for global state (auth, reports, etc.)
- `src/pages/Analysis.tsx` — Polls `GET /analyses/{id}` every few seconds until `statut === 'termine'`, then fetches all sub-resources in parallel
- `src/components/risks/RiskMatrix.tsx` and `src/components/compliance/ComplianceRadar.tsx` — Chart components using Recharts

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` — connection string (port/password depend on your PostgreSQL setup)
- `MISTRAL_API_KEY` — required, get from console.mistral.ai
- `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_hex(32))"`

All other variables have working defaults. `.env` is gitignored — never commit it.

## API URL Prefix

All endpoints: `/api/v1/`. Key routes:
- `POST /api/v1/analyses/lancer/{rapport_id}` — triggers analysis (returns 202, runs in background)
- `GET /api/v1/analyses/{analyse_id}` — poll for status (`en_cours` → `termine` | `erreur`)
- `POST /api/v1/chat/{analyse_id}` — RAG chat question
- `GET /api/v1/export/{analyse_id}/pdf` and `/excel` — download reports
