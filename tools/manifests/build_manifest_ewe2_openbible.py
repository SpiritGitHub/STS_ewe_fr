"""Build a TSV manifest for the OpenBible ewe2 text corpus.

Expected layout:
  data/ewe2/{train,dev,test}/<BOOK>/<BOOK>_<CHAPTER>_Verse_<VERSE>.txt

Each file appears to contain the verse text on the first non-empty line.

Output TSV columns:
  split, book, chapter, verse, text, relpath, source

Usage:
  .\.venv\Scripts\python.exe tools/manifests/build_manifest_ewe2_openbible.py --root data/ewe2 --out data/manifests/text/manifest_ewe2_openbible.tsv

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from dataclasses import dataclass
from typing import Iterable


FILENAME_RE = re.compile(r"^(?P<book>[A-Z0-9]{3})_(?P<chapter>\d{3})_Verse_(?P<verse>\d{3})\.txt$")


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass(frozen=True)
class Row:
    split: str
    book: str
    chapter: int
    verse: int
    text: str
    relpath: str
    source: str


def _iter_files(root: str) -> Iterable[tuple[str, str, str]]:
    for split in ("train", "dev", "test"):
        split_dir = os.path.join(root, split)
        if not os.path.isdir(split_dir):
            continue
        for book in os.listdir(split_dir):
            book_dir = os.path.join(split_dir, book)
            if not os.path.isdir(book_dir):
                continue
            for name in os.listdir(book_dir):
                if name.lower().endswith(".txt"):
                    yield split, book, os.path.join(book_dir, name)


def _read_verse_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()

    lines = [ln.strip() for ln in content.splitlines()]
    non_empty = [ln for ln in lines if ln]
    return " ".join(non_empty).strip()


def build_manifest(root: str, out_path: str, source: str = "openbible") -> int:
    repo_root = _repo_root()

    rows: list[Row] = []
    bad_name = 0
    empty_text = 0

    for split, _, path in _iter_files(root):
        name = os.path.basename(path)
        m = FILENAME_RE.match(name)
        if not m:
            bad_name += 1
            continue

        book = m.group("book")
        chapter = int(m.group("chapter"))
        verse = int(m.group("verse"))

        text = _read_verse_text(path)
        if not text:
            empty_text += 1

        relpath = os.path.relpath(os.path.abspath(path), repo_root).replace("\\", "/")

        rows.append(
            Row(
                split=split,
                book=book,
                chapter=chapter,
                verse=verse,
                text=text,
                relpath=relpath,
                source=source,
            )
        )

    rows.sort(key=lambda r: (r.split, r.book, r.chapter, r.verse))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["split", "book", "chapter", "verse", "text", "relpath", "source"])
        for r in rows:
            w.writerow([r.split, r.book, f"{r.chapter:03d}", f"{r.verse:03d}", r.text, r.relpath, r.source])

    print("root:", root)
    print("wrote:", out_path)
    print("rows:", len(rows))
    print("bad_filename_pattern_skipped:", bad_name)
    print("empty_text_rows:", empty_text)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join("data", "ewe2"), help="Root folder (default: data/ewe2)")
    ap.add_argument(
        "--out",
        default=os.path.join("data", "manifests", "text", "manifest_ewe2_openbible.tsv"),
        help="Output TSV path (default: data/manifests/text/manifest_ewe2_openbible.tsv)",
    )
    ap.add_argument("--source", default="openbible", help="Source tag to include (default: openbible)")
    args = ap.parse_args()

    return build_manifest(args.root, args.out, source=args.source)


if __name__ == "__main__":
    raise SystemExit(main())
