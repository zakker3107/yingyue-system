@echo off
setlocal
set "PY=%~dp0.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
  exit /b 1
)

echo [1/3] Running test suite...
"%PY%" -m pytest -q tests
if errorlevel 1 (
  echo [ERROR] Test suite failed.
  exit /b 1
)

echo [2/3] Running health check with smoke test...
"%PY%" scripts\health_check.py --run-smoke
if errorlevel 1 (
  echo [ERROR] Health check failed.
  exit /b 1
)

echo [3/3] Generating daily report...
"%PY%" scripts\generate_daily_report.py
if errorlevel 1 (
  echo [ERROR] Daily report generation failed.
  exit /b 1
)

echo [SUCCESS] Daily check completed.
endlocal
pause