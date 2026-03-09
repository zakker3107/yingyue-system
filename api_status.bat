@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'SilentlyContinue'; Write-Host '[API Status]'; $resp = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 5; if ($resp) { Write-Host ('- Health: OK (' + $resp.StatusCode + ')'); Write-Host ('- Body: ' + $resp.Content) } else { Write-Host '- Health: DOWN' }; Write-Host '- Port 8000:'; netstat -ano | findstr :8000"
endlocal
pause
