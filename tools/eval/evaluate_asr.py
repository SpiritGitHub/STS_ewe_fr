r"""Evaluate ASR (Whisper) on dev/test and export WER/CER + per-example CSV.

Inputs
- An ASR manifest TSV with at least columns: split, audio, text
  (also supports legacy: audio_path)
- A trained Whisper checkpoint directory (Hugging Face), e.g. models/asr_whisper_ewe

Outputs (defaults)
- JSON summary: docs/results/asr_metrics.json
- CSV per-example: docs/results/asr_preds_<split>.csv

Usage:
  .\.venv\Scripts\python.exe tools/eval/evaluate_asr.py --model-dir models/asr_whisper_ewe
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _iter_manifest(manifest_path: str, split: str, max_examples: int | None):
    n = 0
    with open(manifest_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if (row.get("split") or "").strip() != split:
                continue
            audio = (row.get("audio") or row.get("audio_path") or "").strip()
            text = (row.get("text") or "").strip()
            if not audio or not text:
                continue
            yield audio, text
            n += 1
            if max_examples is not None and n >= max_examples:
                break


@dataclass
class ASRMetrics:
    model_dir: str
    manifest: str
    split: str
    n: int
    wer: float
    cer: float


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifests/asr/manifest_ewe2_audio.tsv")
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-json", default="docs/results/asr_metrics.json")
    ap.add_argument("--out-csv-prefix", default="docs/results/asr_preds")
    ap.add_argument("--max-examples", type=int, default=0, help="0 = no limit")
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    max_examples = None if args.max_examples == 0 else args.max_examples

    import torch  # type: ignore
    from jiwer import cer, wer  # type: ignore
    from transformers import WhisperForConditionalGeneration, WhisperProcessor  # type: ignore

    device = "cuda" if torch.cuda.is_available() else "cpu"

    processor = WhisperProcessor.from_pretrained(args.model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_dir).to(device)
    model.eval()

    repo_root = _repo_root()

    manifest_path = args.manifest
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(repo_root, manifest_path.replace("/", os.sep))

    out_json = args.out_json
    if not os.path.isabs(out_json):
        out_json = os.path.join(repo_root, out_json.replace("/", os.sep))

    out_csv_prefix = args.out_csv_prefix
    if not os.path.isabs(out_csv_prefix):
        out_csv_prefix = os.path.join(repo_root, out_csv_prefix.replace("/", os.sep))

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(out_csv_prefix) or ".", exist_ok=True)

    all_metrics: list[ASRMetrics] = []

    for split in ("dev", "test"):
        examples = list(_iter_manifest(manifest_path, split, max_examples))
        if not examples:
            continue

        audio_paths: list[str] = []
        refs: list[str] = []
        for audio, text in examples:
            if not os.path.isabs(audio):
                audio = os.path.join(repo_root, audio.replace("/", os.sep))
            audio_paths.append(audio)
            refs.append(text)

        preds: list[str] = []

        from datasets import Audio, Dataset  # type: ignore

        ds = Dataset.from_list([{"audio": p} for p in audio_paths]).cast_column("audio", Audio(sampling_rate=16000))

        for i in range(0, len(ds), args.batch_size):
            batch = ds[i : i + args.batch_size]["audio"]
            arrays = [b["array"] for b in batch]
            inputs = processor.feature_extractor(arrays, sampling_rate=16000, return_tensors="pt")
            input_features = inputs.input_features.to(device)

            with torch.no_grad():
                gen_ids = model.generate(input_features)
            text = processor.tokenizer.batch_decode(gen_ids, skip_special_tokens=True)
            preds.extend([s.strip() for s in text])

        w = float(wer(refs, preds))
        c = float(cer(refs, preds))

        all_metrics.append(
            ASRMetrics(
                model_dir=args.model_dir,
                manifest=args.manifest,
                split=split,
                n=len(preds),
                wer=round(w, 6),
                cer=round(c, 6),
            )
        )

        out_csv = f"{out_csv_prefix}_{split}.csv"
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            wcsv = csv.DictWriter(f, fieldnames=["split", "audio", "ref", "pred"])
            wcsv.writeheader()
            for a, r, p in zip(audio_paths, refs, preds):
                wcsv.writerow({"split": split, "audio": a, "ref": r, "pred": p})

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump([asdict(m) for m in all_metrics], f, ensure_ascii=False, indent=2)

    print("wrote:", out_json)
    print("wrote CSV prefix:", out_csv_prefix)
    for m in all_metrics:
        print(m)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
