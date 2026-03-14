Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$githubDesktopRoot = Join-Path $env:LOCALAPPDATA "GitHubDesktop"

if (-not (Test-Path $githubDesktopRoot)) {
  throw "GitHub Desktop folder was not found: $githubDesktopRoot"
}

$gitExe = Get-ChildItem $githubDesktopRoot -Recurse -Filter git.exe |
  Where-Object { $_.FullName -like '*\resources\app\git\cmd\git.exe' } |
  Sort-Object FullName -Descending |
  Select-Object -First 1

if (-not $gitExe) {
  throw "git.exe was not found inside GitHub Desktop."
}

$gitCmdDir = Split-Path $gitExe.FullName -Parent
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($userPath -split ";" | Where-Object { $_ -eq $gitCmdDir }) {
  Write-Host "Git is already in user PATH:" -ForegroundColor Green
  Write-Host $gitCmdDir
  exit 0
}

$newPath = if ([string]::IsNullOrWhiteSpace($userPath)) {
  $gitCmdDir
} else {
  "$userPath;$gitCmdDir"
}

[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "Git path added to user PATH:" -ForegroundColor Green
Write-Host $gitCmdDir
Write-Host ""
Write-Host "Restart PowerShell and run: git --version" -ForegroundColor Cyan
