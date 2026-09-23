from __future__ import annotations

from ..providers.base import Direction
from .context import get_context
from ..models.db_models import add_history


async def transcribe(audio_bytes: bytes, direction: Direction, audio_ext: str | None = None) -> str:
    ctx = get_context()
    text = await ctx.stt.transcribe(audio_bytes, direction, audio_ext=audio_ext)
    add_history(ctx.db_path, direction=direction, kind="stt", input_text=None, output_text=text)
    return text
