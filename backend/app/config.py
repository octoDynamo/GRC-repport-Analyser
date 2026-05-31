"""Application configuration using pydantic-settings."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to this file → works from any working directory
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "GRC AI Analyzer"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str

    # ── Mistral AI ────────────────────────────────────────────────────────────
    mistral_api_key: str
    mistral_model: str = "mistral-large-latest"

    # ── File Storage ──────────────────────────────────────────────────────────
    upload_dir: str = "uploads"

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # ── JWT ───────────────────────────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # ── CORS ──────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    # ── HuggingFace (sentence-transformers offline mode) ──────────────────────
    transformers_offline: str = "1"
    hf_datasets_offline: str = "1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
