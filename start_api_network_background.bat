@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
set "URL=http://127.0.0.1:8000/console/dashboard"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python scripts\optimize_environment.py
  exit /b 1
)

"%PY%" scripts\launch_api_background.py network
if errorlevel 1 exit /b %errorlevel%

start "YingYue Console" "%URL%"
echo [OPEN] %URL%
echo [API]  http://YOUR_PC_IP:8000
endlocal & exit /b 0
