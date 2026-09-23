from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import Direction


@dataclass(frozen=True)
class TransformersMTConfig:
    model_dir_ee_to_fr: str | None
    model_dir_fr_to_ee: str | None


class LocalTransformersMT:
    """Local MT provider using Hugging Face Transformers.

    This provider is lazy-imported: it only requires transformers/torch if enabled.
    Expected model dirs are produced by scripts/train_mt_ewe_fr.py.
    """

    def __init__(self, cfg: TransformersMTConfig):
        self._cfg = cfg
        self._pipelines: dict[str, Any] = {}

    def _get_pipeline(self, direction: Direction):
        key = direction
        if key in self._pipelines:
            return self._pipelines[key]

        model_dir = self._cfg.model_dir_ee_to_fr if direction == "ee_to_fr" else self._cfg.model_dir_fr_to_ee
        if not model_dir:
            raise RuntimeError(
                f"Missing model dir for direction={direction}. Set MT_MODEL_DIR_EE_TO_FR / MT_MODEL_DIR_FR_TO_EE"
            )

        from transformers import pipeline  # type: ignore

        p = pipeline("translation", model=model_dir)
        self._pipelines[key] = p
        return p

    async def translate(self, text: str, direction: Direction) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        p = self._get_pipeline(direction)
        out = p(text, max_length=256)
        if isinstance(out, list) and out and isinstance(out[0], dict):
            return (out[0].get("translation_text") or "").strip()
        return str(out)
