#!/bin/bash
# run_dashboard.sh
# Starts the Kairos 3D Futuristic Dashboard
# Linux/Mac bash script for easy startup

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     HERMESCLAW 3D FUTURISTIC DASHBOARD                      ║"
echo "║     Cyberpunk AI Swarm Command Center                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -q -r requirements.txt > /dev/null 2>&1

# Start the dashboard backend in background
echo "🚀 Starting FastAPI Dashboard Backend (port 8001)..."
python -m uvicorn backend.dashboard_api:app --reload --reload-dir backend --reload-dir core --reload-dir hermes --port 8001 &
BACKEND_PID=$!

# Wait a second for backend to start
sleep 2

DASHBOARD_DIR="kairos"
if [ ! -d "$DASHBOARD_DIR" ]; then
    DASHBOARD_DIR="dashboard"
fi

# Check if Node modules exist
if [ ! -d "$DASHBOARD_DIR/node_modules" ]; then
    echo "📦 Installing Frontend dependencies..."
    cd "$DASHBOARD_DIR"
    npm install > /dev/null 2>&1
    cd ..
fi

# Start the dashboard dev server
echo "🎨 Starting Dashboard Frontend (port 3000)..."
cd "$DASHBOARD_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ Dashboard is starting..."
echo "🌐 Frontend: http://localhost:3000"
echo "📡 Backend API: http://localhost:8001"
echo "🔌 WebSocket: ws://localhost:8001/ws/dashboard"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for user to interrupt
wait $BACKEND_PID $FRONTEND_PID
