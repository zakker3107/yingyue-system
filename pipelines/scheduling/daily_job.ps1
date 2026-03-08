param(
    [string]$PythonPath = "",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

if (-not $PythonPath) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonPath = $venvPython
    } else {
        $PythonPath = "python"
    }
}

Write-Host "[DailyJob] ProjectRoot: $ProjectRoot"
Write-Host "[DailyJob] PythonPath: $PythonPath"

Push-Location $ProjectRoot
try {
    & $PythonPath "scripts\run_mvp.py"
    if ($LASTEXITCODE -ne 0) {
        throw "run_mvp.py failed with exit code $LASTEXITCODE"
    }

    & $PythonPath "scripts\generate_daily_report.py"
    if ($LASTEXITCODE -ne 0) {
        throw "generate_daily_report.py failed with exit code $LASTEXITCODE"
    }

    Write-Host "[DailyJob] Completed successfully"
} finally {
    Pop-Location
}
