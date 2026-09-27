# CipherLens — Environment Setup (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
#
# Creates a Python virtual environment and installs all dependencies.
# Requires: Python 3.10+ and pip.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== CipherLens Environment Setup ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

# Check Python
$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
try {
    $PyVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "Using Python $PyVersion"
} catch {
    Write-Host "Error: Python not found. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
$VenvDir = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir ..."
    & $Python -m venv $VenvDir
} else {
    Write-Host "Virtual environment already exists at $VenvDir"
}

# Activate and install
Write-Host "Installing dependencies ..."
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
. $ActivateScript
pip install --upgrade pip --quiet
pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "To activate the environment:"
Write-Host "  . $VenvDir\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Quick verification:"
Write-Host "  python -c 'import cipherlens; print(""CipherLens OK"")'"
Write-Host "  pytest"
