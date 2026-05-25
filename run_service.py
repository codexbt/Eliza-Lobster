"""run_service.py
Production-ready entry point for running Kairos Bot as a Windows Service (via NSSM)
or Linux systemd, or Task Scheduler.

Features:
- Clean start_bot() call
- Graceful signal handling (SIGINT/SIGTERM)
- Auto-restart wrapper (optional)
- Logs everything to logs/bot.log (already configured in bot_orchestrator)

Usage:
  1. Install NSSM: https://nssm.cc/
  2. nssm install KairosBot
     Path: python.exe
     Arguments: D:\hermes\run_service.py
     Startup dir: D:\hermes
  3. Set environment variables for tokens in the service if needed.

Or simply:
  python run_service.py
"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

# Ensure we are in project root
ROOT = Path(__file__).parent.resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from bot_orchestrator import start_bot

def handle_signal(signum, frame):
    print(f"\n[run_service] Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signals (Windows supports SIGINT, SIGTERM via CTRL+C / service stop)
    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    print("[run_service] Kairos Multi-Platform Bot starting as service...")
    print("Logs: logs/bot.log")
    print("To stop: use service manager or Ctrl+C")

    # Simple auto-restart loop (the bot itself also has some resilience)
    restart_count = 0
    max_restarts = 50
    while restart_count < max_restarts:
        try:
            start_bot()
        except KeyboardInterrupt:
            print("[run_service] Stopped by user.")
            break
        except Exception as e:
            restart_count += 1
            print(f"[run_service] Bot crashed ({e}). Auto-restart #{restart_count} in 8s...")
            time.sleep(8)
    else:
        print("[run_service] Too many restarts. Exiting. Check logs/bot.log")
