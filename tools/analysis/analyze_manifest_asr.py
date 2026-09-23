"""Analyze an ASR manifest TSV.

Designed for the dataset format in `data/manifests/asr/manifest_ewe_asr.tsv`:
    split\taudio_path\ttext\tspeaker_id\tlocale

Usage:
  .\.venv\Scripts\python.exe tools/analysis/analyze_manifest_asr.py --manifest data/manifests/asr/manifest_ewe_asr.tsv --check-audio 200 --out-json docs/stats/manifest_asr_stats.json

Outputs:
- Printed summary to stdout
- Optional JSON report via --out-json

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass(frozen=True)
class ManifestStats:
    rows: int
    columns: list[str]
    split_counts: dict[str, int]
    locale_counts: dict[str, int]
    unique_speakers: int
    top_speakers: list[tuple[str, int]]
    text_len_chars: dict[str, float]
    audio_exists_check: dict[str, int] | None


def _percentiles(sorted_values: list[int], ps: Iterable[float]) -> dict[str, float]:
    if not sorted_values:
        return {}

    def pick(p: float) -> float:
        # Nearest-rank percentile (1-indexed), stable for small samples
        n = len(sorted_values)
        k = max(1, int(round(p * n)))
        return float(sorted_values[min(n - 1, k - 1)])

    out: dict[str, float] = {}
    for p in ps:
        out[f"p{int(p*100)}"] = pick(p)
    return out


def analyze_manifest(manifest_path: str, check_audio: int = 0) -> ManifestStats:
    repo_root = _repo_root()

    rows: list[dict[str, str]] = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)

    if not rows:
        return ManifestStats(
            rows=0,
            columns=[],
            split_counts={},
            locale_counts={},
            unique_speakers=0,
            top_speakers=[],
            text_len_chars={},
            audio_exists_check=None,
        )

    columns = list(rows[0].keys())
    split_counts = dict(Counter(r.get("split", "") for r in rows))
    locale_counts = dict(Counter(r.get("locale", "") for r in rows))

    speakers = Counter(r.get("speaker_id", "") for r in rows)

    texts = [r.get("text", "") or "" for r in rows]
    lens = [len(t) for t in texts]
    lens_sorted = sorted(lens)

    text_len_chars: dict[str, float] = {
        "mean": float(statistics.mean(lens)) if lens else 0.0,
        "median": float(statistics.median(lens)) if lens else 0.0,
        "min": float(lens_sorted[0]) if lens_sorted else 0.0,
        "max": float(lens_sorted[-1]) if lens_sorted else 0.0,
        **_percentiles(lens_sorted, [0.9, 0.95, 0.99]),
    }

    audio_exists_check: dict[str, int] | None = None
    if check_audio and check_audio > 0:
        checked = 0
        missing = 0
        for r in rows:
            p = (r.get("audio_path") or r.get("audio") or "").strip()
            if not p:
                continue
            checked += 1

            # Support both absolute and repo-relative paths
            p_check = p
            if not os.path.isabs(p_check):
                p_check = os.path.join(repo_root, p_check.replace("/", os.sep))

            if not os.path.exists(p_check):
                missing += 1
            if checked >= check_audio:
                break
        audio_exists_check = {"checked": checked, "missing": missing}

    return ManifestStats(
        rows=len(rows),
        columns=columns,
        split_counts=split_counts,
        locale_counts=locale_counts,
        unique_speakers=len(speakers),
        top_speakers=speakers.most_common(20),
        text_len_chars=text_len_chars,
        audio_exists_check=audio_exists_check,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        default=os.path.join("data", "manifests", "asr", "manifest_ewe_asr.tsv"),
        help="Path to manifest TSV (default: data/manifests/asr/manifest_ewe_asr.tsv)",
    )
    ap.add_argument(
        "--check-audio",
        type=int,
        default=0,
        help="Check existence of first N audio paths (default: 0 = skip)",
    )
    ap.add_argument(
        "--out-json",
        default="",
        help="Optional path to write JSON report",
    )

    args = ap.parse_args()

    stats = analyze_manifest(args.manifest, check_audio=args.check_audio)

    print("ASR manifest:", args.manifest)
    print("rows:", stats.rows)
    print("columns:", ", ".join(stats.columns))
    print("split_counts:", stats.split_counts)
    print("locale_counts:", stats.locale_counts)
    print("unique_speakers:", stats.unique_speakers)
    print("top_speakers:")
    for spk, n in stats.top_speakers:
        if spk == "":
            spk = "<empty>"
        print(f"  {spk}: {n}")
    print("text_len_chars:", {k: round(v, 2) for k, v in stats.text_len_chars.items()})
    if stats.audio_exists_check is not None:
        print("audio_exists_check:", stats.audio_exists_check)

    if args.out_json:
        os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(asdict(stats), f, ensure_ascii=False, indent=2)
        print("wrote:", args.out_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
