from __future__ import annotations

from ..providers.base import Direction
from .context import get_context
from ..models.db_models import add_history


async def translate(text: str, direction: Direction) -> str:
    ctx = get_context()
    text = (text or "").strip()
    out = await ctx.mt.translate(text, direction)
    add_history(ctx.db_path, direction=direction, kind="translate", input_text=text, output_text=out)
    return out
