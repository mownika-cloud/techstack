<#
.SYNOPSIS
    Start the Voice → Whisper → Claude browser-based server on Windows.

.DESCRIPTION
    run-voice-server.ps1 — Windows PowerShell equivalent of run-voice-server.sh

    Starts a local Flask web server. Open the printed URL in your browser,
    allow microphone access, then click Record and speak your command.
    Whisper transcribes it and sends it straight to Claude Code.

.EXAMPLE
    .\run-voice-server.ps1              # starts on http://localhost:5050
    .\run-voice-server.ps1 -Port 8080   # custom port

.NOTES
    Dependencies: python (with openai-whisper, flask), claude CLI
    Install deps:  pip install openai-whisper flask
#>

param(
    [Alias("p")][int]$Port = 5050
)

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ServerScript = Join-Path $ScriptDir "voice_server.py"

if (-not (Test-Path $ServerScript)) {
    Write-Error "voice_server.py not found at: $ServerScript"
    exit 1
}

# Resolve python binary (Windows may use 'python' rather than 'python3')
$PythonBin = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             else {
                 Write-Error "Python not found. Install Python 3 from https://python.org"
                 exit 1
             }

# Ensure Flask is installed
$flaskCheck = & $PythonBin -c "import flask" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Flask not found — installing..." -ForegroundColor Yellow
    & $PythonBin -m pip install flask --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Flask. Run: pip install flask"
        exit 1
    }
}

# Ensure Whisper CLI is available
$whisperCheck = Get-Command whisper -ErrorAction SilentlyContinue
if (-not $whisperCheck) {
    Write-Host "Whisper CLI not found — installing openai-whisper..." -ForegroundColor Yellow
    & $PythonBin -m pip install openai-whisper --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install openai-whisper. Run: pip install openai-whisper"
        exit 1
    }
}

Write-Host ""
Write-Host "  Starting Voice → Claude server..." -ForegroundColor Green
Write-Host "  Open http://localhost:$Port in your browser" -ForegroundColor Cyan
Write-Host "  Allow microphone access, click Record, and speak." -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host ""

& $PythonBin $ServerScript --port $Port
