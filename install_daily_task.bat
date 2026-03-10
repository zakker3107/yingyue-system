@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipelines\scheduling\install_daily_task.ps1" -TaskName "YingYue-Daily-Ops" -Time "08:30"
endlocal
pause
