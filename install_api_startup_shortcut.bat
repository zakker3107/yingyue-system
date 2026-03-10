@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipelines\scheduling\install_api_startup_shortcut.ps1" -ShortcutName "YingYue API"
endlocal
pause