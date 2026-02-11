# ==========================================
#  RotorDyn Windows .exe Build Script
# ==========================================
#  Usage: Right-click -> Run with PowerShell
#  Or:    powershell -ExecutionPolicy Bypass -File build_windows.ps1
# ==========================================

$ErrorActionPreference = "Stop"

Write-Host "`n===================================="
Write-Host "  RotorDyn Windows Build Script"
Write-Host "====================================`n"

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] $pyVersion"
} catch {
    Write-Host "[ERROR] Python not found! Install Python 3.12+ from https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

# Create venv
Write-Host "`n[1/4] Creating virtual environment..."
python -m venv .venv

# Install deps
Write-Host "[2/4] Installing dependencies..."
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -e .
.\.venv\Scripts\pip install pyinstaller pywebview

# Build
Write-Host "[3/4] Building .exe..."
.\.venv\Scripts\pyinstaller main.py `
    --name RotorDyn `
    --onedir `
    --windowed `
    --noconfirm `
    --clean `
    --collect-all nicegui `
    --hidden-import plotly `
    --hidden-import engineio.async_drivers.aiohttp

Write-Host "`n[4/4] Build complete!"
Write-Host "`n===================================="
Write-Host "  Output: dist\RotorDyn\RotorDyn.exe"
Write-Host "===================================="
Write-Host "`nDouble-click RotorDyn.exe to run!`n"

Read-Host "Press Enter to exit"
