<#
.SYNOPSIS
    Record your voice, transcribe with Whisper, and pass the result to Claude Code.

.DESCRIPTION
    voice-claude.ps1 — Windows PowerShell equivalent of voice-claude.sh

.EXAMPLE
    .\voice-claude.ps1                  # Record until Ctrl+C, then run claude
    .\voice-claude.ps1 -Duration 10     # Record 10 seconds, then run claude
    .\voice-claude.ps1 -Model small     # Use the 'small' Whisper model
    .\voice-claude.ps1 -File audio.wav  # Transcribe existing file, then run claude
    .\voice-claude.ps1 -DryRun          # Print the transcription; don't run claude

.NOTES
    Dependencies: python (with openai-whisper, sounddevice, soundfile), claude CLI
#>

param(
    [Alias("m")][string]$Model    = "base",
    [Alias("d")][int]   $Duration = 0,
    [Alias("f")][string]$File     = "",
    [switch]            $DryRun
)

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$TranscribePy = Join-Path $ScriptDir "transcribe.py"

if (-not (Test-Path $TranscribePy)) {
    Write-Error "transcribe.py not found at: $TranscribePy"
    exit 1
}

# Resolve python binary (Windows may use 'python' rather than 'python3')
$PythonBin = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             else {
                 Write-Error "Python not found. Install Python 3 from https://python.org"
                 exit 1
             }

# Build argument list
$PyArgs = @($TranscribePy, "-m", $Model)
if ($Duration -gt 0) { $PyArgs += @("-d", $Duration) }
if ($File -ne "")    { $PyArgs += @("-f", $File) }

# Run transcribe.py — write stdout to a temp file so stdin stays open for user input
$TmpFile = [System.IO.Path]::GetTempFileName()
try {
    & $PythonBin @PyArgs | Out-File -FilePath $TmpFile -Encoding utf8 -NoNewline
    $ExitCode = $LASTEXITCODE
} catch {
    Write-Error "Failed to run transcribe.py: $_"
    Remove-Item $TmpFile -ErrorAction SilentlyContinue
    exit 1
}

if ($ExitCode -ne 0) {
    Remove-Item $TmpFile -ErrorAction SilentlyContinue
    exit $ExitCode
}

$Transcript = (Get-Content $TmpFile -Raw -Encoding utf8).Trim()
Remove-Item $TmpFile -ErrorAction SilentlyContinue

if ([string]::IsNullOrWhiteSpace($Transcript)) {
    Write-Host "No transcription produced. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Transcription ===" -ForegroundColor Cyan
Write-Host $Transcript
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "(Dry run — not sending to Claude Code)" -ForegroundColor Yellow
    exit 0
}

# Pass transcription to Claude Code
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code" -ForegroundColor Red
    Write-Host "Transcription saved above — paste it manually."
    exit 1
}

Write-Host "Sending to Claude Code..." -ForegroundColor Green
claude $Transcript
