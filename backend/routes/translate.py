from __future__ import annotations

from fastapi import APIRouter

from ..providers.base import Direction
from ..services import translation_service

router = APIRouter(tags=["translate"])


@router.post("/api/translate")
async def translate(direction: Direction, text: str) -> dict:
    translation = await translation_service.translate(text, direction)
    return {"direction": direction, "input": (text or "").strip(), "translation": translation}
