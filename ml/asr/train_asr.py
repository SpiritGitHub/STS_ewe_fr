"""Fine-tune a Whisper ASR model using your manifests.

Primary target (clean, aligned audio+text):
- data/manifests/asr/manifest_ewe2_audio.tsv  (flac + verse text)

Optional:
- data/manifests/asr/manifest_ewe_asr.tsv (mp3 + transcribed speech)
- data/manifests/asr/manifest_asr_global.tsv (merged)

This is the ASR training entrypoint in the ml/ layout.

Usage (PowerShell)
  F:/STS/.venv/Scripts/python.exe ml/asr/train_asr.py `
    --manifest data/manifests/asr/manifest_ewe2_audio.tsv `
    --model openai/whisper-small `
    --out-dir models/asr_whisper_ewe `
    --max-train 50000 `
    --max-eval 2000
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Any


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _iter_asr_manifest(path: str, split: str, max_rows: int | None):
    seen = 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if (row.get("split") or "").strip() != split:
                continue
            audio = (row.get("audio") or row.get("audio_path") or "").strip()
            text = (row.get("text") or "").strip()
            if not audio or not text:
                continue
            yield {"audio": audio, "text": text}
            seen += 1
            if max_rows is not None and seen >= max_rows:
                break


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifests/asr/manifest_ewe2_audio.tsv")
    ap.add_argument("--model", default="openai/whisper-small")
    ap.add_argument("--out-dir", default="models/asr_whisper_ewe")

    ap.add_argument("--language", default="ewe")
    ap.add_argument("--task", default="transcribe")

    ap.add_argument("--max-train", type=int, default=0, help="0 = no limit")
    ap.add_argument("--max-eval", type=int, default=0, help="0 = no limit")

    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--eval-batch-size", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument("--max-label-length", type=int, default=256)

    ap.add_argument(
        "--resume-from",
        default="",
        help="Checkpoint path to resume from. Use 'auto' to resume from the latest checkpoint in --out-dir.",
    )
    args = ap.parse_args()

    max_train = None if args.max_train == 0 else args.max_train
    max_eval = None if args.max_eval == 0 else args.max_eval

    import evaluate  # type: ignore
    import numpy as np  # type: ignore
    from datasets import Audio, Dataset  # type: ignore
    from transformers import (  # type: ignore
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperForConditionalGeneration,
        WhisperProcessor,
        trainer_utils,
    )

    repo_root = _repo_root()

    out_dir = args.out_dir or "models/asr_whisper_ewe"
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(repo_root, out_dir.replace("/", os.sep))

    manifest_path = args.manifest
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(repo_root, manifest_path.replace("/", os.sep))

    train_rows = list(_iter_asr_manifest(manifest_path, "train", max_train))
    dev_rows = list(_iter_asr_manifest(manifest_path, "dev", max_eval))

    if not train_rows:
        raise SystemExit("No training rows found")

    for r in train_rows:
        if not os.path.isabs(r["audio"]):
            r["audio"] = os.path.join(repo_root, r["audio"].replace("/", os.sep))
    for r in dev_rows:
        if not os.path.isabs(r["audio"]):
            r["audio"] = os.path.join(repo_root, r["audio"].replace("/", os.sep))

    ds_train = Dataset.from_list(train_rows).cast_column("audio", Audio(sampling_rate=16000))
    ds_dev = Dataset.from_list(dev_rows).cast_column("audio", Audio(sampling_rate=16000)) if dev_rows else None

    processor = WhisperProcessor.from_pretrained(args.model, language=args.language, task=args.task)
    model = WhisperForConditionalGeneration.from_pretrained(args.model)

    if hasattr(processor, "get_decoder_prompt_ids"):
        model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language=args.language, task=args.task)

    def prepare(batch: dict[str, Any]):
        audio = batch["audio"]
        batch["input_features"] = processor.feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
        batch["labels"] = processor.tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_label_length,
        ).input_ids
        return batch

    ds_train_p = ds_train.map(prepare, remove_columns=ds_train.column_names)
    ds_dev_p = ds_dev.map(prepare, remove_columns=ds_dev.column_names) if ds_dev is not None else None

    def data_collator(features):
        input_features = [{"input_features": f["input_features"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]

        batch = processor.feature_extractor.pad(input_features, return_tensors="pt")
        labels_batch = processor.tokenizer.pad(label_features, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels
        return batch

    wer = evaluate.load("wer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        if isinstance(pred_ids, tuple):
            pred_ids = pred_ids[0]

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_ids = np.where(label_ids != -100, label_ids, processor.tokenizer.pad_token_id)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        pred_str = [s.strip() for s in pred_str]
        label_str = [s.strip() for s in label_str]
        return {"wer": wer.compute(predictions=pred_str, references=label_str)}

    os.makedirs(out_dir, exist_ok=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        fp16=False,
        evaluation_strategy="steps" if ds_dev_p is not None else "no",
        save_strategy="steps",
        eval_steps=500,
        save_steps=500,
        logging_steps=50,
        predict_with_generate=True,
        generation_max_length=args.max_label_length,
        seed=args.seed,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=ds_train_p,
        eval_dataset=ds_dev_p,
        data_collator=data_collator,
        compute_metrics=compute_metrics if ds_dev_p is not None else None,
        tokenizer=processor.feature_extractor,
    )

    resume_from = None
    if args.resume_from:
        if args.resume_from == "auto":
            resume_from = trainer_utils.get_last_checkpoint(out_dir)
        else:
            resume_from = args.resume_from

    trainer.train(resume_from_checkpoint=resume_from)

    trainer.save_model(out_dir)
    processor.save_pretrained(out_dir)

    print("saved:", out_dir)
    print("manifest:", args.manifest)
    print("language:", args.language, "task:", args.task)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
