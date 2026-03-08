@echo off
setlocal
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
  exit /b 1
)
"%PY%" scripts\status_report.py %*
set "EXITCODE=%ERRORLEVEL%"
if %EXITCODE% NEQ 0 (
  echo [WARN] status report indicates FAIL
)
endlocal & exit /b %EXITCODE%
