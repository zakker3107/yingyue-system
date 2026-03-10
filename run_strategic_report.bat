@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\generate_strategic_report.py %*
) else (
  python scripts\generate_strategic_report.py %*
)
endlocal
