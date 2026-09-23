r"""Evaluate MT checkpoints on dev/test and export metrics to JSON/CSV.

Inputs
- MT manifest TSV (default: data/manifests/mt/manifest_ewe_fr_bitext.tsv) with columns: split, ee, fr
- Trained model directory (Hugging Face), e.g. models/mt_ee_to_fr

Outputs (defaults)
- JSON summary: docs/results/mt_metrics_<direction>.json
- CSV per-example: docs/results/mt_preds_<direction>_<split>.csv

Usage:
  .\.venv\Scripts\python.exe tools/eval/evaluate_mt.py --direction ee_to_fr --model-dir models/mt_ee_to_fr
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from typing import Literal


Direction = Literal["ee_to_fr", "fr_to_ee"]


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _iter_manifest(manifest_path: str, split: str, max_examples: int | None):
    n = 0
    with open(manifest_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if (row.get("split") or "").strip() != split:
                continue
            ee = (row.get("ee") or "").strip()
            fr = (row.get("fr") or "").strip()
            if not ee or not fr:
                continue
            yield ee, fr
            n += 1
            if max_examples is not None and n >= max_examples:
                break


@dataclass
class MTMetrics:
    direction: str
    model_dir: str
    split: str
    n: int
    bleu: float
    chrf: float


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifests/mt/manifest_ewe_fr_bitext.tsv")
    ap.add_argument("--direction", choices=["ee_to_fr", "fr_to_ee"], required=True)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-json", default="")
    ap.add_argument("--out-csv-prefix", default="")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--max-examples", type=int, default=0, help="0 = no limit")
    args = ap.parse_args()

    max_examples = None if args.max_examples == 0 else args.max_examples

    import torch  # type: ignore
    import evaluate  # type: ignore
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore

    repo_root = _repo_root()

    manifest_path = args.manifest
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(repo_root, manifest_path.replace("/", os.sep))

    out_json = (args.out_json or "").strip()
    if not out_json:
        out_json = os.path.join("docs", "results", f"mt_metrics_{args.direction}.json")
    if not os.path.isabs(out_json):
        out_json = os.path.join(repo_root, out_json.replace("/", os.sep))

    out_csv_prefix = (args.out_csv_prefix or "").strip()
    if not out_csv_prefix:
        out_csv_prefix = os.path.join("docs", "results", f"mt_preds_{args.direction}")
    if not os.path.isabs(out_csv_prefix):
        out_csv_prefix = os.path.join(repo_root, out_csv_prefix.replace("/", os.sep))

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_csv_prefix) or ".", exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, use_fast=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_dir).to(device)
    model.eval()

    bleu_metric = evaluate.load("sacrebleu")
    chrf_metric = evaluate.load("chrf")

    all_metrics: list[MTMetrics] = []

    for split in ("dev", "test"):
        pairs = list(_iter_manifest(manifest_path, split, max_examples))
        if not pairs:
            continue

        src_texts: list[str] = []
        ref_texts: list[str] = []
        for ee, fr in pairs:
            if args.direction == "ee_to_fr":
                src_texts.append(ee)
                ref_texts.append(fr)
            else:
                src_texts.append(fr)
                ref_texts.append(ee)

        preds: list[str] = []

        for i in range(0, len(src_texts), args.batch_size):
            batch = src_texts[i : i + args.batch_size]
            enc = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=args.max_length).to(device)
            with torch.no_grad():
                out_ids = model.generate(**enc, max_length=args.max_length)
            batch_preds = tokenizer.batch_decode(out_ids, skip_special_tokens=True)
            preds.extend([p.strip() for p in batch_preds])

        bleu = bleu_metric.compute(predictions=preds, references=[[r] for r in ref_texts])["score"]
        chrf = chrf_metric.compute(predictions=preds, references=ref_texts)["score"]

        all_metrics.append(
            MTMetrics(
                direction=args.direction,
                model_dir=args.model_dir,
                split=split,
                n=len(preds),
                bleu=round(float(bleu), 4),
                chrf=round(float(chrf), 4),
            )
        )

        out_csv = f"{out_csv_prefix}_{split}.csv"
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["split", "src", "ref", "pred"])
            w.writeheader()
            for ref, pred, src in zip(ref_texts, preds, src_texts):
                w.writerow({"split": split, "src": src, "ref": ref, "pred": pred})

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump([asdict(m) for m in all_metrics], f, ensure_ascii=False, indent=2)

    print("wrote:", out_json)
    print("wrote CSV prefix:", out_csv_prefix)
    for m in all_metrics:
        print(m)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
