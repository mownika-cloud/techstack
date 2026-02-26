#!/usr/bin/env python3
"""
Voice-to-Claude Code: Record audio from microphone and transcribe using Whisper AI.
Usage:
  python3 transcribe.py                  # Record until Ctrl+C, transcribe, print
  python3 transcribe.py -f audio.wav     # Transcribe an existing audio file
  python3 transcribe.py -m medium        # Use a specific Whisper model
  python3 transcribe.py -d 10            # Record for 10 seconds
"""

import argparse
import sys
import tempfile
import os

import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper


SAMPLE_RATE = 16000  # Whisper expects 16kHz


def has_input_device() -> bool:
    """Return True if at least one audio input device is available."""
    try:
        devices = sd.query_devices()
        if not devices:
            return False
        # query_devices() returns a dict for a single device, list for multiple
        if isinstance(devices, dict):
            devices = [devices]
        return any(d.get("max_input_channels", 0) > 0 for d in devices)
    except Exception:
        return False


def prompt_text_fallback() -> str:
    """Prompt the user to type their prompt when no mic is available."""
    print("No microphone detected — falling back to text input.", file=sys.stderr)
    print("Type your prompt below (Enter to finish, Ctrl+C to cancel):", file=sys.stderr)
    try:
        sys.stderr.write("> ")
        sys.stderr.flush()
        text = sys.stdin.readline().strip()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(0)
    return text


def record_audio(duration: int | None = None, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Record audio from the default microphone.

    If duration is None, records until the user presses Ctrl+C.
    Returns a numpy array of float32 audio samples.
    """
    if duration:
        print(f"Recording for {duration} seconds... (speak now)", file=sys.stderr)
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return audio.flatten()
    else:
        print("Recording... Press Ctrl+C to stop.", file=sys.stderr)
        frames = []
        block_size = 1024

        def callback(indata, frame_count, time_info, status):
            frames.append(indata.copy())

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size,
            callback=callback,
        ):
            try:
                while True:
                    sd.sleep(100)
            except KeyboardInterrupt:
                pass

        if not frames:
            return np.array([], dtype="float32")
        return np.concatenate(frames).flatten()


def record_with_options(duration: int | None, model_name: str, output: str | None) -> str:
    """Record audio, then ask: [S]end / [R]e-record / [C]ancel. Returns transcript."""
    while True:
        audio = record_audio(duration=duration)

        if audio.size == 0:
            print("No audio captured.", file=sys.stderr)
        else:
            # Save and transcribe
            if output:
                audio_path = output
                sf.write(audio_path, audio, SAMPLE_RATE)
                print(f"Audio saved to {audio_path}", file=sys.stderr)
                text = transcribe_audio(audio_path, model_name=model_name)
            else:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    audio_path = tmp.name
                try:
                    sf.write(audio_path, audio, SAMPLE_RATE)
                    text = transcribe_audio(audio_path, model_name=model_name)
                finally:
                    os.unlink(audio_path)

            if text:
                print(f"\nTranscribed: {text}", file=sys.stderr)

        print("\nWhat would you like to do?", file=sys.stderr)
        print("  [S] Send this transcription", file=sys.stderr)
        print("  [R] Re-record", file=sys.stderr)
        print("  [C] Cancel", file=sys.stderr)
        try:
            sys.stderr.write("Choice [S/R/C]: ")
            sys.stderr.flush()
            choice = sys.stdin.readline().strip().lower()
        except KeyboardInterrupt:
            print("\nCancelled.", file=sys.stderr)
            sys.exit(0)

        if choice in ("s", ""):
            if audio.size == 0 or not text:
                print("Nothing to send — please re-record.", file=sys.stderr)
                continue
            return text
        elif choice == "r":
            print("", file=sys.stderr)
            continue
        else:
            print("Cancelled.", file=sys.stderr)
            sys.exit(0)


def transcribe_audio(audio_path: str, model_name: str = "base") -> str:
    """Load Whisper model and transcribe the given audio file."""
    print(f"Loading Whisper '{model_name}' model...", file=sys.stderr)
    model = whisper.load_model(model_name)
    print("Transcribing...", file=sys.stderr)
    result = model.transcribe(audio_path)
    return result["text"].strip()


def main():
    parser = argparse.ArgumentParser(
        description="Record or load audio, then transcribe with Whisper AI."
    )
    parser.add_argument(
        "-f", "--file", metavar="AUDIO_FILE",
        help="Path to an existing audio file to transcribe (skips recording)."
    )
    parser.add_argument(
        "-m", "--model", default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to use (default: base)."
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=None,
        help="Recording duration in seconds. If omitted, records until Ctrl+C."
    )
    parser.add_argument(
        "-o", "--output", metavar="OUTPUT_FILE",
        help="Save the recorded audio to this WAV file."
    )
    args = parser.parse_args()

    if args.file:
        text = transcribe_audio(args.file, model_name=args.model)
    elif not has_input_device():
        # No mic available — fall back to typed input
        text = prompt_text_fallback()
    else:
        # Mic available — record with interactive Send/Re-record/Cancel prompt
        text = record_with_options(
            duration=args.duration,
            model_name=args.model,
            output=args.output,
        )

    if not text:
        print("No text produced.", file=sys.stderr)
        sys.exit(1)

    print(text)


if __name__ == "__main__":
    main()
