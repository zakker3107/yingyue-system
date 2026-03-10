param(
    [string]$ShortcutName = "YingYue API"
)

$ErrorActionPreference = "Stop"
$startup = [Environment]::GetFolderPath("Startup")
$linkPath = Join-Path $startup ($ShortcutName + ".lnk")

if (Test-Path $linkPath) {
    Remove-Item $linkPath -Force
    Write-Host "[Startup] Removed shortcut: $linkPath"
} else {
    Write-Host "[Startup] Shortcut not found: $linkPath"
}
