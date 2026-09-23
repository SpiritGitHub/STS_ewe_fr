from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import Direction


@dataclass(frozen=True)
class WhisperSTTConfig:
    model_dir: str
    language: str | None = None  # e.g. "ewe" or "fr"
    task: str = "transcribe"  # "transcribe" or "translate"


class LocalWhisperSTT:
    """Local STT provider using Hugging Face Transformers ASR pipeline.

    Notes
    - This provider expects the incoming audio bytes to be a valid audio file.
    - We persist bytes to a temporary file, then run the ASR pipeline on the path.
    - Dependencies are optional and imported lazily.
    """

    def __init__(self, cfg: WhisperSTTConfig, tmp_dir: Path):
        self._cfg = cfg
        self._tmp_dir = tmp_dir
        self._pipeline: Any | None = None

    def _get_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline

        # Lazy imports (heavy)
        try:
            import torch  # type: ignore
            from transformers import pipeline  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Missing deps for LocalWhisperSTT. Install: torch transformers accelerate soundfile"
            ) from e

        device = 0 if torch.cuda.is_available() else -1
        self._pipeline = pipeline(
            task="automatic-speech-recognition",
            model=self._cfg.model_dir,
            device=device,
        )
        return self._pipeline

    async def transcribe(self, audio_bytes: bytes, direction: Direction, audio_ext: str | None = None) -> str:
        if not audio_bytes:
            return ""

        # Heuristic: if direction is fr_to_ee, language could be French; otherwise Ewe.
        lang = self._cfg.language
        if not lang:
            lang = "fra" if direction == "fr_to_ee" else "ewe"

        ext = (audio_ext or ".wav").strip().lower()
        if not ext.startswith("."):
            ext = "." + ext

        self._tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._tmp_dir / f"upload_{uuid.uuid4().hex}{ext}"
        tmp_path.write_bytes(audio_bytes)

        try:
            p = self._get_pipeline()

            # Some Whisper pipelines accept generate_kwargs.
            kwargs = {"generate_kwargs": {"task": self._cfg.task}}
            # Whisper expects language tokens; many configs accept language as a string.
            kwargs["generate_kwargs"]["language"] = lang

            out = p(str(tmp_path), **kwargs)
            if isinstance(out, dict) and "text" in out:
                return str(out["text"]).strip()
            return str(out).strip()
        finally:
            # Best-effort cleanup.
            try:
                tmp_path.unlink(missing_ok=True)  # py3.8+: ok
            except Exception:
                pass
