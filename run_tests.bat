@echo off
setlocal
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python venv not found: %PY%
  echo Run: python scripts\optimize_environment.py
  exit /b 1
)

echo [INFO] Running smoke test...
"%PY%" tests\test_pipeline_smoke.py
if errorlevel 1 (
  echo [ERROR] Smoke test failed.
  exit /b 1
)

echo [INFO] Running pytest suite (tests\ only)...
"%PY%" -m pytest -q tests
if errorlevel 1 (
  echo [ERROR] Pytest suite failed.
  exit /b 1
)

echo [INFO] All tests passed.
endlocal
pause
