@echo off
setlocal
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  exit /b 1
)
"%PY%" scripts\quick_recovery.py --run-smoke %*
endlocal & exit /b %ERRORLEVEL%
