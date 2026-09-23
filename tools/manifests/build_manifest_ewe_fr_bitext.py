"""Build a clean Ewe↔French bitext manifest from a Hugging Face dataset.

Goal
- Fetch Ewe-French sentence pairs (bitext) from Hugging Face.
- Normalize columns, de-duplicate, filter empties.
- Produce a reproducible train/dev/test split.

Outputs (defaults)
- data/manifests/mt/manifest_ewe_fr_bitext.tsv
  Columns: split, source, ee, fr
- docs/stats/ewe_fr_bitext_stats.json

Usage:
  .\.venv\Scripts\python.exe tools/manifests/build_manifest_ewe_fr_bitext.py --dataset michsethowusu/ewe-french_sentence-pairs

Notes
- This script does NOT scrape Glosbe. Glosbe can be used for manual validation/curation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable


def _norm_text(s: Any) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\u00a0", " ")
    s = " ".join(s.strip().split())
    return s


def _hash_split(key: str, train_pct: int, dev_pct: int, test_pct: int) -> str:
    total = train_pct + dev_pct + test_pct
    if total <= 0:
        raise ValueError("split percentages must sum to > 0")
    digest = hashlib.sha1(key.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % total
    if bucket < train_pct:
        return "train"
    if bucket < train_pct + dev_pct:
        return "dev"
    return "test"


def _infer_pair_fields(example: dict[str, Any]) -> tuple[str, str] | None:
    lower_to_actual: dict[str, str] = {k.lower(): k for k in example.keys()}
    direct_candidates = [
        ("ee", "fr"),
        ("ewe", "french"),
        ("ewe", "fr"),
        ("ee", "french"),
        ("source", "target"),
    ]
    for a, b in direct_candidates:
        if a in lower_to_actual and b in lower_to_actual:
            return lower_to_actual[a], lower_to_actual[b]

    for k in ("translation", "translations"):
        v = example.get(k)
        if isinstance(v, dict):
            if "ee" in v and "fr" in v:
                return f"{k}.ee", f"{k}.fr"
            if "ewe" in v and "french" in v:
                return f"{k}.ewe", f"{k}.french"

    return None


def _get_nested(example: dict[str, Any], path: str) -> Any:
    cur: Any = example
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


@dataclass
class BitextStats:
    dataset: str
    rows_total: int
    rows_written: int
    split_counts: dict[str, int]
    empty_dropped: int
    duplicates_dropped: int
    ee_char_mean: float
    fr_char_mean: float


def build_manifest(
    dataset_name: str,
    out_tsv: str,
    out_json: str,
    train_pct: int,
    dev_pct: int,
    test_pct: int,
    max_rows: int | None,
) -> BitextStats:
    from datasets import load_dataset  # type: ignore

    ds = load_dataset(dataset_name)

    split_order = [s for s in ("train", "validation", "dev", "test") if s in ds]
    if not split_order:
        split_order = list(ds.keys())

    first_split = split_order[0]
    if len(ds[first_split]) == 0:
        raise RuntimeError(f"Dataset split '{first_split}' is empty")

    first_ex = ds[first_split][0]
    if not isinstance(first_ex, dict):
        raise RuntimeError("Unexpected dataset example type; expected dict")

    inferred = _infer_pair_fields(first_ex)
    if inferred is None:
        raise RuntimeError(
            "Could not infer Ewe/French fields from dataset schema. "
            f"First example keys: {sorted(list(first_ex.keys()))}"
        )
    ee_field, fr_field = inferred

    def iter_examples() -> Iterable[dict[str, Any]]:
        seen = 0
        for split_name in split_order:
            for ex in ds[split_name]:
                if not isinstance(ex, dict):
                    continue
                yield ex
                seen += 1
                if max_rows is not None and seen >= max_rows:
                    return

    rows_total = 0
    rows_written = 0
    empty_dropped = 0
    duplicates_dropped = 0
    split_counts: Counter[str] = Counter()
    seen_pairs: set[str] = set()

    ee_lens: list[int] = []
    fr_lens: list[int] = []

    os.makedirs(os.path.dirname(out_tsv) or ".", exist_ok=True)

    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["split", "source", "ee", "fr"],
            delimiter="\t",
        )
        w.writeheader()

        for ex in iter_examples():
            rows_total += 1
            ee = _norm_text(_get_nested(ex, ee_field) if "." in ee_field else ex.get(ee_field))
            fr = _norm_text(_get_nested(ex, fr_field) if "." in fr_field else ex.get(fr_field))

            if not ee or not fr:
                empty_dropped += 1
                continue

            pair_key = f"{ee}\u241f{fr}"
            if pair_key in seen_pairs:
                duplicates_dropped += 1
                continue
            seen_pairs.add(pair_key)

            split = _hash_split(pair_key, train_pct, dev_pct, test_pct)
            split_counts[split] += 1

            w.writerow({"split": split, "source": dataset_name, "ee": ee, "fr": fr})
            rows_written += 1
            ee_lens.append(len(ee))
            fr_lens.append(len(fr))

    ee_mean = (sum(ee_lens) / len(ee_lens)) if ee_lens else 0.0
    fr_mean = (sum(fr_lens) / len(fr_lens)) if fr_lens else 0.0

    stats = BitextStats(
        dataset=dataset_name,
        rows_total=rows_total,
        rows_written=rows_written,
        split_counts=dict(split_counts),
        empty_dropped=empty_dropped,
        duplicates_dropped=duplicates_dropped,
        ee_char_mean=round(ee_mean, 2),
        fr_char_mean=round(fr_mean, 2),
    )

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(asdict(stats), f, ensure_ascii=False, indent=2)

    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="michsethowusu/ewe-french_sentence-pairs")
    ap.add_argument("--out-tsv", default="data/manifests/mt/manifest_ewe_fr_bitext.tsv")
    ap.add_argument("--out-json", default="docs/stats/ewe_fr_bitext_stats.json")
    ap.add_argument("--train-pct", type=int, default=90)
    ap.add_argument("--dev-pct", type=int, default=5)
    ap.add_argument("--test-pct", type=int, default=5)
    ap.add_argument("--max-rows", type=int, default=0, help="0 means no limit")
    args = ap.parse_args()

    max_rows = None if args.max_rows == 0 else args.max_rows

    stats = build_manifest(
        dataset_name=args.dataset,
        out_tsv=args.out_tsv,
        out_json=args.out_json,
        train_pct=args.train_pct,
        dev_pct=args.dev_pct,
        test_pct=args.test_pct,
        max_rows=max_rows,
    )

    print(f"dataset: {stats.dataset}")
    print(f"rows_total: {stats.rows_total}")
    print(f"rows_written: {stats.rows_written}")
    print(f"split_counts: {stats.split_counts}")
    print(f"empty_dropped: {stats.empty_dropped}")
    print(f"duplicates_dropped: {stats.duplicates_dropped}")
    print(f"mean_chars: ee={stats.ee_char_mean} fr={stats.fr_char_mean}")
    print(f"wrote: {args.out_tsv}")
    print(f"wrote: {args.out_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
