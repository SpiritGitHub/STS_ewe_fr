from __future__ import annotations

import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..providers.base import Direction
from ..services import sts_service

router = APIRouter(tags=["sts"])


@router.post("/api/sts")
async def sts(direction: Direction = Form(...), audio: UploadFile = File(...), return_audio_base64: bool = Form(False)) -> dict:
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio")

    ext = None
    if audio.filename and "." in audio.filename:
        ext = "." + audio.filename.rsplit(".", 1)[-1]

    transcript, translation, tts_res = await sts_service.speech_to_speech(data, direction, audio_ext=ext)

    result: dict = {
        "direction": direction,
        "transcript": transcript,
        "translation": translation,
        "tts": {
            "audio_id": tts_res.audio_id,
            "audio_url": f"/api/audio/{tts_res.audio_id}",
            "audio_mime": tts_res.audio_mime,
        },
    }

    if return_audio_base64:
        with open(tts_res.audio_path, "rb") as f:
            result["tts"]["audio_base64"] = base64.b64encode(f.read()).decode("ascii")

    return result
