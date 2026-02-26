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
        audio_path = args.file
        text = transcribe_audio(audio_path, model_name=args.model)
    else:
        audio = record_audio(duration=args.duration)
        if audio.size == 0:
            print("No audio recorded.", file=sys.stderr)
            sys.exit(1)

        # Save to a temp file (or user-specified file)
        if args.output:
            audio_path = args.output
            sf.write(audio_path, audio, SAMPLE_RATE)
            print(f"Audio saved to {audio_path}", file=sys.stderr)
            text = transcribe_audio(audio_path, model_name=args.model)
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = tmp.name
            try:
                sf.write(audio_path, audio, SAMPLE_RATE)
                text = transcribe_audio(audio_path, model_name=args.model)
            finally:
                os.unlink(audio_path)

    print(text)


if __name__ == "__main__":
    main()
