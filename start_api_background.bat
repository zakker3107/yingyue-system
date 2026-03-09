@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
set "SCRIPT=%~dp0scripts\start_api_local.py"
set "URL=http://127.0.0.1:8000/console/dashboard"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python scripts\optimize_environment.py
  exit /b 1
)
if not exist "%SCRIPT%" (
  echo [ERROR] Background launcher not found: %SCRIPT%
  exit /b 1
)

powershell -NoProfile -Command "Start-Process -FilePath '%PY%' -ArgumentList '%SCRIPT%' -WorkingDirectory '%~dp0'"
start "YingYue Console" "%URL%"
echo [OK] Started YingYue API in background mode
echo [OPEN] %URL%
endlocal & exit /b 0
