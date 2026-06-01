#!/usr/bin/env python3
"""Kairos Bot + Dashboard Unified Launcher (Cross-Platform)

Usage:
    python run_unified.py
    
This script:
1. Sets up Python virtual environment
2. Installs Python dependencies  
3. Sets up Node.js dependencies for dashboard
4. Starts FastAPI backend (port 8001)
5. Starts React dashboard (port 3000)
6. Starts bot orchestrator
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path

def run_command(cmd, shell=True):
    """Run command and return exit code"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"ERROR: Failed to run command: {e}")
        return 1

def main():
    print("\n" + "="*60)
    print("Kairos: Bot + Dashboard Unified Launcher")
    print("="*60 + "\n")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Create .env from .env.example
    if not Path(".env").exists():
        print("Creating .env from .env.example...")
        if Path(".env.example").exists():
            with open(".env.example") as f:
                content = f.read()
            with open(".env", "w") as f:
                f.write(content)
            print("[INFO] .env created. Please edit it with your API keys!\n")
        else:
            print("[WARNING] .env.example not found\n")
    
    # Create venv if needed
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("Creating Python virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
    
    # Activate venv (platform specific)
    if platform.system() == "Windows":
        activate_cmd = str(venv_dir / "Scripts" / "activate.bat")
    else:
        activate_cmd = f"source {venv_dir / 'bin' / 'activate'}"
    
    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    pip_cmd = "pip" if platform.system() == "Windows" else "pip3"
    run_command(f"{pip_cmd} install -q -r requirements.txt")
    
    print("\n" + "="*60)
    print("Starting Services...")
    print("="*60 + "\n")
    
    # Start FastAPI backend
    print("[1/3] Starting FastAPI Backend (http://localhost:8001)...")
    backend_cmd = "python -m uvicorn backend.dashboard_api:app --host 0.0.0.0 --port 8001 --reload --reload-dir backend --reload-dir core --reload-dir hermes"
    if platform.system() == "Windows":
        subprocess.Popen(f'start "Kairos Backend" cmd /k {backend_cmd}', shell=True)
    else:
        subprocess.Popen(backend_cmd, shell=True)
    
    time.sleep(2)
    
    # Determine dashboard folder
    dashboard_dir = Path("kairos") if Path("kairos").exists() else Path("dashboard")
    if not (dashboard_dir / "node_modules").exists():
        print("\n[2/3] Installing Node dependencies (first time only)...")
        os.chdir(dashboard_dir)
        run_command("npm install --legacy-peer-deps")
        os.chdir(script_dir)
    else:
        print(f"\n[2/3] Starting dashboard ({dashboard_dir} on http://localhost:3000)...")
    
    # Start dashboard
    dashboard_cmd = f"cd {dashboard_dir} && npm run dev"
    if platform.system() == "Windows":
        subprocess.Popen(f'start "Kairos Dashboard" cmd /k {dashboard_cmd}', shell=True)
    else:
        subprocess.Popen(dashboard_cmd, shell=True)
    
    time.sleep(3)
    
    # Start bot orchestrator
    print("[3/3] Starting Bot/Swarm Orchestrator...")
    bot_cmd = "python bot_orchestrator.py"
    if platform.system() == "Windows":
        subprocess.Popen(f'start "Kairos Bot" cmd /k {bot_cmd}', shell=True)
    else:
        subprocess.Popen(bot_cmd, shell=True)
    
    print("\n" + "="*60)
    print("ALL SERVICES STARTED!")
    print("="*60 + "\n")
    print("Open your browser: http://localhost:3000\n")
    print("Services:")
    print("  - 3D Dashboard:  http://localhost:3000")
    print("  - FastAPI Docs: http://localhost:8001/docs")
    print("  - Bot Console:   Active in separate process\n")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
        # Keep process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


