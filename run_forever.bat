@echo off
REM run_forever.bat
REM Always-running Kairos Multi-Platform Bot (Windows)
REM Auto-restarts on crash, logs to logs/bot.log
REM Double-click or schedule this.

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [Kairos Bot] Starting persistent bot service...
echo Logs: logs\bot.log
echo Press Ctrl+C in this window to stop (or close to restart next time)

:loop
echo [%date% %time%] Starting bot...
python bot_orchestrator.py >> logs\bot.log 2>&1
echo [%date% %time%] Bot exited (crash or stop). Restarting in 5 seconds...
timeout /t 5 >nul
goto loop


