@echo off
setlocal
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
  echo [STOP] PID=%%P
  taskkill /PID %%P /F >nul 2>&1
)

echo [DONE] Requested stop for listeners on port 8000.
endlocal
pause
