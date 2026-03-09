@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipelines\scheduling\install_api_task.ps1" -TaskName "YingYue-API" -Mode "local"
endlocal
pause
