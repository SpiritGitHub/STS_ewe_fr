from __future__ import annotations

from ..providers.base import Direction
from .context import get_context
from ..models.db_models import add_history


async def synthesize(text: str, direction: Direction):
    ctx = get_context()
    text = (text or "").strip()
    res = await ctx.tts.synthesize(text, direction)
    add_history(ctx.db_path, direction=direction, kind="tts", input_text=text, output_text=None)
    return res
