param(
    [string]$TaskName = "YingYue-API",
    [ValidateSet("local", "network")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$launcher = if ($Mode -eq "network") {
    Join-Path $projectRoot "start_api_network_background.bat"
} else {
    Join-Path $projectRoot "start_api_background.bat"
}
$startupInstaller = Join-Path $PSScriptRoot "install_api_startup_shortcut.ps1"

if (-not (Test-Path $launcher)) {
    throw "launcher not found: $launcher"
}

function Get-TaskUserId {
    try {
        $dailyPrincipal = (Get-ScheduledTask -TaskName "YingYue-Daily-MVP" -ErrorAction Stop).Principal.UserId
        if ($dailyPrincipal) {
            return $dailyPrincipal
        }
    } catch {
    }

    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ($identity -and $identity.Contains("\")) {
        return $identity.Split("\")[-1]
    }
    return $env:USERNAME
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$launcher`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId (Get-TaskUserId) -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    Write-Host "[Task] Installed: $TaskName"
    Write-Host "[Task] Mode: $Mode"
    Write-Host "[Task] Launcher: $launcher"
    Write-Host "[Task] Trigger: At logon"
} catch {
    if ($_.Exception.Message -match "Access is denied" -or $_.FullyQualifiedErrorId -match "0x80070005") {
        if (-not (Test-Path $startupInstaller)) {
            throw
        }

        & $startupInstaller -ShortcutName "YingYue API"
        Write-Warning "Task Scheduler registration was denied by Windows. Installed Startup shortcut fallback instead."
        Write-Host "[Fallback] Startup target: $launcher"
    } else {
        throw
    }
}
