# ============================================================
# Kairos Bot + Dashboard Unified Launcher (PowerShell)
# ============================================================
# Usage: .\run_bot_and_dashboard.ps1
#
# This script:
# 1. Sets up Python virtual environment
# 2. Installs Python dependencies
# 3. Sets up Node.js dependencies
# 4. Starts FastAPI backend (port 8001)
# 5. Starts React dashboard (port 3000)
# 6. Starts bot orchestrator
# ============================================================

param(
    [switch]$NoWait = $false,
    [switch]$Headless = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "`n============================================================"
Write-Host "Kairos: Bot + Dashboard Unified Launcher" -ForegroundColor Cyan
Write-Host "============================================================`n"

# Create .env from .env.example
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[INFO] .env created. Please edit it with your API keys!`n" -ForegroundColor Yellow
    }
}

# Create venv if needed
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    & python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
    }
}

# Activate venv
Write-Host "Activating Python virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "Installing Python dependencies..."
& pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python packages"
}

Write-Host "`n============================================================"
Write-Host "Starting Services..."
Write-Host "============================================================`n"

# Start FastAPI backend
Write-Host "[1/3] Starting FastAPI Backend (http://localhost:8001)..."
$BackendProcess = Start-Process powershell -ArgumentList "-NoExit -Command `"python -m uvicorn backend.dashboard_api:app --host 0.0.0.0 --port 8001 --reload --reload-dir backend --reload-dir core --reload-dir hermes`"" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Determine dashboard folder
$DashboardDir = "kairos"
if (-not (Test-Path $DashboardDir)) {
    $DashboardDir = "dashboard"
}

# Install dashboard dependencies if needed
if (-not (Test-Path "$DashboardDir\node_modules")) {
    Write-Host "[2/3] Installing Node dependencies (first time only)..."
    Push-Location $DashboardDir
    & npm install --legacy-peer-deps
    Pop-Location
} else {
    Write-Host "[2/3] Starting dashboard (http://localhost:3000)..."
}

# Start dashboard
$DashboardProcess = Start-Process powershell -ArgumentList "-NoExit -Command `"cd $DashboardDir; npm run dev`"" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

# Start bot orchestrator
Write-Host "[3/3] Starting Bot/Swarm Orchestrator..."
$BotProcess = Start-Process powershell -ArgumentList "-NoExit -Command `"python bot_orchestrator.py`"" -PassThru -WindowStyle Normal

Write-Host "`n============================================================"
Write-Host "ALL SERVICES STARTED!" -ForegroundColor Green
Write-Host "============================================================`n"
Write-Host "Open your browser: http://localhost:3000`n"
Write-Host "Services:"
Write-Host "  - 3D Dashboard:  http://localhost:3000"
Write-Host "  - FastAPI Docs: http://localhost:8001/docs"
Write-Host "  - Bot Console:   Active in separate window`n"
Write-Host "Process IDs:"
Write-Host "  - Backend: $($BackendProcess.Id)"
Write-Host "  - Dashboard: $($DashboardProcess.Id)"
Write-Host "  - Bot: $($BotProcess.Id)`n"
Write-Host "============================================================`n"

if (-not $NoWait) {
    Write-Host "Press any key to exit (this will NOT stop the services)..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "Launcher closing. Services continue running in their windows.`n"


