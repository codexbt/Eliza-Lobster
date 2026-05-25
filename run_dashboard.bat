@echo off
REM run_dashboard.bat
REM Starts the Kairos 3D Futuristic Dashboard
REM Windows batch script for easy one-click startup

setlocal enabledelayedexpansion

echo.
echo ══════════════════════════════════════════════════════════════════
echo ╚     HERMESCLAW 3D FUTURISTIC DASHBOARD                      ╝
echo ║     Cyberpunk AI Swarm Command Center                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if venv exists, create if not
if not exist ".venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing Python dependencies...
pip install -q -r requirements.txt

REM Start the dashboard backend
echo 🚀 Starting FastAPI Dashboard Backend (port 8001)...
start cmd /k "python -m uvicorn backend.dashboard_api:app --reload --reload-dir backend --reload-dir core --reload-dir hermes --port 8001"

REM Wait a second for backend to start
timeout /t 2 /nobreak

set DASHBOARD_DIR=kairos
if not exist "%DASHBOARD_DIR%" set DASHBOARD_DIR=dashboard

REM Check if Node modules exist
if not exist "%DASHBOARD_DIR%\node_modules" (
    echo 📦 Installing Frontend dependencies...
    cd %DASHBOARD_DIR%
    call npm install --legacy-peer-deps
    cd ..
)

REM Start the React frontend dev server
echo 🎨 Starting Dashboard Frontend (port 3000)...
cd %DASHBOARD_DIR%
call npm run dev

echo.
echo ✨ Dashboard is starting...
echo 🌐 Frontend: http://localhost:3000
echo 📡 Backend API: http://localhost:8001
echo 🔌 WebSocket: ws://localhost:8001/ws/dashboard
echo.
echo Press Ctrl+C in either window to stop.
