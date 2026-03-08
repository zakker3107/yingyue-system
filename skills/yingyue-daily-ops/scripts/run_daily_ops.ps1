param(
  [switch]$HealthOnly
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path '.venv/Scripts/python.exe')) {
  throw 'Missing virtual environment at .venv. Run: python -m venv .venv'
}

if ($HealthOnly) {
  .\.venv\Scripts\python.exe scripts\health_check.py --run-smoke
  .\.venv\Scripts\python.exe scripts\status_report.py
  exit 0
}

.\.venv\Scripts\python.exe scripts\run_mvp.py
.\.venv\Scripts\python.exe scripts\generate_daily_report.py
.\.venv\Scripts\python.exe scripts\health_check.py --run-smoke

