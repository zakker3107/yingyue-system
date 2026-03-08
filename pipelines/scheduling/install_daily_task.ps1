param(
    [string]$TaskName = "YingYue-Daily-MVP",
    [string]$Time = "08:30"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$jobScript = Join-Path $projectRoot "pipelines\scheduling\daily_job.ps1"

if (-not (Test-Path $jobScript)) {
    throw "daily_job.ps1 not found: $jobScript"
}

$atTime = [datetime]::ParseExact($Time, "HH:mm", $null)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$jobScript`""
$trigger = New-ScheduledTaskTrigger -Daily -At $atTime
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null

Write-Host "[Task] Installed: $TaskName"
Write-Host "[Task] Schedule: Daily at $Time"
Write-Host "[Task] Script: $jobScript"
