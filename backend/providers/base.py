from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


Direction = Literal["ee_to_fr", "fr_to_ee"]


@dataclass(frozen=True)
class TTSResult:
    audio_id: str
    audio_mime: str
    audio_path: str


class STTProvider(Protocol):
    async def transcribe(self, audio_bytes: bytes, direction: Direction, audio_ext: str | None = None) -> str: ...


class MTProvider(Protocol):
    async def translate(self, text: str, direction: Direction) -> str: ...


class TTSProvider(Protocol):
    async def synthesize(self, text: str, direction: Direction) -> TTSResult: ...
