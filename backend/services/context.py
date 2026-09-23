from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import load_settings
from ..providers.registry import build_providers


@dataclass(frozen=True)
class AppContext:
    settings: any
    stt: any
    mt: any
    tts: any
    db_path: Path


_ctx: AppContext | None = None


def get_context() -> AppContext:
    global _ctx
    if _ctx is not None:
        return _ctx

    settings = load_settings()
    stt, mt, tts = build_providers(settings)

    # DB file lives in repo-root/database/app.db by default
    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "database" / "app.db"

    _ctx = AppContext(settings=settings, stt=stt, mt=mt, tts=tts, db_path=db_path)
    return _ctx
