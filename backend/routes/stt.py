from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..providers.base import Direction
from ..services import stt_service

router = APIRouter(tags=["stt"])


@router.post("/api/stt")
async def stt(direction: Direction = Form(...), audio: UploadFile = File(...)) -> dict:
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio")

    ext = None
    if audio.filename and "." in audio.filename:
        ext = "." + audio.filename.rsplit(".", 1)[-1]

    transcript = await stt_service.transcribe(data, direction, audio_ext=ext)
    return {"direction": direction, "transcript": transcript}
