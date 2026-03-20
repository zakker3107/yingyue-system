@echo off
setlocal
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
  exit /b 1
)
"%PY%" scripts\task_status.py %*
endlocal & exit /b %ERRORLEVEL%
