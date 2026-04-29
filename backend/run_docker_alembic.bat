a@echo off
docker run --rm -v "c:\Users\mahdi\Documents\PFE\GRC platform\grc-ai-analyzer\backend:/app" -w /app --env-file ../.env --network grc_network python:3.13-slim bash -c "pip install --no-cache-dir alembic sqlalchemy asyncpg pydantic pydantic-settings psycopg2-binary passlib bcrypt && DATABASE_URL=postgresql+asyncpg://grc_user:grc_secret@grc_postgres:5432/grc_db alembic upgrade head"
