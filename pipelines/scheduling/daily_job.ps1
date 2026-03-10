param(
    [string]$PythonPath = "",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Label,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    Write-Host "[DailyJob] Step: $Label"
    & $PythonPath $ScriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$ScriptPath failed with exit code $LASTEXITCODE"
    }
}

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
$jobFailed = $false
$jobError = $null
try {
    Invoke-Step -Label "Run MVP pipeline" -ScriptPath "scripts\run_mvp.py"
    Invoke-Step -Label "Generate daily report" -ScriptPath "scripts\generate_daily_report.py"
    Invoke-Step -Label "Run health check" -ScriptPath "scripts\health_check.py" -Arguments @("--run-smoke")
} catch {
    $jobFailed = $true
    $jobError = $_
    Write-Warning "[DailyJob] Main job failed: $($_.Exception.Message)"
} finally {
    try {
        Invoke-Step -Label "Generate status report" -ScriptPath "scripts\status_report.py"
    } catch {
        $jobFailed = $true
        if (-not $jobError) {
            $jobError = $_
        }
        Write-Warning "[DailyJob] Status report failed: $($_.Exception.Message)"
    }
    Pop-Location
}

if ($jobFailed) {
    throw $jobError
}

Write-Host "[DailyJob] Completed successfully"
