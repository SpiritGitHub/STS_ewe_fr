from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .services.context import get_context
from .routes import history, sts, stt, translate, tts


def create_app() -> FastAPI:
    ctx = get_context()

    app = FastAPI(title="STS Ewe↔Fr Backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ctx.settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/audio/{audio_id}")
    def get_audio(audio_id: str):
        path = ctx.settings.audio_storage_dir / f"{audio_id}.wav"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Audio not found")
        return FileResponse(str(path), media_type="audio/wav", filename=path.name)

    app.include_router(stt.router)
    app.include_router(translate.router)
    app.include_router(tts.router)
    app.include_router(sts.router)
    app.include_router(history.router)

    return app


app = create_app()
