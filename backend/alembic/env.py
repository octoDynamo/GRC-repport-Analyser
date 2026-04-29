"""Alembic environment — uses a synchronous psycopg2 connection for migrations.

Using asyncpg inside alembic's synchronous runner causes WinError 121 on
Windows/WSL2. We switch to the standard psycopg2 driver here (which is already
installed as psycopg2-binary in requirements.txt) while keeping asyncpg for the
running FastAPI application.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Import all models so Alembic can detect them
import app.models  # noqa: F401

config = context.config

# Build a *synchronous* psycopg2 URL from the asyncpg one stored in settings.
# e.g. postgresql+asyncpg://user:pass@host/db  →  postgresql+psycopg2://user:pass@host/db
_sync_url = (
    settings.database_url
    .replace("+asyncpg", "+psycopg2")
    .replace("postgresql+psycopg2", "postgresql")   # keep plain driver name
)
config.set_main_option("sqlalchemy.url", _sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
