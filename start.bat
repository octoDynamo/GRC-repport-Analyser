@echo off
setlocal enabledelayedexpansion
title GRC AI Analyzer Startup

echo.
echo  ===============================================
echo    GRC AI Analyzer - Service Startup (Windows)
echo  ===============================================
echo.

:: ─── Check prerequisites ─────────────────────────────────────────────────────
if not exist "%~dp0.env" (
    echo [ERROR] .env file not found.
    echo   Run: copy .env.example .env
    echo   Then fill in MISTRAL_API_KEY and SECRET_KEY.
    pause & exit /b 1
)

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv "%~dp0venv"
    if errorlevel 1 ( echo [ERROR] python -m venv failed. & pause & exit /b 1 )
    call "%~dp0venv\Scripts\activate.bat"
    echo [INFO] Installing backend dependencies...
    pip install -q -r "%~dp0backend\requirements.txt"
) else (
    call "%~dp0venv\Scripts\activate.bat"
)

:: ─── 1. MinIO ────────────────────────────────────────────────────────────────
echo [1/4] MinIO...
curl -sf --max-time 2 http://127.0.0.1:9000/minio/health/live >nul 2>&1
if not errorlevel 1 (
    echo      Already running.
) else if exist C:\minio\minio.exe (
    start "MinIO" /min cmd /k "set MINIO_ROOT_USER=minioadmin && set MINIO_ROOT_PASSWORD=minioadmin && C:\minio\minio.exe server C:\minio\data --address :9000 --console-address :9001"
    timeout /t 5 /nobreak >nul
    echo      Started  ^> http://127.0.0.1:9000  (Console: http://127.0.0.1:9001)
) else (
    echo      [WARN] MinIO not found at C:\minio\minio.exe
    echo      Download minio.exe and save it to C:\minio\minio.exe:
    echo        curl -L -o C:\minio\minio.exe https://dl.min.io/server/minio/release/windows-amd64/minio.exe
    echo      Or start Docker: docker-compose up -d minio
)

:: ─── 2. ChromaDB ─────────────────────────────────────────────────────────────
echo [2/4] ChromaDB...
curl -sf --max-time 2 http://127.0.0.1:8001/api/v2/heartbeat >nul 2>&1
if not errorlevel 1 (
    echo      Already running.
) else (
    if not exist "%~dp0chroma_data" mkdir "%~dp0chroma_data"
    start "ChromaDB" /min cmd /k "call "%~dp0venv\Scripts\activate.bat" && chroma run --path "%~dp0chroma_data" --host 0.0.0.0 --port 8001"
    timeout /t 8 /nobreak >nul
    echo      Started  ^> http://127.0.0.1:8001
)

:: ─── 3. Database migrations ──────────────────────────────────────────────────
echo [3/4] Database migrations...
cd /d "%~dp0backend"
alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Migrations failed. Check DATABASE_URL in .env
    cd /d "%~dp0"
    pause & exit /b 1
)
echo      Up to date.
cd /d "%~dp0"

:: ─── 4. Backend ──────────────────────────────────────────────────────────────
echo [4/4] FastAPI backend...
start "FastAPI" cmd /k "cd /d "%~dp0backend" && call "..\venv\Scripts\activate.bat" && uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
echo      Started  ^> http://localhost:8000/docs

echo.
echo  ===============================================
echo    Ready!
echo  ===============================================
echo    API Docs:       http://localhost:8000/docs
echo    MinIO Console:  http://localhost:9001
echo    ChromaDB:       http://localhost:8001
echo.
echo    Frontend: cd frontend ^&^& npm install ^&^& npm run dev
echo  ===============================================
echo.
pause
