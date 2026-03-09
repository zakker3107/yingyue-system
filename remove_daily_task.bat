@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipelines\scheduling\remove_daily_task.ps1" -TaskName "YingYue-Daily-Ops"
endlocal
pause
