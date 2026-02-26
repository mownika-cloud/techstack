#!/usr/bin/env bash
# voice-claude.sh — Record your voice, transcribe with Whisper, and pass the
#                   result directly to Claude Code as a prompt.
#
# Usage:
#   ./voice-claude.sh                  # Record until Ctrl+C, then run claude
#   ./voice-claude.sh -d 10            # Record 10 seconds, then run claude
#   ./voice-claude.sh -m small         # Use the 'small' Whisper model
#   ./voice-claude.sh -f audio.wav     # Transcribe existing file, then run claude
#   ./voice-claude.sh --dry-run        # Print the transcription; don't run claude
#
# Dependencies: python3, openai-whisper, sounddevice, soundfile, ffmpeg

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE_PY="${SCRIPT_DIR}/transcribe.py"

MODEL="base"
DURATION_FLAG=""
FILE_FLAG=""
DRY_RUN=false

usage() {
  grep '^#' "$0" | grep -v '^#!/' | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)      usage ;;
    -m|--model)     MODEL="$2"; shift 2 ;;
    -d|--duration)  DURATION_FLAG="-d $2"; shift 2 ;;
    -f|--file)      FILE_FLAG="-f $2"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Transcribe — write to a temp file so stdin stays connected to the terminal
TMPFILE="$(mktemp /tmp/voice-claude-XXXXXX.txt)"
trap 'rm -f "$TMPFILE"' EXIT

# shellcheck disable=SC2086
python3 "$TRANSCRIBE_PY" -m "$MODEL" $DURATION_FLAG $FILE_FLAG > "$TMPFILE" </dev/tty
TRANSCRIPT="$(cat "$TMPFILE")"

if [[ -z "$TRANSCRIPT" ]]; then
  echo "No transcription produced. Exiting." >&2
  exit 1
fi

echo ""
echo "=== Transcription ==="
echo "$TRANSCRIPT"
echo "====================="
echo ""

if $DRY_RUN; then
  echo "(Dry run — not sending to Claude Code)"
  exit 0
fi

# Pass transcription to Claude Code
if ! command -v claude &>/dev/null; then
  echo "claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code" >&2
  echo "Transcription saved below — paste it manually:" >&2
  echo "$TRANSCRIPT"
  exit 1
fi

echo "Sending to Claude Code..."
claude "$TRANSCRIPT"
