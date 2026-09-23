"""Quick check: matching between `.txt` and `.flac` files in `data/ewe2`.

Usage:
  .\.venv\Scripts\python.exe tools/checks/check_ewe2_flac_txt_match.py
"""

from __future__ import annotations

import os
from collections import Counter


def main() -> int:
    root = os.path.join("data", "ewe2")

    flac_bases: set[str] = set()
    flac_files = 0
    flac_split: Counter[str] = Counter()

    txt_bases: set[str] = set()
    txt_files = 0
    txt_split: Counter[str] = Counter()

    for dirpath, _, files in os.walk(root):
        for fn in files:
            lower = fn.lower()
            if lower.endswith(".flac"):
                flac_files += 1
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                split = rel.split(os.sep, 1)[0]
                flac_split[split] += 1
                flac_bases.add(os.path.splitext(fn)[0])
            elif lower.endswith(".txt"):
                txt_files += 1
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                split = rel.split(os.sep, 1)[0]
                txt_split[split] += 1
                txt_bases.add(os.path.splitext(fn)[0])

    both = txt_bases & flac_bases
    only_txt = txt_bases - flac_bases
    only_flac = flac_bases - txt_bases

    print("root:", root)
    print("flac_files:", flac_files)
    print("txt_files:", txt_files)
    print("splits_flac:", dict(flac_split))
    print("splits_txt:", dict(txt_split))
    print("matched_pairs:", len(both))
    print("txt_without_flac:", len(only_txt))
    print("flac_without_txt:", len(only_flac))
    print("txt_without_flac_examples:", sorted(list(only_txt))[:10])
    print("flac_without_txt_examples:", sorted(list(only_flac))[:10])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
