# CutCrew one-line installer. Paste into PowerShell:
#   irm https://raw.githubusercontent.com/tohawk89/cutcrew/main/install.ps1 | iex
# Clones (or updates) CutCrew into .\cutcrew, then runs setup.ps1. Set $env:CUTCREW_DIR to choose the folder.

$ErrorActionPreference = "Stop"
$repo = "https://github.com/tohawk89/cutcrew.git"
$dir = if ($env:CUTCREW_DIR) { $env:CUTCREW_DIR } else { Join-Path (Get-Location) "cutcrew" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[..] Installing Git with winget" -ForegroundColor Yellow
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")
}

if (Test-Path (Join-Path $dir ".git")) {
    Write-Host "[..] Updating $dir" -ForegroundColor Yellow
    git -C $dir pull --ff-only
} else {
    Write-Host "[..] Cloning CutCrew into $dir" -ForegroundColor Yellow
    git clone $repo $dir
}

powershell -ExecutionPolicy Bypass -File (Join-Path $dir "setup.ps1")
Write-Host "`nTip: keep CutCrew on the same drive as your recordings, so Claude can hard-link them in (no copies)." -ForegroundColor DarkGray
