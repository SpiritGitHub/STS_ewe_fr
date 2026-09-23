from __future__ import annotations

import base64

from fastapi import APIRouter

from ..providers.base import Direction
from ..services import tts_service

router = APIRouter(tags=["tts"])


@router.post("/api/tts")
async def tts(direction: Direction, text: str, return_base64: bool = False) -> dict:
    tts_res = await tts_service.synthesize(text, direction)

    out: dict = {
        "direction": direction,
        "text": (text or "").strip(),
        "audio_id": tts_res.audio_id,
        "audio_url": f"/api/audio/{tts_res.audio_id}",
        "audio_mime": tts_res.audio_mime,
    }

    if return_base64:
        b = open(tts_res.audio_path, "rb").read()
        out["audio_base64"] = base64.b64encode(b).decode("ascii")

    return out
