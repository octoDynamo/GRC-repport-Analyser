"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    analyses,
    auth,
    chat,
    export,
    rapports,
    recommandations,
)
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GRC AI Analyzer API",
)

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
app.include_router(rapports.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1")
app.include_router(recommandations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
