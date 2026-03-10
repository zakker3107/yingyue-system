param(
    [string]$TaskName = "YingYue-Daily-Ops"
)

$ErrorActionPreference = "Stop"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "[Task] Removed: $TaskName"
