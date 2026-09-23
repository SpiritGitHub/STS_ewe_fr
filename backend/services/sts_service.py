from __future__ import annotations

from ..providers.base import Direction
from .context import get_context
from ..models.db_models import add_history


async def speech_to_speech(audio_bytes: bytes, direction: Direction, audio_ext: str | None = None):
    ctx = get_context()

    transcript = await ctx.stt.transcribe(audio_bytes, direction, audio_ext=audio_ext)
    translation = await ctx.mt.translate(transcript, direction)
    tts_res = await ctx.tts.synthesize(translation, direction)

    add_history(
        ctx.db_path,
        direction=direction,
        kind="sts",
        input_text=transcript,
        output_text=translation,
    )

    return transcript, translation, tts_res
