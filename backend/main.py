"""FastAPI application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import (
    admin,
    analyses,
    auth,
    chat,
    export,
    rapports,
    recommandations,
)
from app.config import settings
from app.core.limiter import limiter

# Set HuggingFace offline mode before sentence-transformers is imported
os.environ.setdefault("TRANSFORMERS_OFFLINE", settings.transformers_offline)
os.environ.setdefault("HF_DATASETS_OFFLINE", settings.hf_datasets_offline)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GRC AI Analyzer API",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration — allow both the configured URL and the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(rapports.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1")
app.include_router(recommandations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
