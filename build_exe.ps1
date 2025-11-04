
# Build your Flask app into a single EXE with PyInstaller
# Usage:
#   Right-click -> Run with PowerShell
#   or: Set-ExecutionPolicy -Scope Process Bypass -Force; .\build_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-Not (Test-Path ".venv")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
  python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
if (Test-Path "requirements.txt") { pip install -r requirements.txt }
pip install pyinstaller

$addDataArgs = @()
if (Test-Path "templates") { $addDataArgs += "--add-data"; $addDataArgs += "templates;templates" }
if (Test-Path "static")    { $addDataArgs += "--add-data"; $addDataArgs += "static;static" }

pyinstaller `
  --noconfirm `
  --onefile `
  --name TelegramAdminApp `
  --console `
  --collect-all flask `
  --collect-all sqlalchemy `
  --collect-all jinja2 `
  --collect-all werkzeug `
  --collect-all psycopg2 `
  $addDataArgs `
  app.py

Write-Host "`nBuild finished." -ForegroundColor Green
Write-Host "Find your EXE under .\dist\TelegramAdminApp.exe" -ForegroundColor Green
Write-Host "Place a .env next to the EXE (copy from .env.example if needed)." -ForegroundColor Green
