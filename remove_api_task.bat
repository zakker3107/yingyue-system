@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipelines\scheduling\remove_api_task.ps1" -TaskName "YingYue-API"
endlocal
pause
