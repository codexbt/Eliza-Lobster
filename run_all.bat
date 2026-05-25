@echo off
REM run_all.bat
REM Comprehensive startup for full Kairos system with 3D Dashboard
REM Windows batch script

setlocal enabledelayedexpansion

echo.
echo ══════════════════════════════════════════════════════════════════
 echo ╚     HERMESCLAW FULL SYSTEM STARTUP                          ╝
echo ║     Multi-Agent Swarm + 3D Command Center                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist ".venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing Python dependencies...
pip install -q -r requirements.txt

echo.
echo Choose what to run:
echo 1. Dashboard Only (3D command center - port 3000/8001)
echo 2. Kairos Daemon (autonomous background scanner)
echo 3. Full System (Dashboard + Kairos)
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo 🎨 Launching Dashboard...
    start cmd /k "python -m uvicorn backend.dashboard_api:app --reload --reload-dir backend --reload-dir core --reload-dir hermes --port 8001"
    timeout /t 2
    cd dashboard
    if not exist "node_modules" npm install > nul 2>&1
    call npm run dev
) else if "%choice%"=="2" (
    echo 🤖 Launching Kairos Daemon...
    python -m core.kairos_daemon
) else if "%choice%"=="3" (
    echo 🎨 Launching Dashboard...
    start cmd /k "python -m uvicorn backend.dashboard_api:app --reload --reload-dir backend --reload-dir core --reload-dir hermes --port 8001"
    echo 🤖 Launching Kairos Daemon...
    start cmd /k "python -m core.kairos_daemon"
    timeout /t 2
    cd dashboard
    if not exist "node_modules" npm install > nul 2>&1
    call npm run dev
) else (
    echo Invalid choice. Exiting.
    exit /b 1
)
