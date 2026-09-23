r"""Merge multiple ASR manifests into a single "global" manifest + comparative stats.

Inputs (expected in this repo)
- data/manifests/asr/manifest_ewe_asr.tsv
  Columns: split, audio, text, speaker_id, locale
- data/manifests/asr/manifest_ewe2_audio.tsv
  Columns: split, book, chapter, verse, audio, text, relpath_txt, relpath_audio, source

Output (defaults)
- data/manifests/asr/manifest_asr_global.tsv
  Columns (normalized): split, source, audio, text, speaker_id, locale, book, chapter, verse
- docs/stats/asr_global_stats.json
  Comparative stats grouped by source and split.

Usage:
  .\.venv\Scripts\python.exe tools/manifests/build_manifest_asr_global.py --check-audio 200

Notes
- Audio paths are written as repo-relative POSIX paths (with '/').
- For ewe2 rows, speaker_id/locale may be empty (unless you later add them).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _norm_text(s: Any) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\u00a0", " ")
    return " ".join(s.strip().split())


def _to_posix_relpath(repo_root: str, path: str) -> str:
    path = (path or "").strip()
    if not path:
        return ""
    path = path.replace("\\", "/")
    if not os.path.isabs(path) and not (len(path) > 1 and path[1] == ":"):
        return path
    try:
        rel = os.path.relpath(path, repo_root)
    except ValueError:
        return path.replace("\\", "/")
    return rel.replace("\\", "/")


def _read_tsv(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        return [dict(row) for row in r]


def _safe_int(s: str) -> int | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


@dataclass
class GroupStats:
    rows: int
    unique_speakers: int
    text_len_mean: float
    text_len_median: float
    text_len_max: int
    audio_ext_counts: dict[str, int]


@dataclass
class GlobalStats:
    out_tsv: str
    total_rows: int
    by_source: dict[str, dict[str, GroupStats]]
    audio_exists_check: dict[str, int] | None


def _compute_group_stats(rows: list[dict[str, str]]) -> GroupStats:
    speakers = {r.get("speaker_id", "").strip() for r in rows if (r.get("speaker_id") or "").strip()}
    lens = [len((r.get("text") or "")) for r in rows]
    if lens:
        mean_v = float(sum(lens) / len(lens))
        med_v = float(statistics.median(lens))
        max_v = int(max(lens))
    else:
        mean_v = 0.0
        med_v = 0.0
        max_v = 0

    ext_counts: Counter[str] = Counter()
    for r in rows:
        audio = (r.get("audio") or "").strip()
        ext = os.path.splitext(audio)[1].lower() if audio else ""
        if ext:
            ext_counts[ext] += 1

    return GroupStats(
        rows=len(rows),
        unique_speakers=len(speakers),
        text_len_mean=round(mean_v, 2),
        text_len_median=round(med_v, 2),
        text_len_max=max_v,
        audio_ext_counts=dict(ext_counts),
    )


def build_global(
    asr_manifest: str,
    ewe2_manifest: str,
    out_tsv: str,
    out_json: str,
    check_audio: int = 0,
) -> GlobalStats:
    repo_root = _repo_root()

    asr_rows = _read_tsv(asr_manifest)
    ewe2_rows = _read_tsv(ewe2_manifest)

    merged: list[dict[str, str]] = []

    for r in asr_rows:
        merged.append(
            {
                "split": (r.get("split") or "").strip(),
                "source": "ewe_asr",
                "audio": _to_posix_relpath(repo_root, (r.get("audio") or r.get("audio_path") or "")),
                "text": _norm_text(r.get("text")),
                "speaker_id": (r.get("speaker_id") or "").strip(),
                "locale": (r.get("locale") or "").strip(),
                "book": "",
                "chapter": "",
                "verse": "",
            }
        )

    for r in ewe2_rows:
        merged.append(
            {
                "split": (r.get("split") or "").strip(),
                "source": (r.get("source") or "ewe2_openbible").strip(),
                "audio": _to_posix_relpath(repo_root, (r.get("audio") or r.get("relpath_audio") or "")),
                "text": _norm_text(r.get("text")),
                "speaker_id": (r.get("speaker_id") or "").strip(),
                "locale": (r.get("locale") or "").strip(),
                "book": (r.get("book") or "").strip(),
                "chapter": str(_safe_int(r.get("chapter") or "") or "").strip(),
                "verse": str(_safe_int(r.get("verse") or "") or "").strip(),
            }
        )

    os.makedirs(os.path.dirname(out_tsv) or ".", exist_ok=True)
    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["split", "source", "audio", "text", "speaker_id", "locale", "book", "chapter", "verse"],
            delimiter="\t",
        )
        w.writeheader()
        for r in merged:
            w.writerow(r)

    by_source: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for r in merged:
        by_source[r["source"]][r["split"]].append(r)

    stats_by_source: dict[str, dict[str, GroupStats]] = {}
    for source, splits in by_source.items():
        stats_by_source[source] = {split: _compute_group_stats(rows) for split, rows in splits.items()}

    audio_exists_check: dict[str, int] | None = None
    if check_audio and check_audio > 0:
        checked = 0
        missing = 0
        for r in merged:
            p = (r.get("audio") or "").strip()
            if not p:
                continue
            checked += 1
            p_check = p
            if not os.path.isabs(p_check):
                p_check = os.path.join(repo_root, p_check.replace("/", os.sep))
            if not os.path.exists(p_check):
                missing += 1
            if checked >= check_audio:
                break
        audio_exists_check = {"checked": checked, "missing": missing}

    out = GlobalStats(
        out_tsv=out_tsv.replace("\\", "/"),
        total_rows=len(merged),
        by_source=stats_by_source,
        audio_exists_check=audio_exists_check,
    )

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(asdict(out), f, ensure_ascii=False, indent=2)

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asr-manifest", default="data/manifests/asr/manifest_ewe_asr.tsv")
    ap.add_argument("--ewe2-manifest", default="data/manifests/asr/manifest_ewe2_audio.tsv")
    ap.add_argument("--out-tsv", default="data/manifests/asr/manifest_asr_global.tsv")
    ap.add_argument("--out-json", default="docs/stats/asr_global_stats.json")
    ap.add_argument("--check-audio", type=int, default=0)
    args = ap.parse_args()

    stats = build_global(args.asr_manifest, args.ewe2_manifest, args.out_tsv, args.out_json, check_audio=args.check_audio)

    print("wrote:", args.out_tsv)
    print("wrote:", args.out_json)
    print("total_rows:", stats.total_rows)
    if stats.audio_exists_check:
        print("audio_exists_check:", stats.audio_exists_check)

    for source, splits in stats.by_source.items():
        print(f"source: {source}")
        for split, s in splits.items():
            print(
                f"  {split}: rows={s.rows} speakers={s.unique_speakers} "
                f"text_mean={s.text_len_mean} text_med={s.text_len_median} text_max={s.text_len_max} ext={s.audio_ext_counts}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
