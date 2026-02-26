#!/usr/bin/env bash
# install.sh — One-shot installer for Voice-to-Claude Code (Whisper AI)
set -euo pipefail

echo "=== Voice-to-Claude Code Installer ==="
echo ""

# 1. System dependencies
echo "[1/3] Installing system packages (ffmpeg, portaudio)..."
if command -v apt-get &>/dev/null; then
  apt-get install -y ffmpeg portaudio19-dev
elif command -v brew &>/dev/null; then
  brew install ffmpeg portaudio
else
  echo "WARNING: Cannot auto-install ffmpeg. Please install it manually." >&2
fi

# 2. Python packages
echo ""
echo "[2/3] Installing Python packages..."
pip3 install -r "$(dirname "$0")/requirements.txt"

# 3. Permissions
echo ""
echo "[3/3] Making scripts executable..."
chmod +x "$(dirname "$0")/voice-claude.sh"
chmod +x "$(dirname "$0")/transcribe.py"

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Quick start:"
echo "  # Record until Ctrl+C, transcribe, send to Claude Code:"
echo "  ./voice-claude.sh"
echo ""
echo "  # Transcribe only (no Claude):"
echo "  python3 transcribe.py"
echo ""
echo "  # Record 10 seconds with the 'small' model:"
echo "  ./voice-claude.sh -d 10 -m small"
echo ""
echo "Whisper models (accuracy vs speed trade-off):"
echo "  tiny < base < small < medium < large"
