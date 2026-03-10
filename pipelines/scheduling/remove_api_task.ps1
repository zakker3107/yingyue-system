param(
    [string]$TaskName = "YingYue-API"
)

$ErrorActionPreference = "Stop"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "[Task] Removed: $TaskName"
