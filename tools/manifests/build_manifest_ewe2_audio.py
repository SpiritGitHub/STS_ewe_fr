"""Build an audio+text manifest from the ewe2 OpenBible corpus.

Observation:
- For each verse, ewe2 contains BOTH:
  - a text file: BOOK_###_Verse_###.txt
  - an audio file: BOOK_###_Verse_###.flac

This script creates a clean ASR-ready manifest.

Output TSV columns:
  split, book, chapter, verse, audio, text, relpath_txt, relpath_audio, source

Outputs (defaults):
- data/manifests/asr/manifest_ewe2_audio.tsv
- docs/stats/ewe2_audio_stats.json

Usage:
  .\.venv\Scripts\python.exe tools/manifests/build_manifest_ewe2_audio.py --root data/ewe2
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass


FILENAME_RE = re.compile(r"^(?P<book>[A-Z0-9]{3})_(?P<chapter>\d{3})_Verse_(?P<verse>\d{3})\.(?P<ext>txt|flac)$")


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        # Preserve content but normalize trailing whitespace.
        return "\n".join([line.rstrip() for line in f.read().splitlines()]).strip()


@dataclass
class Ewe2AudioStats:
    root: str
    rows_written: int
    split_counts: dict[str, int]
    empty_text_rows: int
    missing_audio_rows: int
    missing_text_rows: int
    filename_pattern_bad: int
    books_top: list[tuple[str, int]]


def build_manifest(root: str, out_tsv: str, out_json: str) -> Ewe2AudioStats:
    root = os.path.abspath(root)
    repo_root = _repo_root()

    # Map basename -> paths
    txt_by_base: dict[str, str] = {}
    flac_by_base: dict[str, str] = {}
    bad = 0

    for dirpath, _, files in os.walk(root):
        for fn in files:
            m = FILENAME_RE.match(fn)
            if not m:
                # Ignore unrelated files, but count if they look like verse assets
                if fn.lower().endswith((".txt", ".flac")):
                    bad += 1
                continue
            base = os.path.splitext(fn)[0]
            ext = m.group("ext")
            full = os.path.join(dirpath, fn)
            if ext == "txt":
                txt_by_base[base] = full
            else:
                flac_by_base[base] = full

    bases = sorted(set(txt_by_base.keys()) | set(flac_by_base.keys()))

    os.makedirs(os.path.dirname(out_tsv) or ".", exist_ok=True)

    split_counts: Counter[str] = Counter()
    books: Counter[str] = Counter()
    rows_written = 0
    empty_text_rows = 0
    missing_audio_rows = 0
    missing_text_rows = 0

    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "split",
                "book",
                "chapter",
                "verse",
                "audio",
                "text",
                "relpath_txt",
                "relpath_audio",
                "source",
            ],
            delimiter="\t",
        )
        w.writeheader()

        for base in bases:
            txt_path = txt_by_base.get(base)
            flac_path = flac_by_base.get(base)

            # Split inferred from directory structure: root/split/BOOK/...
            any_path = txt_path or flac_path
            assert any_path is not None
            rel_from_root = os.path.relpath(any_path, root)
            split = rel_from_root.split(os.sep, 1)[0]

            m = FILENAME_RE.match(os.path.basename(any_path))
            if not m:
                continue
            book = m.group("book")
            chapter = int(m.group("chapter"))
            verse = int(m.group("verse"))

            text = ""
            if txt_path is None:
                missing_text_rows += 1
            else:
                text = _read_text(txt_path)
                if not text:
                    empty_text_rows += 1

            if flac_path is None:
                missing_audio_rows += 1

            # Write only rows that have both audio and text (ASR-ready)
            if not txt_path or not flac_path or not text:
                continue

            rel_txt_repo = os.path.relpath(txt_path, repo_root).replace(os.sep, "/")
            rel_audio_repo = os.path.relpath(flac_path, repo_root).replace(os.sep, "/")

            w.writerow(
                {
                    "split": split,
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "audio": rel_audio_repo,
                    "text": text,
                    "relpath_txt": rel_txt_repo,
                    "relpath_audio": rel_audio_repo,
                    "source": "ewe2_openbible",
                }
            )
            rows_written += 1
            split_counts[split] += 1
            books[book] += 1

    stats = Ewe2AudioStats(
        root=os.path.relpath(root, repo_root).replace(os.sep, "/"),
        rows_written=rows_written,
        split_counts=dict(split_counts),
        empty_text_rows=empty_text_rows,
        missing_audio_rows=missing_audio_rows,
        missing_text_rows=missing_text_rows,
        filename_pattern_bad=bad,
        books_top=books.most_common(10),
    )

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(asdict(stats), f, ensure_ascii=False, indent=2)

    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/ewe2")
    ap.add_argument("--out-tsv", default="data/manifests/asr/manifest_ewe2_audio.tsv")
    ap.add_argument("--out-json", default="docs/stats/ewe2_audio_stats.json")
    args = ap.parse_args()

    stats = build_manifest(args.root, args.out_tsv, args.out_json)
    print("ewe2 audio root:", args.root)
    print("rows_written:", stats.rows_written)
    print("split_counts:", stats.split_counts)
    print("empty_text_rows:", stats.empty_text_rows)
    print("missing_audio_rows:", stats.missing_audio_rows)
    print("missing_text_rows:", stats.missing_text_rows)
    print("filename_pattern_bad:", stats.filename_pattern_bad)
    print("top_books:", stats.books_top)
    print("wrote:", args.out_tsv)
    print("wrote:", args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
