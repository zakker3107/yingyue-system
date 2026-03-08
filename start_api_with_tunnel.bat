@echo off
REM Start API with ngrok tunnel for internet access
REM Usage: run this batch file to start both API and ngrok tunnel

cd /d "%~dp0"

REM Check if ngrok is installed
where ngrok >nul 2>nul
if errorlevel 1 (
    echo ngrok not found. Installing ngrok...
    echo.
    echo 請下載 ngrok from https://ngrok.com/download
    echo 或使用 npm: npm install -g ngrok
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables for network access
set YINGYUE_API_HOST=0.0.0.0
set YINGYUE_API_PORT=8000

REM Start API in background
echo Starting YingYue API on 0.0.0.0:8000...
echo Local access: http://127.0.0.1:8000
start "YingYue API" cmd /k python scripts\start_api.py

REM Wait for API to start
echo Waiting 3 seconds for API to start...
timeout /t 3 /nobreak

REM Start ngrok tunnel
echo.
echo Starting ngrok tunnel...
echo.
ngrok http 8000

pause
