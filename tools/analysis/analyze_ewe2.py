"""Analyze the `data/ewe2` text corpus.

Corpus layout (observed):
    data/ewe2/{train,dev,test}/<BOOK>/<BOOK>_<CHAPTER>_Verse_<VERSE>.txt

This script computes:
- counts by split and by book
- file size stats
- text length stats (chars, lines)
- empty files and whitespace-only files
- filename pattern validation and missing indices per (book, chapter)
- a small sample of non-ASCII characters used

Usage:
  .\.venv\Scripts\python.exe tools/analysis/analyze_ewe2.py --root data/ewe2 --out-json docs/stats/ewe2_stats.json

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable


FILENAME_RE = re.compile(r"^(?P<book>[A-Z0-9]{3})_(?P<chapter>\d{3})_Verse_(?P<verse>\d{3})\.txt$")


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass(frozen=True)
class SplitStats:
    files: int
    bytes: int
    by_book: dict[str, int]


@dataclass(frozen=True)
class TextStats:
    files: int
    chars: dict[str, float]
    lines: dict[str, float]


@dataclass(frozen=True)
class Ewe2Report:
    root: str
    total_files: int
    split_stats: dict[str, SplitStats]
    filename_pattern_bad: int
    empty_files: int
    whitespace_only_files: int
    text_stats: TextStats
    non_ascii_top: list[tuple[str, int]]
    missing_verses_examples: list[dict[str, object]]


def _percentiles(sorted_values: list[int], ps: Iterable[float]) -> dict[str, float]:
    if not sorted_values:
        return {}

    def pick(p: float) -> float:
        n = len(sorted_values)
        k = max(1, int(round(p * n)))
        return float(sorted_values[min(n - 1, k - 1)])

    out: dict[str, float] = {}
    for p in ps:
        out[f"p{int(p*100)}"] = pick(p)
    return out


def _stats(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    s = sorted(values)
    return {
        "mean": float(statistics.mean(values)),
        "median": float(statistics.median(values)),
        "min": float(s[0]),
        "max": float(s[-1]),
        **_percentiles(s, [0.9, 0.95, 0.99]),
    }


def iter_txt_files(root: str) -> Iterable[tuple[str, str, str]]:
    """Yield (split, book, file_path) for every .txt file under root."""
    for split in ("train", "dev", "test"):
        split_dir = os.path.join(root, split)
        if not os.path.isdir(split_dir):
            continue
        for book in os.listdir(split_dir):
            book_dir = os.path.join(split_dir, book)
            if not os.path.isdir(book_dir):
                continue
            for name in os.listdir(book_dir):
                if not name.lower().endswith(".txt"):
                    continue
                yield split, book, os.path.join(book_dir, name)


def analyze(root: str, non_ascii_sample_limit: int = 200_000) -> Ewe2Report:
    split_bytes: Counter[str] = Counter()
    split_files: Counter[str] = Counter()
    by_book: dict[str, Counter[str]] = defaultdict(Counter)

    filename_bad = 0
    empty_files = 0
    whitespace_only_files = 0

    char_lengths: list[int] = []
    line_counts: list[int] = []

    non_ascii: Counter[str] = Counter()
    seen_chars_budget = 0

    # For missing verse detection per (book, chapter)
    verses_seen: dict[tuple[str, str, str], set[int]] = defaultdict(set)  # (split, book, chapter)->set(verse)
    verses_max: dict[tuple[str, str, str], int] = defaultdict(int)

    for split, book_dir_name, path in iter_txt_files(root):
        split_files[split] += 1
        by_book[split][book_dir_name] += 1

        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        split_bytes[split] += size
        if size == 0:
            empty_files += 1

        name = os.path.basename(path)
        m = FILENAME_RE.match(name)
        if not m:
            filename_bad += 1
        else:
            book = m.group("book")
            chapter = m.group("chapter")
            verse = int(m.group("verse"))
            key = (split, book, chapter)
            verses_seen[key].add(verse)
            verses_max[key] = max(verses_max[key], verse)

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                text = f.read()

        if text.strip() == "":
            whitespace_only_files += 1

        char_lengths.append(len(text))
        line_counts.append(0 if text == "" else text.count("\n") + 1)

        if seen_chars_budget < non_ascii_sample_limit:
            for ch in text:
                if ord(ch) > 127:
                    non_ascii[ch] += 1
            seen_chars_budget += len(text)

    split_stats: dict[str, SplitStats] = {}
    for split in sorted(set(split_files.keys()) | set(split_bytes.keys())):
        split_stats[split] = SplitStats(
            files=int(split_files[split]),
            bytes=int(split_bytes[split]),
            by_book=dict(by_book[split]),
        )

    text_stats = TextStats(
        files=len(char_lengths),
        chars=_stats(char_lengths),
        lines=_stats(line_counts),
    )

    # Missing verses examples (detect holes)
    missing_examples: list[dict[str, object]] = []
    for (split, book, chapter), seen in sorted(verses_seen.items()):
        max_verse = verses_max[(split, book, chapter)]
        if max_verse <= 0:
            continue
        missing = [v for v in range(0, max_verse + 1) if v not in seen]
        if missing:
            missing_examples.append(
                {
                    "split": split,
                    "book": book,
                    "chapter": chapter,
                    "max_verse": max_verse,
                    "missing_count": len(missing),
                    "missing_first": missing[:20],
                }
            )
        if len(missing_examples) >= 30:
            break

    return Ewe2Report(
        root=root,
        total_files=int(sum(split_files.values())),
        split_stats=split_stats,
        filename_pattern_bad=int(filename_bad),
        empty_files=int(empty_files),
        whitespace_only_files=int(whitespace_only_files),
        text_stats=text_stats,
        non_ascii_top=non_ascii.most_common(50),
        missing_verses_examples=missing_examples,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=os.path.join("data", "ewe2"),
        help="Root folder containing train/dev/test (default: data/ewe2)",
    )
    ap.add_argument(
        "--out-json",
        default=os.path.join("docs", "stats", "ewe2_stats.json"),
        help="Path to write JSON report (default: docs/stats/ewe2_stats.json)",
    )
    ap.add_argument(
        "--non-ascii-budget",
        type=int,
        default=200_000,
        help="Max chars to scan for non-ASCII stats (default: 200000)",
    )
    args = ap.parse_args()

    report = analyze(args.root, non_ascii_sample_limit=args.non_ascii_budget)

    print("ewe2 root:", report.root)
    print("total_files:", report.total_files)
    for split, st in report.split_stats.items():
        print(f"split {split}: files={st.files} bytes={st.bytes}")
        top_books = sorted(st.by_book.items(), key=lambda x: x[1], reverse=True)[:10]
        print("  top_books:", top_books)

    print("filename_pattern_bad:", report.filename_pattern_bad)
    print("empty_files:", report.empty_files)
    print("whitespace_only_files:", report.whitespace_only_files)
    print("text chars:", {k: round(v, 2) for k, v in report.text_stats.chars.items()})
    print("text lines:", {k: round(v, 2) for k, v in report.text_stats.lines.items()})
    print("non_ascii_top (sampled):", report.non_ascii_top[:20])

    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)
    print("wrote:", args.out_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
