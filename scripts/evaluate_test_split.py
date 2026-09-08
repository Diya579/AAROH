#!/usr/bin/env python3
"""AAROH — Canonical Multi-Label Evaluation on the Held-Out TEST Split.

Executes read-only inference and evaluation of the fine-tuned production Text Emotion model
using the exact canonical multi-label pipeline from `train_text_emotion.py`:
- Loads exported model via `TextEmotionModel.load_from_artifact`
- Evaluates the entire held-out TEST split (10,854 samples: English + Hindi)
- Enforces model.eval() and torch.no_grad()
- Performs memory-safe batched inference (default batch_size=16)
- Evaluates multi-label precision, recall, Micro/Macro F1 (th=0.50)
- Executes threshold sweep over [0.15, 0.60] to find optimal decision threshold
- Computes mean Brier calibration score and per-class metrics across all 28 emotions
- Generates language-specific performance breakdowns (English vs. Hindi)
- Strictly read-only: does not modify model weights, checkpoints, or existing repository files

Usage:
    python3 scripts/evaluate_test_split.py [OPTIONS]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Anchor repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    multilabel_confusion_matrix,
    precision_recall_fscore_support,
)

from backend.ml.training.models.text_emotion.dataset import (
    GOEMOTIONS_TAXONOMY,
    load_combined_emotion_records,
)
from backend.ml.training.models.text_emotion.model import TextEmotionModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AAROH — Canonical Multi-Label Evaluation on Held-Out TEST Split"
    )
    parser.add_argument(
        "--model-dir",
        default="checkpoints/text_emotion/colab_finetune_40k_run",
        help="Path to exported model artifact directory (default: checkpoints/text_emotion/colab_finetune_40k_run)",
    )
    parser.add_argument(
        "--data-dir",
        default="datasets/processed",
        help="Path to datasets/processed directory (default: datasets/processed)",
    )
    parser.add_argument(
        "--output-file",
        default="checkpoints/text_emotion/colab_finetune_40k_run/test_split_metrics.json",
        help="Path to write evaluation metrics JSON",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Memory-safe inference batch size (default: 16)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Inference device ('cuda' or 'cpu', defaults to auto-detect)",
    )
    return parser.parse_args()


def compute_metrics_dict(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    th: float = 0.5,
) -> dict[str, Any]:
    """Canonical multi-label metric calculation copied directly from train_text_emotion.py:637-678."""
    if len(y_true) == 0:
        return {}

    bin_mat = (y_probs >= th).astype(np.float32)
    p_mi, r_mi, f1_mi, _ = precision_recall_fscore_support(y_true, bin_mat, average="micro", zero_division=0)
    p_ma, r_ma, f1_ma, _ = precision_recall_fscore_support(y_true, bin_mat, average="macro", zero_division=0)
    em = accuracy_score(y_true, bin_mat)
    brier = float(np.mean([brier_score_loss(y_true[:, c], y_probs[:, c]) for c in range(y_true.shape[1])]))

    p_c, r_c, f1_c, sup_c = precision_recall_fscore_support(y_true, bin_mat, average=None, zero_division=0)
    cm_mat = multilabel_confusion_matrix(y_true, bin_mat)
    per_cls = {}
    cm_sum = {}
    for c, name in enumerate(GOEMOTIONS_TAXONOMY):
        per_cls[name] = {
            "precision": round(float(p_c[c]), 4),
            "recall": round(float(r_c[c]), 4),
            "f1": round(float(f1_c[c]), 4),
            "support": int(sup_c[c]),
            "predicted_positives": int(np.sum(bin_mat[:, c])),
        }
        tn, fp, fn, tp = cm_mat[c].ravel()
        cm_sum[name] = {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)}

    zero_rec = [n for n, m in per_cls.items() if m["recall"] == 0.0]
    return {
        "exact_match_accuracy": round(float(em), 4),
        "micro_precision": round(float(p_mi), 4),
        "micro_recall": round(float(r_mi), 4),
        "micro_f1": round(float(f1_mi), 4),
        "macro_precision": round(float(p_ma), 4),
        "macro_recall": round(float(r_ma), 4),
        "macro_f1": round(float(f1_ma), 4),
        "mean_brier_score": round(float(brier), 4),
        "samples_evaluated": len(y_true),
        "total_true_positives": int(np.sum(y_true)),
        "total_predicted_positives": int(np.sum(bin_mat)),
        "zero_recall_classes_count": len(zero_rec),
        "zero_recall_classes": zero_rec,
        "per_class_metrics": per_cls,
        "confusion_matrix_summary": cm_sum,
    }


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    model_dir = Path(args.model_dir)
    output_path = Path(args.output_file)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 75)
    print("  AAROH — CANONICAL TEST SPLIT EVALUATION (INFERENCE ONLY)")
    print("=" * 75)
    print(f"Model Directory:    {model_dir}")
    print(f"Dataset Directory:  {data_dir}")
    print(f"Metrics Output:     {output_path}")
    print(f"Batch Size:         {args.batch_size}")
    print(f"Execution Device:   {device}")
    if device == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU Hardware:       {props.name} ({round(props.total_memory / (1024**3), 2)} GB VRAM)")
    print("-" * 75)

    # 1. Verify model artifact exists
    if not model_dir.exists():
        print(f"[ERROR] Model artifact directory does not exist: {model_dir}")
        sys.exit(1)

    # 2. Load model directly from artifact
    print(f"\n[1/5] Loading fine-tuned production model from '{model_dir}'...")
    model = TextEmotionModel.load_from_artifact(model_dir, device=device)
    print(f"  ✓ Model loaded successfully (Execution Mode: {model.execution_mode}, Backbone: {model.backbone})")

    # 3. Load entire held-out TEST split
    print(f"\n[2/5] Loading held-out TEST split from '{data_dir}'...")
    test_records = load_combined_emotion_records(data_dir, split="test")
    if not test_records:
        print(f"[ERROR] No records loaded for split 'test' in {data_dir}!")
        sys.exit(1)

    en_count = sum(1 for r in test_records if r.get("language") == "en")
    hi_count = sum(1 for r in test_records if r.get("language") == "hi")
    print(f"  ✓ Loaded {len(test_records)} TEST samples (English: {en_count:,}, Hindi: {hi_count:,})")

    # 4. Multi-hot binary ground-truth matrix construction
    num_classes = len(GOEMOTIONS_TAXONOMY)
    test_texts = [r.get("text", "") for r in test_records]
    test_true_labels = []
    for r in test_records:
        vec = [0.0] * num_classes
        for lid in r.get("label_ids", []):
            if 0 <= lid < num_classes:
                vec[lid] = 1.0
        test_true_labels.append(vec)
    test_true_matrix = np.array(test_true_labels, dtype=np.float32)

    # 5. Memory-safe batched inference
    print(f"\n[3/5] Executing memory-safe batched inference (batch_size={args.batch_size})...")
    t0 = time.time()
    preds = model.encode_and_predict(test_texts, device=device, batch_size=args.batch_size)
    duration = time.time() - t0
    throughput = round(len(test_records) / max(0.001, duration), 1)
    print(f"  ✓ Inference completed in {duration:.2f}s ({throughput} samples/sec).")

    pred_prob_matrix = np.zeros_like(test_true_matrix)
    for i, p_dict in enumerate(preds["emotion_probabilities"]):
        for c, name in enumerate(GOEMOTIONS_TAXONOMY):
            pred_prob_matrix[i, c] = p_dict.get(name, 0.0)

    # 6. Canonical metric calculation at threshold = 0.50
    print("\n[4/5] Computing canonical multi-label metrics and threshold sweep...")
    agg_eval = compute_metrics_dict(test_true_matrix, pred_prob_matrix, th=0.5)

    # Language-specific evaluations
    en_indices = [i for i, r in enumerate(test_records) if r.get("language") == "en"]
    hi_indices = [i for i, r in enumerate(test_records) if r.get("language") == "hi"]
    en_eval = compute_metrics_dict(test_true_matrix[en_indices], pred_prob_matrix[en_indices], th=0.5) if en_indices else {}
    hi_eval = compute_metrics_dict(test_true_matrix[hi_indices], pred_prob_matrix[hi_indices], th=0.5) if hi_indices else {}

    # Canonical threshold sweep (0.15 to 0.60, step=0.05)
    threshold_search = {}
    best_th = 0.5
    best_th_macro_f1 = float(agg_eval["macro_f1"])
    for th in np.arange(0.15, 0.65, 0.05):
        th_val = round(float(th), 2)
        th_bin = (pred_prob_matrix >= th_val).astype(np.float32)
        _, _, th_f1, _ = precision_recall_fscore_support(test_true_matrix, th_bin, average="macro", zero_division=0)
        threshold_search[str(th_val)] = round(float(th_f1), 4)
        if th_f1 > best_th_macro_f1:
            best_th_macro_f1 = float(th_f1)
            best_th = th_val

    # 7. Write metrics to destination
    print(f"\n[5/5] Saving test metrics to '{output_path}'...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "split": "test",
        "model_artifact": str(model_dir),
        "samples_evaluated": len(test_records),
        "duration_seconds": round(duration, 2),
        "throughput_samples_per_sec": throughput,
        "exact_match_accuracy": agg_eval["exact_match_accuracy"],
        "micro_precision": agg_eval["micro_precision"],
        "micro_recall": agg_eval["micro_recall"],
        "micro_f1": agg_eval["micro_f1"],
        "macro_precision": agg_eval["macro_precision"],
        "macro_recall": agg_eval["macro_recall"],
        "macro_f1": agg_eval["macro_f1"],
        "mean_brier_score": agg_eval["mean_brier_score"],
        "best_macro_f1_threshold": best_th,
        "best_macro_f1_at_best_threshold": round(best_th_macro_f1, 4),
        "threshold_curve": threshold_search,
        "zero_recall_classes_count_at_05": agg_eval["zero_recall_classes_count"],
        "zero_recall_classes_at_05": agg_eval["zero_recall_classes"],
        "language_specific": {
            "english": en_eval,
            "hindi": hi_eval,
        },
        "per_class_metrics": agg_eval["per_class_metrics"],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Successfully wrote test metrics report to {output_path}")

    # =========================================================================
    # FORMAL TEST EVALUATION DISPLAY
    # =========================================================================
    print("\n" + "=" * 75)
    print("  CANONICAL TEST SPLIT EVALUATION RESULTS")
    print("=" * 75)
    print(f"  Total Samples Evaluated:   {len(test_records):,}")
    print(f"  Inference Duration:        {duration:.2f}s ({throughput} samples/sec)")
    print(f"  Aggregate Micro F1 (0.50): {agg_eval['micro_f1']:.4f}  (P: {agg_eval['micro_precision']:.4f}, R: {agg_eval['micro_recall']:.4f})")
    print(f"  Aggregate Macro F1 (0.50): {agg_eval['macro_f1']:.4f}  (P: {agg_eval['macro_precision']:.4f}, R: {agg_eval['macro_recall']:.4f})")
    print(f"  Mean Brier Score:          {agg_eval['mean_brier_score']:.4f}")
    print(f"  Best Threshold:            {best_th} (Macro F1 at Best Threshold: {best_th_macro_f1:.4f})")

    print("\n--- Language Breakdowns (at threshold=0.50) ---")
    if en_eval:
        print(f"  English (N={len(en_indices):,}): Micro F1 = {en_eval['micro_f1']:.4f} | Macro F1 = {en_eval['macro_f1']:.4f} | Brier = {en_eval['mean_brier_score']:.4f}")
    if hi_eval:
        print(f"  Hindi   (N={len(hi_indices):,}): Micro F1 = {hi_eval['micro_f1']:.4f} | Macro F1 = {hi_eval['macro_f1']:.4f} | Brier = {hi_eval['mean_brier_score']:.4f}")

    print("\n--- Per-Class Metrics (Threshold = 0.50) ---")
    print(f"  {'Class Name':<16} | {'Precision':<9} | {'Recall':<9} | {'F1':<9} | {'Support':<7} | {'Pred Pos':<8}")
    print("  " + "-" * 70)
    for c_name in GOEMOTIONS_TAXONOMY:
        cm = agg_eval["per_class_metrics"][c_name]
        print(f"  {c_name:<16} | {cm['precision']:<9.4f} | {cm['recall']:<9.4f} | {cm['f1']:<9.4f} | {cm['support']:<7} | {cm['predicted_positives']:<8}")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()
