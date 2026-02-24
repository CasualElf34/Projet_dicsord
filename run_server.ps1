#!/usr/bin/env pwsh
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " LIKOO SERVER LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install --upgrade -r requirements.txt

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Starting server..."     -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python server.py
