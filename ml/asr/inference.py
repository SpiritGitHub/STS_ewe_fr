"""ASR inference (Whisper) for the demo.

This uses the same provider implementation as the backend (`backend.providers.LocalWhisperSTT`).

Usage (PowerShell)
  F:/STS/.venv/Scripts/python.exe ml/asr/inference.py `
    --model-dir models/asr_whisper_ewe `
    --audio data/ewe2/ewe/dev/EZR/EZR_001_Verse_000.flac `
    --direction ee_to_fr
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from backend.providers.base import Direction
from backend.providers.stt_local_whisper import LocalWhisperSTT, WhisperSTTConfig


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True, help="Path to a local Whisper model directory")
    ap.add_argument("--audio", required=True, help="Path to an audio file")
    ap.add_argument("--direction", choices=["ee_to_fr", "fr_to_ee"], default="ee_to_fr")
    ap.add_argument("--language", default="", help="Optional override (e.g. ewe, fra)")
    ap.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    args = ap.parse_args()

    repo_root = _repo_root()

    audio_path = Path(args.audio)
    if not audio_path.is_absolute():
        audio_path = (repo_root / audio_path).resolve()

    model_dir = Path(args.model_dir)
    if not model_dir.is_absolute():
        model_dir = (repo_root / model_dir).resolve()

    if not audio_path.exists():
        raise SystemExit(f"Audio not found: {audio_path}")

    storage_dir = (repo_root / "storage" / "audio")
    storage_dir.mkdir(parents=True, exist_ok=True)

    ext = audio_path.suffix.lower() or None

    stt = LocalWhisperSTT(
        WhisperSTTConfig(
            model_dir=str(model_dir),
            language=(args.language.strip() or None),
            task=args.task,
        ),
        tmp_dir=storage_dir,
    )

    audio_bytes = audio_path.read_bytes()
    direction: Direction = args.direction  # type: ignore[assignment]
    text = _run_async(stt.transcribe(audio_bytes, direction, audio_ext=ext))
    print(text)
    return 0


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Not expected for CLI; but keep safe.
        return asyncio.run(coro)

    return asyncio.run(coro)


if __name__ == "__main__":
    raise SystemExit(main())
