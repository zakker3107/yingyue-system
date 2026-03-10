@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python scripts\optimize_environment.py
  exit /b 1
)

"%PY%" scripts\api_status.py
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
