param(
    [string]$TaskName = "YingYue-Daily-MVP"
)

$ErrorActionPreference = "Stop"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "[Task] Removed: $TaskName"
