from __future__ import annotations

import math
import uuid
import wave
from pathlib import Path

from .base import Direction, TTSResult


class MockSTT:
    async def transcribe(self, audio_bytes: bytes, direction: Direction, audio_ext: str | None = None) -> str:
        # Placeholder transcript.
        return "Míele gbe Eʋegbe gblɔm." if direction == "ee_to_fr" else "Je parle en français."


class MockMT:
    async def translate(self, text: str, direction: Direction) -> str:
        if not text:
            return ""
        if direction == "ee_to_fr":
            return "Je parle en éwé."
        return "Míele gbe Eʋegbe gblɔm."


class MockTTS:
    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir

    async def synthesize(self, text: str, direction: Direction) -> TTSResult:
        audio_id = str(uuid.uuid4())
        out = self._storage_dir / f"{audio_id}.wav"
        freq = 520.0 if direction == "ee_to_fr" else 330.0
        self._write_beep(out, freq_hz=freq)
        return TTSResult(audio_id=audio_id, audio_mime="audio/wav", audio_path=str(out))

    def _write_beep(self, path: Path, seconds: float = 1.2, freq_hz: float = 440.0, sr: int = 22050) -> None:
        nframes = int(seconds * sr)
        amp = 12000
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            for i in range(nframes):
                t = i / sr
                sample = int(amp * math.sin(2 * math.pi * freq_hz * t))
                wf.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))
