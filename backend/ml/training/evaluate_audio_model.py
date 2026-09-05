#!/usr/bin/env python3
"""Evaluation suite for AAROH Audio Emotion Representation Model (Slice 3.4).

Evaluates the model strictly on holdout test actors to prevent actor leakage.
Reports:
- Overall Accuracy
- Precision
- Recall
- Macro F1
- Weighted F1
- 8x8 Confusion Matrix
- Per-class accuracy for all 8 RAVDESS emotions:
  (neutral, calm, happy, sad, angry, fearful, disgust, surprised)

Usage:
    python3 -m backend.ml.training.evaluate_audio_model [OPTIONS]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

from backend.ml.training.models.audio_emotion.dataset import (
    RAVDESS_EMOTIONS,
    RavdessDataset,
    split_ravdess_records_by_actor,
)
from backend.ml.training.models.audio_emotion.model import AudioEmotionModel
from backend.ml.training.models.common import (
    compute_accuracy,
    compute_confusion_matrix,
    compute_per_class_accuracy,
    compute_precision_recall_f1,
    enforce_audio_emotion_boundary,
)
from backend.ml.training.preprocessing.common import read_jsonl


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Audio Emotion Representation Model.")
    parser.add_argument("--models-dir", default="models/audio_emotion", help="Directory where model is exported.")
    parser.add_argument("--data-dir", default="datasets/processed", help="Directory of processed JSONL datasets.")
    parser.add_argument("--output-file", default="models/audio_emotion/evaluation_metrics.json", help="Path to save output metrics JSON.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for programmatic actor split.")
    return parser.parse_args(args)


def evaluate_audio_emotion(
    data_dir: Path | str = "datasets/processed",
    models_dir: Path | str = "models/audio_emotion",
    seed: int = 42,
    output_file: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Evaluates the Audio Emotion Model on holdout test actors."""
    enforce_audio_emotion_boundary("audio_emotion_evaluation")

    p_dir = Path(data_dir)
    jsonl_path = p_dir / "ravdess.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"RAVDESS dataset not found: {jsonl_path}")

    all_records = read_jsonl(jsonl_path)
    train_records, test_records = split_ravdess_records_by_actor(
        all_records,
        test_ratio=0.25,
        seed=seed,
    )

    test_actors = sorted(list(set(r["actor"] for r in test_records)))
    train_actors = sorted(list(set(r["actor"] for r in train_records)))

    # Zero leakage check
    if set(test_actors).intersection(set(train_actors)):
        raise ValueError("Actor leakage detected in evaluation split!")

    print(f"Evaluating Audio Emotion Model on {len(test_records)} holdout samples (Actors: {test_actors})")

    model = AudioEmotionModel()
    m_dir = Path(models_dir)
    ckpt_file = m_dir / "pytorch_model.bin"
    if ckpt_file.exists():
        try:
            import torch
            model.load_state_dict(torch.load(ckpt_file, map_location="cpu"))
        except Exception:
            try:
                with open(ckpt_file, "rb") as f:
                    model.load_state_dict(json.loads(f.read().decode("utf-8")))
            except Exception:
                pass

    dataset = RavdessDataset(test_records)
    waveforms = [dataset[i]["waveform"] for i in range(len(dataset))]
    targets = [dataset[i]["emotion"] for i in range(len(dataset))]

    eval_preds = model.encode_and_predict(waveforms)
    pred_classes = [
        max(p.items(), key=lambda item: item[1])[0]
        for p in eval_preds["audio_emotion_probabilities"]
    ]

    acc = compute_accuracy(targets, pred_classes)
    prf = compute_precision_recall_f1(targets, pred_classes, classes=RAVDESS_EMOTIONS)
    conf_matrix = compute_confusion_matrix(targets, pred_classes, classes=RAVDESS_EMOTIONS)
    per_class_acc = compute_per_class_accuracy(targets, pred_classes, classes=RAVDESS_EMOTIONS)

    results = {
        "model": "audio_emotion",
        "accuracy": round(acc, 4),
        "precision": round(prf["precision"], 4),
        "recall": round(prf["recall"], 4),
        "macro_f1": round(prf["macro_f1"], 4),
        "weighted_f1": round(prf["weighted_f1"], 4),
        "per_class_accuracy": per_class_acc,
        "confusion_matrix": conf_matrix,
        "classes": list(RAVDESS_EMOTIONS),
        "evaluated_samples": len(test_records),
        "test_actors": test_actors,
        "clinical_boundary_verified": "Audio Emotion != Clinical Distress",
    }

    print("=" * 72)
    print("  AAROH — Audio Emotion Model Evaluation Results")
    print("=" * 72)
    print(f"Overall Accuracy:  {results['accuracy']:.4f}")
    print(f"Macro Precision:   {results['precision']:.4f}")
    print(f"Macro Recall:      {results['recall']:.4f}")
    print(f"Macro F1:          {results['macro_f1']:.4f}")
    print(f"Weighted F1:       {results['weighted_f1']:.4f}")
    print("\nPer-Class Accuracy:")
    for emo, score in per_class_acc.items():
        print(f"  {emo:<12}: {score:.4f}")

    print("\nConfusion Matrix (Rows=True, Cols=Predicted):")
    header = "       " + " ".join(f"{c[:4]:>6}" for c in RAVDESS_EMOTIONS)
    print(header)
    for i, row in enumerate(conf_matrix):
        row_str = f"{RAVDESS_EMOTIONS[i][:6]:<6} " + " ".join(f"{val:>6}" for val in row)
        print(row_str)
    print("=" * 72)

    if output_file:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Saved evaluation metrics to: {out_p}")

    return results


if __name__ == "__main__":
    args = parse_args()
    evaluate_audio_emotion(
        data_dir=args.data_dir,
        models_dir=args.models_dir,
        seed=args.seed,
        output_file=args.output_file,
    )
