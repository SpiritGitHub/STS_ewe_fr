"""Train / fine-tune a MT model using your Ewe↔French bitext manifest.

This is the MT training entrypoint in the ml/ layout.

Expected TSV columns:
- split (train/dev/test)
- ee
- fr

Default manifest path:
- data/manifests/mt/manifest_ewe_fr_bitext.tsv

Usage (PowerShell)
  # ee -> fr
  F:/STS/.venv/Scripts/python.exe ml/mt/train_mt.py `
    --manifest data/manifests/mt/manifest_ewe_fr_bitext.tsv `
    --direction ee_to_fr `
    --model facebook/nllb-200-distilled-600M `
    --out-dir models/mt_ee_to_fr `
    --max-train 200000 `
    --max-eval 5000
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Literal


Direction = Literal["ee_to_fr", "fr_to_ee"]


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _iter_manifest(manifest_path: str, wanted_split: str):
    with open(manifest_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if (row.get("split") or "").strip() != wanted_split:
                continue
            ee = (row.get("ee") or "").strip()
            fr = (row.get("fr") or "").strip()
            if not ee or not fr:
                continue
            yield {"ee": ee, "fr": fr}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifests/mt/manifest_ewe_fr_bitext.tsv")
    ap.add_argument("--direction", choices=["ee_to_fr", "fr_to_ee"], required=True)
    ap.add_argument("--model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--out-dir", default="")

    ap.add_argument("--max-train", type=int, default=0, help="0 = no limit")
    ap.add_argument("--max-eval", type=int, default=0, help="0 = no limit")

    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--eval-batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument(
        "--resume-from",
        default="",
        help="Checkpoint path to resume from. Use 'auto' to resume from the latest checkpoint in --out-dir.",
    )

    args = ap.parse_args()

    import evaluate  # type: ignore
    import numpy as np  # type: ignore
    from datasets import Dataset  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        trainer_utils,
    )

    src_lang = "ewe_Latn" if args.direction == "ee_to_fr" else "fra_Latn"
    tgt_lang = "fra_Latn" if args.direction == "ee_to_fr" else "ewe_Latn"

    repo_root = _repo_root()

    out_dir = (args.out_dir or "").strip()
    if not out_dir:
        out_dir = os.path.join("models", f"mt_{args.direction}")
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(repo_root, out_dir.replace("/", os.sep))

    manifest_path = args.manifest
    if not os.path.isabs(manifest_path):
        manifest_path = os.path.join(repo_root, manifest_path.replace("/", os.sep))

    train_examples = list(_iter_manifest(manifest_path, "train"))
    dev_examples = list(_iter_manifest(manifest_path, "dev"))

    if args.max_train and args.max_train > 0:
        train_examples = train_examples[: args.max_train]
    if args.max_eval and args.max_eval > 0:
        dev_examples = dev_examples[: args.max_eval]

    if not train_examples:
        raise SystemExit("No train examples found")

    ds_train = Dataset.from_list(train_examples)
    ds_dev = Dataset.from_list(dev_examples) if dev_examples else None

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if hasattr(tokenizer, "src_lang"):
        tokenizer.src_lang = src_lang  # type: ignore[attr-defined]

    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    def preprocess(batch):
        if args.direction == "ee_to_fr":
            inputs = batch["ee"]
            targets = batch["fr"]
        else:
            inputs = batch["fr"]
            targets = batch["ee"]

        model_inputs = tokenizer(inputs, max_length=args.max_length, truncation=True)

        with tokenizer.as_target_tokenizer():
            labels = tokenizer(targets, max_length=args.max_length, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    ds_train_tok = ds_train.map(preprocess, batched=True, remove_columns=ds_train.column_names)
    ds_dev_tok = None
    if ds_dev is not None:
        ds_dev_tok = ds_dev.map(preprocess, batched=True, remove_columns=ds_dev.column_names)

    metric = evaluate.load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)

        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        decoded_preds = [p.strip() for p in decoded_preds]
        decoded_labels = [[l.strip()] for l in decoded_labels]
        res = metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"sacrebleu": res["score"]}

    os.makedirs(out_dir, exist_ok=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        predict_with_generate=True,
        evaluation_strategy="steps" if ds_dev_tok is not None else "no",
        save_strategy="steps",
        eval_steps=500,
        save_steps=500,
        logging_steps=50,
        fp16=False,
        seed=args.seed,
        report_to=[],
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=ds_train_tok,
        eval_dataset=ds_dev_tok,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics if ds_dev_tok is not None else None,
    )

    resume_from = None
    if args.resume_from:
        if args.resume_from == "auto":
            resume_from = trainer_utils.get_last_checkpoint(out_dir)
        else:
            resume_from = args.resume_from

    trainer.train(resume_from_checkpoint=resume_from)

    trainer.save_model(out_dir)
    tokenizer.save_pretrained(out_dir)

    print("saved:", out_dir)
    print("direction:", args.direction)
    print("src_lang:", src_lang, "tgt_lang:", tgt_lang)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
