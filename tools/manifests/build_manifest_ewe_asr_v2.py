"""Rebuild a clean ASR manifest TSV for the Ewe audio dataset.

Reads the existing TSV (default: data/manifests/asr/manifest_ewe_asr.tsv) and writes a new TSV
with normalized, reproducible paths.

Output TSV columns:
  split, audio, text, speaker_id, locale

Where `audio` is a workspace-relative path when possible (otherwise kept as-is).

Usage:
  .\.venv\Scripts\python.exe tools/manifests/build_manifest_ewe_asr_v2.py --in data/manifests/asr/manifest_ewe_asr.tsv --out data/manifests/asr/manifest_ewe_asr_v2.tsv

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import os


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _norm_split(value: str) -> str:
    v = (value or "").strip().lower()
    if v in {"train", "dev", "test"}:
        return v
    if v in {"valid", "val", "validation"}:
        return "dev"
    return v


def _to_rel_if_possible(path: str, repo_root: str) -> str:
    p = (path or "").strip().strip('"')
    if not p:
        return ""

    if not os.path.isabs(p):
        return p.replace("\\", "/")

    abs_p = os.path.abspath(p)
    try:
        rel = os.path.relpath(abs_p, repo_root)
    except ValueError:
        return p

    if rel.startswith(".."):
        return p

    return rel.replace("\\", "/")


def rebuild(in_path: str, out_path: str, write_missing: str = "") -> int:
    repo_root = _repo_root()

    rows_out: list[list[str]] = []
    missing_rows: list[list[str]] = []

    total = 0
    missing = 0

    with open(in_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            total += 1
            split = _norm_split(r.get("split", ""))
            audio_raw = r.get("audio_path", r.get("audio", ""))
            audio = _to_rel_if_possible(audio_raw, repo_root)
            text = (r.get("text", "") or "").replace("\r", " ").replace("\n", " ").strip()
            speaker_id = (r.get("speaker_id", "") or "").strip()
            locale = (r.get("locale", "") or "").strip()

            exists = True
            if audio and not os.path.isabs(audio):
                exists = os.path.exists(os.path.join(repo_root, audio.replace("/", os.sep)))

            if not exists:
                missing += 1
                missing_rows.append([split, audio, text, speaker_id, locale])

            rows_out.append([split, audio, text, speaker_id, locale])

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["split", "audio", "text", "speaker_id", "locale"])
        w.writerows(rows_out)

    if write_missing:
        os.makedirs(os.path.dirname(write_missing) or ".", exist_ok=True)
        with open(write_missing, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["split", "audio", "text", "speaker_id", "locale"])
            w.writerows(missing_rows)

    print("in:", in_path)
    print("out:", out_path)
    print("rows:", total)
    print("missing_audio_inside_repo:", missing)
    if write_missing:
        print("missing_list:", write_missing)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default=os.path.join("data", "manifests", "asr", "manifest_ewe_asr.tsv"))
    ap.add_argument("--out", dest="out_path", default=os.path.join("data", "manifests", "asr", "manifest_ewe_asr_v2.tsv"))
    ap.add_argument(
        "--write-missing",
        default="",
        help="Optional TSV path to write rows whose audio path is missing (only checked for repo-relative paths)",
    )
    args = ap.parse_args()

    return rebuild(args.in_path, args.out_path, write_missing=args.write_missing)


if __name__ == "__main__":
    raise SystemExit(main())
