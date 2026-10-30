# CutCrew setup. Safe to run again any time (e.g. after moving this folder).
#   powershell -ExecutionPolicy Bypass -File setup.ps1          # everything needed to edit
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -WithObs # also install OBS Studio

param([switch]$WithObs)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$HyperFrames = "hyperframes@0.8.172"   # keep in step with animations/package.json

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")
}

function Ensure-Tool($command, $wingetId, $label) {
    if (Get-Command $command -ErrorAction SilentlyContinue) {
        Write-Host "[ok] $label" -ForegroundColor Green
        return
    }
    Write-Host "[..] Installing $label with winget" -ForegroundColor Yellow
    winget install --id $wingetId -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
}

Write-Host "`n== 1. Tools ==" -ForegroundColor Cyan
Ensure-Tool git Git.Git "Git"
Ensure-Tool ffmpeg Gyan.FFmpeg "FFmpeg"
Ensure-Tool node OpenJS.NodeJS.LTS "Node.js"
Ensure-Tool py Python.Python.3.12 "Python"
$nodeMajor = [int]((node --version).TrimStart("v").Split(".")[0])
if ($nodeMajor -lt 22) { throw "HyperFrames needs Node.js 22+, you have $(node --version). Run: winget upgrade OpenJS.NodeJS.LTS" }
if ($WithObs) { Ensure-Tool obs64 OBSProject.OBSStudio "OBS Studio" }

Write-Host "`n== 2. Your style files (first run only) ==" -ForegroundColor Cyan
# Your taste lives in these files and is never committed; start from the defaults.
$starter = @{
    "STYLE.md"           = "defaults\STYLE.md"
    "style.json"         = "defaults\style.json"
    "FEEDBACK.md"        = "defaults\FEEDBACK.md"
    "library\CREDITS.md" = "defaults\CREDITS.md"
}
foreach ($file in $starter.Keys) {
    if (Test-Path $file) { Write-Host "[ok] $file (kept yours)" -ForegroundColor Green }
    else { Copy-Item $starter[$file] $file; Write-Host "[new] $file" -ForegroundColor Yellow }
}
foreach ($dir in "projects", "library\music", "library\sfx") { New-Item -ItemType Directory -Force $dir | Out-Null }

Write-Host "`n== 3. Python environment (Parakeet transcriber) ==" -ForegroundColor Cyan
$py = ".venv\Scripts\python.exe"
$healthy = (Test-Path $py) -and ((& $py -c "print(1)" 2>$null) -eq "1")
if (-not $healthy) {
    if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }
    py -3 -m venv .venv
}
& $py -m pip install --upgrade pip -q
& $py -m pip install -r requirements.txt -q

Write-Host "`n== 4. Download Parakeet model (~2.4 GB, first run only) ==" -ForegroundColor Cyan
& $py -c "import onnx_asr; onnx_asr.load_model('nemo-parakeet-tdt-0.6b-v3'); onnx_asr.load_vad('silero'); print('[ok] Parakeet ready')"

Write-Host "`n== 5. Card fonts ==" -ForegroundColor Cyan
# The cards use two fonts that ship with Windows; they may not be redistributed, so copy them locally.
$fonts = "animations\assets\fonts"
New-Item -ItemType Directory -Force $fonts | Out-Null
foreach ($font in "SegUIVar.ttf", "bahnschrift.ttf") {
    $src = Join-Path $env:WINDIR "Fonts\$font"
    if (Test-Path "$fonts\$font") { Write-Host "[ok] $font" -ForegroundColor Green }
    elseif (Test-Path $src) { Copy-Item $src $fonts; Write-Host "[new] $font" -ForegroundColor Yellow }
    else { Write-Host "[!!] $font not found in Windows\Fonts; cards will fall back to a plain sans-serif" -ForegroundColor Red }
}

Write-Host "`n== 6. HyperFrames (animator) + its Claude Code skills ==" -ForegroundColor Cyan
Push-Location animations
npx --yes $HyperFrames doctor
# Core skills plus the two workflows this studio routes to.
npx --yes $HyperFrames skills update motion-graphics media-use
Write-Host 'Note: whisper-cpp, Kokoro, MusicGen and Docker are optional extras, not needed here.' -ForegroundColor DarkGray
Pop-Location

Write-Host "`n== 7. Claude Code ==" -ForegroundColor Cyan
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "[ok] Claude Code $(claude --version)" -ForegroundColor Green
} else {
    Write-Host "[!!] Claude Code not found. Install the desktop app (https://claude.ai/download)" -ForegroundColor Red
    Write-Host "     or the CLI:  irm https://claude.ai/install.ps1 | iex" -ForegroundColor Red
}

Write-Host "`nAll set. Open this folder in Claude Code and type /setup (first time) or /edit <project-name>." -ForegroundColor Green
