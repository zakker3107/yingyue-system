@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\generate_weekly_ai_review.py %*
) else (
  python scripts\generate_weekly_ai_review.py %*
)
endlocal
