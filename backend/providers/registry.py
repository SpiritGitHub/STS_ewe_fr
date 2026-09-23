from __future__ import annotations

from pathlib import Path

from ..core.settings import Settings

from .mock import MockMT, MockSTT, MockTTS
from .mt_local_transformers import LocalTransformersMT, TransformersMTConfig
from .stt_local_whisper import LocalWhisperSTT, WhisperSTTConfig


def build_providers(settings: Settings):
    # STT
    if settings.stt_provider == "mock":
        stt = MockSTT()
    elif settings.stt_provider == "local_whisper":
        stt = LocalWhisperSTT(
            WhisperSTTConfig(
                model_dir=settings.stt_model_dir or "",
                language=settings.whisper_language,
                task=settings.whisper_task,
            ),
            tmp_dir=settings.audio_storage_dir,
        )
    else:
        raise RuntimeError(f"Unsupported STT_PROVIDER={settings.stt_provider} (supported: mock, local_whisper)")

    # MT
    if settings.mt_provider == "mock":
        mt = MockMT()
    elif settings.mt_provider == "local_transformers":
        mt = LocalTransformersMT(
            TransformersMTConfig(
                model_dir_ee_to_fr=str(settings.mt_model_dir_ee_to_fr) if settings.mt_model_dir_ee_to_fr else None,
                model_dir_fr_to_ee=str(settings.mt_model_dir_fr_to_ee) if settings.mt_model_dir_fr_to_ee else None,
            )
        )
    else:
        raise RuntimeError(f"Unsupported MT_PROVIDER={settings.mt_provider}")

    # TTS
    if settings.tts_provider == "mock":
        tts = MockTTS(settings.audio_storage_dir)
    else:
        raise RuntimeError(f"Unsupported TTS_PROVIDER={settings.tts_provider} (only mock for now)")

    return stt, mt, tts
