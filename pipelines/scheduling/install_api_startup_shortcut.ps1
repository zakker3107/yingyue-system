param(
    [string]$ShortcutName = "YingYue API"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target = Join-Path $projectRoot "start_api_background.bat"
if (-not (Test-Path $target)) {
    throw "launcher not found: $target"
}

$startup = [Environment]::GetFolderPath("Startup")
$linkPath = Join-Path $startup ($ShortcutName + ".lnk")

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($linkPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $projectRoot
$sc.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,13"
$sc.Save()

Write-Host "[Startup] Installed shortcut: $linkPath"
Write-Host "[Startup] Target: $target"
