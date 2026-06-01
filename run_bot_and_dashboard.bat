@echo off
REM ============================================================
REM Kairos Bot + 3D Dashboard (Unified Launcher)
REM Run both bot and dashboard simultaneously with one command
REM ============================================================
REM Usage: run_bot_and_dashboard.bat
REM        OR: cmd /c run_bot_and_dashboard.bat
REM
REM This script:
REM 1. Sets up Python virtual environment
REM 2. Installs Python dependencies
REM 3. Sets up Node.js dependencies for dashboard
REM 4. Starts FastAPI backend on port 8001 (new window)
REM 5. Starts KAIROS Dashboard (React) on port 3000 (new window) from the "dashboard" folder
REM 6. Starts bot/swarm orchestrator (new window)
REM ============================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo Kairos: Bot + Dashboard Unified Launcher
echo ============================================================
echo.

REM Create .env from .env.example if it doesn't exist
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo ^[INFO^] .env created. Please edit it with your API keys!
    echo.
)

REM Create venv if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo Activating Python virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate venv
    pause
    exit /b 1
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Starting Services...
echo ============================================================
echo.
echo ^[1/3^] Starting FastAPI Backend (http://localhost:8001)...
start "Kairos Backend" cmd /k "python -m uvicorn backend.dashboard_api:app --host 0.0.0.0 --port 8001 --reload --reload-dir backend --reload-dir core --reload-dir hermes"

echo ^[2/3^] Starting KAIROS Dashboard (http://localhost:3000)...

set DASHBOARD_DIR=dashboard

REM Important: Make sure you have run "cd dashboard && npm install --legacy-peer-deps" at least once

start "Kairos Dashboard" cmd /k "cd /d %~dp0\%DASHBOARD_DIR% && npm run dev"

REM [3/3] Bot is disabled for now (fake tokens causing errors).
REM To enable later, put real tokens in config.yaml or .env and uncomment the lines below.

REM echo ^[3/3^] Starting Bot/Swarm Orchestrator...
REM timeout /t 3 /nobreak
REM start "Kairos Bot" cmd /k "python bot_orchestrator.py"

echo.
echo ============================================================
echo ALL SERVICES STARTED!
echo ============================================================
echo.
echo Open your browser: http://localhost:3000
echo.
echo Services:
echo   - KAIROS Dashboard:  http://localhost:3000
echo   - FastAPI Docs: http://localhost:8001/docs
echo.
echo To stop services: Close this window (or press any key).
echo All other windows will be closed automatically.
echo.
echo ============================================================
echo.

pause >nul

echo Stopping all services...

taskkill /FI "WINDOWTITLE eq Kairos Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Kairos Dashboard*" /F >nul 2>&1
REM taskkill /FI "WINDOWTITLE eq Kairos Bot*" /F >nul 2>&1

echo All services stopped.
timeout /t 2 >nul


