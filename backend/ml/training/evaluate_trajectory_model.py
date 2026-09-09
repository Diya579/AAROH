"""Evaluation script for Longitudinal Trajectory Model (Slice 3.7).

Reports:
- Overall Accuracy
- Multi-class Precision, Recall, Macro F1, and Weighted F1
- Confusion Matrix (4x4 across STABLE, IMPROVING, WORSENING, RAPIDLY_WORSENING)
- Per-class Accuracy
- Trajectory Distribution (predicted vs ground truth counts and percentages)
- Mean Trajectory Embedding Norm Invariant (unit sphere: norm = 1.0)
- Strict Clinical Boundary Enforcement across all outputs

Disclaimers:
- Smoke-test metrics are intended only to verify pipeline functionality.
- Evaluated on SYNTHETIC DEMONSTRATION LABELS ONLY (NOT CLINICAL GROUND TRUTH).
- Does NOT predict clinical diagnosis, future escalation, or psychiatric risk.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.ml.training.models.common import enforce_trajectory_boundary, set_seed
from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    ID_TO_LABEL,
    LABEL_DISCLAIMER,
    LABEL_TO_ID,
    SMOKE_TEST_DISCLAIMER,
    VALID_TRAJECTORY_LABELS,
    CaseTrajectory,
    build_synthetic_trajectories,
    split_trajectories_by_case,
)
from backend.ml.training.models.trajectory.model import (
    LongitudinalTrajectoryModel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Longitudinal Trajectory Model (Slice 3.7)")
    parser.add_argument("--model-dir", type=str, default="models/trajectory", help="Exported model directory")
    parser.add_argument("--output-file", type=str, default="models/trajectory/metrics.json", help="Destination for metrics JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for evaluation split")
    parser.add_argument("--case-count", type=int, default=32, help="Evaluation case count")
    parser.add_argument("--history-window", type=int, default=DEFAULT_HISTORY_WINDOW, help="Fixed history window")
    return parser.parse_args()


def compute_multiclass_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Sequence[str] = VALID_TRAJECTORY_LABELS,
) -> Dict[str, Any]:
    """Computes multi-class accuracy, per-class metrics, confusion matrix, macro & weighted F1."""
    n = len(y_true)
    if n == 0:
        return {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "per_class": {},
            "confusion_matrix": {},
        }

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = round(correct / n, 4)

    # 4x4 Confusion matrix: matrix[true_label][pred_label]
    cm: Dict[str, Dict[str, int]] = {
        tl: {pl: 0 for pl in labels} for tl in labels
    }
    for yt, yp in zip(y_true, y_pred):
        if yt in cm and yp in cm[yt]:
            cm[yt][yp] += 1

    per_class: Dict[str, Dict[str, float]] = {}
    f1_list: List[float] = []
    prec_list: List[float] = []
    rec_list: List[float] = []
    weighted_f1_sum = 0.0

    for lbl in labels:
        tp = cm[lbl][lbl]
        fp = sum(cm[other][lbl] for other in labels if other != lbl)
        fn = sum(cm[lbl][other] for other in labels if other != lbl)
        support = sum(cm[lbl][other] for other in labels)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        acc_class = tp / support if support > 0 else 0.0

        per_class[lbl] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc_class, 4),
            "support": support,
        }
        f1_list.append(f1)
        prec_list.append(prec)
        rec_list.append(rec)
        weighted_f1_sum += f1 * support

    macro_prec = round(sum(prec_list) / len(labels), 4)
    macro_rec = round(sum(rec_list) / len(labels), 4)
    macro_f1 = round(sum(f1_list) / len(labels), 4)
    weighted_f1 = round(weighted_f1_sum / n, 4) if n > 0 else 0.0

    return {
        "accuracy": accuracy,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def evaluate_trajectory(
    model_dir: str = "models/trajectory",
    output_file: Optional[str] = "models/trajectory/metrics.json",
    seed: int = 42,
    case_count: int = 32,
    history_window: int = DEFAULT_HISTORY_WINDOW,
) -> Dict[str, Any]:
    """Runs evaluation for Longitudinal Trajectory Model on held-out synthetic test cases."""
    set_seed(seed)
    m_path = Path(model_dir)

    print("=" * 74)
    print("  AAROH — Longitudinal Trajectory Model Evaluation (Slice 3.7)")
    print("=" * 74)
    print(f"Model Directory:    {model_dir}")
    print(f"Supervision Notice: {LABEL_DISCLAIMER}")
    print(f"Random Seed:        {seed}")
    print(f"History Window:     {history_window}")
    print("-" * 74)

    # 1. Load Model
    if (m_path / "pytorch_model.bin").exists():
        model = LongitudinalTrajectoryModel.load_from_artifact(m_path, device="cpu")
    else:
        model = LongitudinalTrajectoryModel(history_window=history_window, seed=seed)
    weights_path = m_path / "weights"
    if weights_path.exists():
        with open(weights_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        model.W_proj = state["W_proj"]
        model.b_proj = state["b_proj"]
        model.W_agg1 = state["W_agg1"]
        model.b_agg1 = state["b_agg1"]
        model.W_agg2 = state["W_agg2"]
        model.b_agg2 = state["b_agg2"]
        model.W_head1 = state["W_head1"]
        model.b_head1 = state["b_head1"]
        model.W_head2 = state["W_head2"]
        model.b_head2 = state["b_head2"]
        print(f"Successfully loaded exported weights from {weights_path}")
    else:
        print(f"Warning: {weights_path} not found; evaluating with initialized weights.")

    # 2. Build Evaluation Cases (independent seed + held-out cases)
    eval_cases = build_synthetic_trajectories(
        case_count=case_count,
        min_interactions=3,
        max_interactions=14,
        seed=seed + 999,
    )
    _, test_cases = split_trajectories_by_case(eval_cases, val_ratio=0.5, seed=seed + 999)
    print(f"Loaded {len(test_cases)} held-out case trajectories for evaluation: {[c.case_id for c in test_cases]}")

    # 3. Predict & Collect Metrics
    y_true: List[str] = []
    y_pred: List[str] = []
    embedding_norms: List[float] = []
    scores: List[float] = []

    for case in test_cases:
        out = model.predict_trajectory(case)

        # Validate clinical boundaries
        for k in out.keys():
            enforce_trajectory_boundary(k)

        p_label = out["trajectory_label"]
        t_label = case.trajectory_label
        emb = out["trajectory_embedding"]

        norm = math.sqrt(sum(v * v for v in emb))
        embedding_norms.append(norm)

        y_true.append(t_label)
        y_pred.append(p_label)
        scores.append(out["trajectory_score"])

    # 4. Metrics Computation
    metrics = compute_multiclass_metrics(y_true, y_pred)
    mean_norm = round(float(sum(embedding_norms) / len(embedding_norms)), 4) if embedding_norms else 1.0

    # Label distribution
    pred_dist: Dict[str, int] = {lbl: y_pred.count(lbl) for lbl in VALID_TRAJECTORY_LABELS}
    true_dist: Dict[str, int] = {lbl: y_true.count(lbl) for lbl in VALID_TRAJECTORY_LABELS}
    n_total = len(test_cases)
    pred_pcts = {lbl: round(100.0 * cnt / n_total, 1) for lbl, cnt in pred_dist.items()} if n_total else {}

    report: Dict[str, Any] = {
        "model_type": "longitudinal_trajectory_model",
        "sample_count": n_total,
        "history_window": history_window,
        "accuracy": metrics["accuracy"],
        "macro_precision": metrics["macro_precision"],
        "macro_recall": metrics["macro_recall"],
        "macro_f1": metrics["macro_f1"],
        "weighted_f1": metrics["weighted_f1"],
        "per_class_metrics": metrics["per_class"],
        "confusion_matrix": metrics["confusion_matrix"],
        "predicted_label_distribution": {
            "counts": pred_dist,
            "percentages": pred_pcts,
        },
        "ground_truth_distribution": true_dist,
        "mean_trajectory_embedding_norm": mean_norm,
        "embedding_norm_invariant_satisfied": bool(abs(mean_norm - 1.0) < 1e-3),
        "clinical_boundaries_enforced": True,
        "label_disclaimer": LABEL_DISCLAIMER,
        "smoke_test_disclaimer": SMOKE_TEST_DISCLAIMER,
    }

    # Print Report
    print("\n" + "-" * 74)
    print("                     TRAJECTORY EVALUATION REPORT")
    print("-" * 74)
    print(f"Validation Cases:                 {n_total}")
    print(f"Overall Accuracy:                 {metrics['accuracy']:.4f}")
    print(f"Macro Precision:                  {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:                     {metrics['macro_recall']:.4f}")
    print(f"Macro F1:                         {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:                      {metrics['weighted_f1']:.4f}")
    print(f"Mean Embedding Norm:              {mean_norm:.4f} (Expected: 1.0000)")
    print(f"Predicted Distribution:           {pred_dist}")
    print(f"Predicted Percentages:            {pred_pcts}")
    print("\nPer-Class Breakdown:")
    for lbl, vals in metrics["per_class"].items():
        print(f"  {lbl:<18} | Prec: {vals['precision']:.2f} | Rec: {vals['recall']:.2f} | F1: {vals['f1']:.2f} | Support: {vals['support']}")
    print("\nConfusion Matrix (Rows=True, Cols=Pred):")
    for tl in VALID_TRAJECTORY_LABELS:
        row_str = "  ".join(f"{cm_val:3d}" for cm_val in metrics["confusion_matrix"][tl].values())
        print(f"  {tl:<18}: [ {row_str} ]")

    print("-" * 74)
    print("                     SMOKE-TEST EVALUATION NOTICE")
    print("-" * 74)
    print(f"* {SMOKE_TEST_DISCLAIMER}")
    print(f"* {LABEL_DISCLAIMER}")
    print("=" * 74 + "\n")

    if output_file:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved evaluation metrics to {out_p}")

    return report


def main() -> None:
    args = parse_args()
    evaluate_trajectory(
        model_dir=args.model_dir,
        output_file=args.output_file,
        seed=args.seed,
        case_count=args.case_count,
        history_window=args.history_window,
    )


if __name__ == "__main__":
    main()
