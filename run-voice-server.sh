#!/usr/bin/env bash
# run-voice-server.sh — Start the Voice → Whisper → Claude local server.
#
# Usage:
#   ./run-voice-server.sh              # starts on port 5050
#   ./run-voice-server.sh --port 8080  # custom port
#
# Then open http://localhost:<port> in your browser, allow mic access, and speak.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
  echo "Flask not found — installing..."
  pip install flask --quiet --ignore-installed blinker
fi

# Ensure Whisper CLI is available
if ! command -v whisper &>/dev/null; then
  echo "Whisper CLI not found — installing openai-whisper..."
  pip install openai-whisper --quiet
fi

exec python3 "${SCRIPT_DIR}/voice_server.py" "$@"
