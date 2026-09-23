from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]
    audio_storage_dir: Path

    stt_provider: str
    mt_provider: str
    tts_provider: str

    stt_model_dir: str | None
    whisper_language: str | None
    whisper_task: str

    # Optional local model directories
    mt_model_dir_ee_to_fr: Path | None
    mt_model_dir_fr_to_ee: Path | None


def _parse_csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default).strip()
    return [s.strip() for s in raw.split(",") if s.strip()]


def _parse_path_env(name: str) -> Path | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    return Path(raw)


def load_settings() -> Settings:
    cors_origins = _parse_csv_env("CORS_ORIGINS", "http://localhost:5173")

    storage = os.getenv("AUDIO_STORAGE_DIR", "storage/audio").strip()
    backend_root = Path(__file__).resolve().parents[2]
    audio_dir = (backend_root / storage).resolve()
    audio_dir.mkdir(parents=True, exist_ok=True)

    stt_provider = os.getenv("STT_PROVIDER", "mock").strip()
    mt_provider = os.getenv("MT_PROVIDER", "mock").strip()
    tts_provider = os.getenv("TTS_PROVIDER", "mock").strip()

    stt_model_dir = os.getenv("STT_MODEL_DIR", "").strip() or None
    whisper_language = os.getenv("WHISPER_LANGUAGE", "").strip() or None
    whisper_task = os.getenv("WHISPER_TASK", "transcribe").strip() or "transcribe"

    return Settings(
        cors_origins=cors_origins,
        audio_storage_dir=audio_dir,
        stt_provider=stt_provider,
        mt_provider=mt_provider,
        tts_provider=tts_provider,

        stt_model_dir=stt_model_dir,
        whisper_language=whisper_language,
        whisper_task=whisper_task,
        mt_model_dir_ee_to_fr=_parse_path_env("MT_MODEL_DIR_EE_TO_FR"),
        mt_model_dir_fr_to_ee=_parse_path_env("MT_MODEL_DIR_FR_TO_EE"),
    )
