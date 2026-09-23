"""TTS inference.

Right now the project only ships a mock TTS provider (beep WAV) used by the demo.
This CLI lets you generate the same WAV output as the backend.

Usage (PowerShell)
  F:/STS/.venv/Scripts/python.exe ml/tts/inference.py `
    --direction ee_to_fr `
    --text "Bonjour" `
    --out-wav storage/audio/out.wav
"""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.providers.base import Direction
from backend.providers.mock import MockTTS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", choices=["ee_to_fr", "fr_to_ee"], required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--out-wav", default="storage/audio/tts_out.wav")
    args = ap.parse_args()

    repo_root = _repo_root()
    out_path = Path(args.out_wav)
    if not out_path.is_absolute():
        out_path = (repo_root / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    storage_dir = out_path.parent
    tts = MockTTS(storage_dir)

    direction: Direction = args.direction  # type: ignore[assignment]
    res = _run_async(tts.synthesize(args.text, direction))

    # MockTTS chooses a random UUID filename; copy to deterministic output path.
    generated = Path(res.audio_path)
    out_path.write_bytes(generated.read_bytes())

    print(str(out_path))
    return 0


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.run(coro)

    return asyncio.run(coro)


if __name__ == "__main__":
    raise SystemExit(main())
