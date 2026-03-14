Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Step([string]$message) {
  Write-Host ""
  Write-Host $message -ForegroundColor Cyan
}

function Ensure-Command([string]$name, [string]$hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw $hint
  }
}

Step "[1/6] Checking required tools"
Ensure-Command "python" "Python was not found in PATH."
Ensure-Command "npm" "npm was not found in PATH."

Step "[2/6] Installing JavaScript dependencies"
npm install

Step "[3/6] Building frontend"
npm run build

Step "[4/6] Installing PyInstaller"
python -m pip install pyinstaller

Step "[5/6] Preparing build directories"
New-Item -ItemType Directory -Force -Path "app_data" | Out-Null
New-Item -ItemType Directory -Force -Path "app_data\exports" | Out-Null
New-Item -ItemType Directory -Force -Path "app_data\uploads" | Out-Null

if (Test-Path "build\pyinstaller") {
  Remove-Item "build\pyinstaller" -Recurse -Force
}
if (Test-Path "build\spec") {
  Remove-Item "build\spec" -Recurse -Force
}
if (Test-Path "release") {
  Remove-Item "release" -Recurse -Force
}

Step "[6/6] Packaging desktop app into EXE"
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name "ArchiveInvestigations" `
  --distpath "release" `
  --workpath "build\pyinstaller" `
  --specpath "build\spec" `
  --collect-submodules backend `
  --collect-all fastapi `
  --collect-all uvicorn `
  --collect-all starlette `
  --collect-all anyio `
  --collect-all pydantic `
  --collect-all pydantic_core `
  --add-data "$root\dist;dist" `
  --add-data "$root\backend;backend" `
  --add-data "$root\app_data;app_data" `
  desktop_app.py

Write-Host ""
Write-Host "Build completed." -ForegroundColor Green
Write-Host "EXE: $root\release\ArchiveInvestigations\ArchiveInvestigations.exe" -ForegroundColor Green
