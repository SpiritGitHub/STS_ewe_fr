r"""Train all models (ASR + MT) from a single Python entrypoint.

Runs the main training entrypoints under ml/.

Usage examples:
  # Quick smoke run (small max-train/max-eval)
  .\.venv\Scripts\python.exe ml/train_all.py --quick

  # Full runs (no caps)
  .\.venv\Scripts\python.exe ml/train_all.py

  # Resume from latest checkpoints
  .\.venv\Scripts\python.exe ml/train_all.py --resume auto

  # Only MT (both directions)
  .\.venv\Scripts\python.exe ml/train_all.py --no-asr

  # Only ASR
  .\.venv\Scripts\python.exe ml/train_all.py --no-mt
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@dataclass(frozen=True)
class RunConfig:
    quick: bool
    resume: str

    asr_manifest: str
    asr_model: str
    asr_out_dir: str
    asr_max_train: int
    asr_max_eval: int

    mt_manifest: str
    mt_model: str
    mt_out_dir_ee_to_fr: str
    mt_out_dir_fr_to_ee: str
    mt_max_train: int
    mt_max_eval: int

    run_asr: bool
    run_mt: bool


def _run(cmd: list[str]) -> None:
    print("\n$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument(
        "--resume",
        default="",
        help="Pass-through to training scripts. Use 'auto' to resume from latest checkpoint in each output dir.",
    )

    ap.add_argument("--no-asr", action="store_true")
    ap.add_argument("--no-mt", action="store_true")

    ap.add_argument("--asr-manifest", default="data/manifests/asr/manifest_ewe2_audio.tsv")
    ap.add_argument("--asr-model", default="openai/whisper-small")
    ap.add_argument("--asr-out-dir", default="models/asr_whisper_ewe")

    ap.add_argument("--mt-manifest", default="data/manifests/mt/manifest_ewe_fr_bitext.tsv")
    ap.add_argument("--mt-model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--mt-out-dir-ee-to-fr", default="models/mt_ee_to_fr")
    ap.add_argument("--mt-out-dir-fr-to-ee", default="models/mt_fr_to_ee")

    args = ap.parse_args()

    repo_root = _repo_root()

    quick = bool(args.quick)

    cfg = RunConfig(
        quick=quick,
        resume=(args.resume or "").strip(),
        asr_manifest=args.asr_manifest,
        asr_model=args.asr_model,
        asr_out_dir=args.asr_out_dir,
        asr_max_train=5000 if quick else 0,
        asr_max_eval=500 if quick else 0,
        mt_manifest=args.mt_manifest,
        mt_model=args.mt_model,
        mt_out_dir_ee_to_fr=args.mt_out_dir_ee_to_fr,
        mt_out_dir_fr_to_ee=args.mt_out_dir_fr_to_ee,
        mt_max_train=20000 if quick else 0,
        mt_max_eval=2000 if quick else 0,
        run_asr=not args.no_asr,
        run_mt=not args.no_mt,
    )

    py = sys.executable

    if cfg.run_mt:
        mt_script = os.path.join(repo_root, "ml", "mt", "train_mt.py")

        for direction, out_dir in (
            ("ee_to_fr", cfg.mt_out_dir_ee_to_fr),
            ("fr_to_ee", cfg.mt_out_dir_fr_to_ee),
        ):
            cmd = [
                py,
                mt_script,
                "--manifest",
                cfg.mt_manifest,
                "--direction",
                direction,
                "--model",
                cfg.mt_model,
                "--out-dir",
                out_dir,
            ]
            if cfg.mt_max_train:
                cmd += ["--max-train", str(cfg.mt_max_train)]
            if cfg.mt_max_eval:
                cmd += ["--max-eval", str(cfg.mt_max_eval)]
            if cfg.resume:
                cmd += ["--resume-from", cfg.resume]

            _run(cmd)

    if cfg.run_asr:
        asr_script = os.path.join(repo_root, "ml", "asr", "train_asr.py")
        cmd = [
            py,
            asr_script,
            "--manifest",
            cfg.asr_manifest,
            "--model",
            cfg.asr_model,
            "--out-dir",
            cfg.asr_out_dir,
        ]
        if cfg.asr_max_train:
            cmd += ["--max-train", str(cfg.asr_max_train)]
        if cfg.asr_max_eval:
            cmd += ["--max-eval", str(cfg.asr_max_eval)]
        if cfg.resume:
            cmd += ["--resume-from", cfg.resume]

        _run(cmd)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
