@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================
echo   Starting KAIROS Autonomous Daemon
echo   Kairos / Kairos-Hermes Swarm
echo ============================================
echo.

python -m core.kairos_daemon %*

echo.
echo KAIROS daemon exited.
pause
