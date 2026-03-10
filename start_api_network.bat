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

set YINGYUE_API_HOST=0.0.0.0
set YINGYUE_API_PORT=8000

echo Starting YingYue API for network access...
echo.
echo Available at:
echo - Local console:  %URL%
echo - Local API:      http://127.0.0.1:8000
echo - Network API:    http://YOUR_PC_IP:8000
echo.
echo To find your PC IP, run: ipconfig
echo.
start "YingYue Console" "%URL%"
"%PY%" scripts\start_api.py
endlocal
pause
