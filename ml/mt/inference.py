"""MT inference for the demo.

Uses backend's local Transformers MT provider (so behavior matches the API).

Usage (PowerShell)
  # ee -> fr
  F:/STS/.venv/Scripts/python.exe ml/mt/inference.py `
    --direction ee_to_fr `
    --model-dir models/mt_ee_to_fr `
    --text "Míele gbe Eʋegbe gblɔm."
"""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.providers.base import Direction
from backend.providers.mt_local_transformers import LocalTransformersMT, TransformersMTConfig


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", choices=["ee_to_fr", "fr_to_ee"], required=True)
    ap.add_argument("--model-dir", required=True, help="Path to the trained model directory for this direction")
    ap.add_argument("--text", required=True)
    args = ap.parse_args()

    repo_root = _repo_root()
    model_dir = Path(args.model_dir)
    if not model_dir.is_absolute():
        model_dir = (repo_root / model_dir).resolve()

    direction: Direction = args.direction  # type: ignore[assignment]

    cfg = TransformersMTConfig(
        model_dir_ee_to_fr=str(model_dir) if direction == "ee_to_fr" else None,
        model_dir_fr_to_ee=str(model_dir) if direction == "fr_to_ee" else None,
    )
    mt = LocalTransformersMT(cfg)

    out = _run_async(mt.translate(args.text, direction))
    print(out)
    return 0


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.run(coro)

    return asyncio.run(coro)


if __name__ == "__main__":
    raise SystemExit(main())
