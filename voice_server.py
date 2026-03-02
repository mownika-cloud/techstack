#!/usr/bin/env python3
"""
voice_server.py — Local Flask server that lets the browser capture microphone
audio, transcribes it with the Whisper CLI, and pipes the result to Claude Code.

Flow:
  Browser mic (MediaRecorder) → POST /transcribe → whisper CLI → /result
  Then: copy transcription → paste into Claude, or click "Send to Claude"

Run with:
  python3 voice_server.py          # starts on http://localhost:5050
  python3 voice_server.py --port 8080
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# HTML / JS front-end (single-file, no external deps)
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice → Claude</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0d1117; color: #e6edf3;
    display: flex; flex-direction: column; align-items: center;
    min-height: 100vh; padding: 40px 20px;
  }
  h1 { font-size: 1.6rem; margin-bottom: 8px; }
  .subtitle { color: #8b949e; margin-bottom: 32px; font-size: .9rem; }
  .card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 28px; width: 100%; max-width: 600px;
  }
  .controls { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
  button {
    padding: 10px 22px; border: none; border-radius: 8px;
    font-size: .95rem; cursor: pointer; font-weight: 600;
    transition: opacity .15s;
  }
  button:disabled { opacity: .4; cursor: not-allowed; }
  #btnRecord  { background: #238636; color: #fff; }
  #btnStop    { background: #da3633; color: #fff; }
  #btnSend    { background: #1f6feb; color: #fff; }
  #btnCopy    { background: #30363d; color: #e6edf3; }
  .status {
    font-size: .85rem; color: #8b949e;
    margin-bottom: 14px; min-height: 18px;
  }
  .pulse { color: #f85149; animation: blink 1s infinite; }
  @keyframes blink { 50% { opacity: .3; } }
  label { font-size: .85rem; color: #8b949e; display: block; margin-bottom: 6px; }
  select, textarea {
    width: 100%; background: #0d1117; color: #e6edf3;
    border: 1px solid #30363d; border-radius: 6px;
    padding: 8px 10px; font-size: .9rem;
    font-family: inherit;
  }
  select { margin-bottom: 18px; }
  textarea { resize: vertical; min-height: 110px; margin-bottom: 14px; }
  .row { display: flex; gap: 10px; }
  audio { width: 100%; margin-bottom: 14px; border-radius: 6px; }
  #audioWrap { display: none; }
  .footer { margin-top: 24px; font-size: .8rem; color: #484f58; }
</style>
</head>
<body>
<h1>🎙️ Voice → Claude</h1>
<p class="subtitle">Speak → Whisper transcribes → Claude gets your prompt</p>

<div class="card">
  <label for="modelSel">Whisper model</label>
  <select id="modelSel">
    <option value="tiny">tiny  (fastest, ~39 MB)</option>
    <option value="base" selected>base  (good balance, ~74 MB)</option>
    <option value="small">small (better accuracy, ~244 MB)</option>
    <option value="medium">medium (high accuracy, ~769 MB)</option>
    <option value="large">large  (best, ~1550 MB)</option>
  </select>

  <div class="controls">
    <button id="btnRecord">⏺ Record</button>
    <button id="btnStop" disabled>⏹ Stop</button>
  </div>

  <div class="status" id="status">Ready — click Record and speak.</div>

  <div id="audioWrap">
    <label>Recorded audio</label>
    <audio id="audioPlayer" controls></audio>
  </div>

  <label for="transcript">Transcription</label>
  <textarea id="transcript" placeholder="Transcription will appear here…" readonly></textarea>

  <div class="row">
    <button id="btnCopy" disabled>📋 Copy</button>
    <button id="btnSend" disabled>🚀 Send to Claude</button>
  </div>
</div>

<p class="footer">Server: voice_server.py &nbsp;|&nbsp; Whisper CLI &nbsp;|&nbsp; Claude Code</p>

<script>
let mediaRecorder, audioChunks = [], audioBlob;

const btnRecord  = document.getElementById('btnRecord');
const btnStop    = document.getElementById('btnStop');
const btnCopy    = document.getElementById('btnCopy');
const btnSend    = document.getElementById('btnSend');
const statusEl   = document.getElementById('status');
const transcript = document.getElementById('transcript');
const audioWrap  = document.getElementById('audioWrap');
const audioPlayer= document.getElementById('audioPlayer');
const modelSel   = document.getElementById('modelSel');

function setStatus(msg, pulse=false) {
  statusEl.textContent = msg;
  statusEl.className = 'status' + (pulse ? ' pulse' : '');
}

btnRecord.addEventListener('click', async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = handleStop;
    mediaRecorder.start();
    btnRecord.disabled = true;
    btnStop.disabled = false;
    btnSend.disabled = true;
    btnCopy.disabled = true;
    transcript.value = '';
    audioWrap.style.display = 'none';
    setStatus('🔴 Recording… click Stop when done.', true);
  } catch (err) {
    setStatus('Mic access denied: ' + err.message);
  }
});

btnStop.addEventListener('click', () => {
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach(t => t.stop());
  btnStop.disabled = true;
  setStatus('Processing…');
});

async function handleStop() {
  audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
  audioPlayer.src = URL.createObjectURL(audioBlob);
  audioWrap.style.display = 'block';
  setStatus('Sending to Whisper…');

  const form = new FormData();
  form.append('audio', audioBlob, 'recording.webm');
  form.append('model', modelSel.value);

  try {
    const res  = await fetch('/transcribe', { method: 'POST', body: form });
    const data = await res.json();
    if (data.error) {
      setStatus('Error: ' + data.error);
    } else {
      transcript.value = data.text;
      btnCopy.disabled = false;
      btnSend.disabled = false;
      setStatus('Done! Review below, then Copy or Send to Claude.');
    }
  } catch (err) {
    setStatus('Request failed: ' + err.message);
  }
  btnRecord.disabled = false;
}

btnCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(transcript.value)
    .then(() => setStatus('Copied to clipboard!'))
    .catch(() => {
      transcript.select();
      document.execCommand('copy');
      setStatus('Copied!');
    });
});

btnSend.addEventListener('click', async () => {
  const text = transcript.value.trim();
  if (!text) return;
  btnSend.disabled = true;
  setStatus('Sending to Claude…');
  try {
    const res  = await fetch('/send_to_claude', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.error) {
      setStatus('Claude error: ' + data.error);
      btnSend.disabled = false;
    } else {
      setStatus('Sent! Check your terminal for Claude\'s response.');
    }
  } catch (err) {
    setStatus('Failed: ' + err.message);
    btnSend.disabled = false;
  }
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.files.get("audio")
    model = request.form.get("model", "base")

    if not audio_file:
        return jsonify({"error": "No audio file received"}), 400

    # Save uploaded webm/ogg blob to a temp file; ffmpeg (inside whisper) converts it
    suffix = ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        audio_file.save(tmp_path)

    try:
        out_dir = tempfile.mkdtemp()
        result = subprocess.run(
            [
                "whisper", tmp_path,
                "--model", model,
                "--output_format", "txt",
                "--output_dir", out_dir,
                "--fp16", "False",       # CPU-safe
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip() or "whisper failed"}), 500

        # whisper writes <basename>.txt in out_dir
        txt_files = list(Path(out_dir).glob("*.txt"))
        if not txt_files:
            return jsonify({"error": "No transcription output found"}), 500

        text = txt_files[0].read_text().strip()
        return jsonify({"text": text})

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Whisper timed out (>5 min)"}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        os.unlink(tmp_path)


@app.route("/send_to_claude", methods=["POST"])
def send_to_claude():
    data = request.get_json(force=True)
    text = (data or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    claude_bin = "claude"
    if not subprocess.run(["which", claude_bin], capture_output=True).returncode == 0:
        return jsonify({"error": "claude CLI not found"}), 500

    # Fire-and-forget in background so HTTP response returns quickly
    subprocess.Popen(
        [claude_bin, text],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Voice → Whisper → Claude local server")
    parser.add_argument("--port", type=int, default=5050, help="Port to listen on (default 5050)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default 0.0.0.0)")
    args = parser.parse_args()

    print(f"\n  Voice → Claude server running at http://localhost:{args.port}")
    print(f"  Open that URL in your browser, allow mic access, and start speaking.\n")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
