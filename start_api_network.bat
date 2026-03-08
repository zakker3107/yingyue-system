@echo off
REM Start API for local network access (without ngrok)
REM Allows access from other devices on the same network

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables for network access
set YINGYUE_API_HOST=0.0.0.0
set YINGYUE_API_PORT=8000

REM Start API
echo Starting YingYue API for network access...
echo.
echo Available at:
echo - Local:          http://127.0.0.1:8000
echo - Network:        http://YOUR_PC_IP:8000
echo.
echo To find your PC IP, run: ipconfig
echo.
python scripts\start_api.py

pause
