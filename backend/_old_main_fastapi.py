from __future__ import annotations

import base64

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from core.settings import load_settings
from providers.base import Direction
from providers.registry import build_providers


settings = load_settings()
stt_provider, mt_provider, tts_provider = build_providers(settings)


app = FastAPI(title="STS Ewe↔Fr Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/stt")
async def stt(
    direction: Direction = Form(...),
    audio: UploadFile = File(...),
) -> dict:
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio")

     # Best-effort extension for local decoders
    ext = ""
    if audio.filename and "." in audio.filename:
        ext = "." + audio.filename.rsplit(".", 1)[-1]

    transcript = await stt_provider.transcribe(data, direction, audio_ext=ext or None)
    return {"direction": direction, "transcript": transcript}


@app.post("/api/translate")
async def translate(
    direction: Direction,
    text: str,
) -> dict:
    text = text.strip()
    translation = await mt_provider.translate(text, direction)
    return {"direction": direction, "input": text, "translation": translation}


@app.post("/api/tts")
async def tts(
    direction: Direction,
    text: str,
    return_base64: bool = False,
) -> dict:
    text = text.strip()
    tts_res = await tts_provider.synthesize(text, direction)

    out: dict = {
        "direction": direction,
        "text": text,
        "audio_id": tts_res.audio_id,
        "audio_url": f"/api/audio/{tts_res.audio_id}",
    }

    if return_base64:
        b = open(tts_res.audio_path, "rb").read()
        out["audio_base64"] = base64.b64encode(b).decode("ascii")
        out["audio_mime"] = tts_res.audio_mime

    return out


@app.get("/api/audio/{audio_id}")
def get_audio(audio_id: str):
    path = settings.audio_storage_dir / f"{audio_id}.wav"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(str(path), media_type="audio/wav", filename=path.name)


@app.post("/api/sts")
async def sts(
    direction: Direction = Form(...),
    audio: UploadFile = File(...),
    return_audio_base64: bool = Form(False),
) -> dict:
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio")

    ext = ""
    if audio.filename and "." in audio.filename:
        ext = "." + audio.filename.rsplit(".", 1)[-1]

    transcript = await stt_provider.transcribe(data, direction, audio_ext=ext or None)
    translation = await mt_provider.translate(transcript, direction)
    tts_res = await tts_provider.synthesize(translation, direction)

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
        result["tts"]["audio_base64"] = base64.b64encode(open(tts_res.audio_path, "rb").read()).decode("ascii")

    return result
