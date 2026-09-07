"""Evaluation script for Escalation Assessment Model (Slice 3.8 Revision).

Evaluates:
- Calibration: Brier Score, Expected Calibration Error (ECE), Calibration Bins.
- Discrimination: ROC-AUC, PR-AUC.
- Operational Performance: Accuracy, Precision, Recall, F1 Score.
- Risk Distribution across LOW, MODERATE, and HIGH categories.
- Grounded Explainability and Confidence metrics.

Disclaimers:
- Smoke-test metrics are intended only to verify pipeline functionality.
- Evaluated on SYNTHETIC DEMONSTRATION LABELS ONLY (NOT CLINICAL GROUND TRUTH).
- Does NOT predict clinical diagnosis or provide treatment/intervention advice.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure workspace root is in sys.path
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from backend.ml.training.models.common import enforce_escalation_boundary, set_seed
from backend.ml.training.models.escalation.dataset import (
    DEFAULT_TARGET_HORIZON_DAYS,
    LABEL_DISCLAIMER,
    SMOKE_TEST_DISCLAIMER,
    EscalationConfig,
    EscalationInputRecord,
    build_synthetic_escalation_records,
    split_escalation_records_by_case,
)
from backend.ml.training.models.escalation.model import (
    EscalationAssessmentModel,
)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Escalation Assessment Model (Slice 3.8)")
    parser.add_argument("--model-dir", type=str, default="models/escalation", help="Exported model directory")
    parser.add_argument("--output-file", type=str, default="models/escalation/metrics.json", help="Destination for metrics JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for evaluation split")
    parser.add_argument("--case-count", type=int, default=40, help="Evaluation case count")
    return parser.parse_args(args)


def compute_brier_score(y_true: List[int], y_prob: List[float]) -> float:
    """Mean squared difference between predicted probabilities and binary outcomes."""
    if not y_true:
        return 0.0
    return round(sum((p - y) ** 2 for y, p in zip(y_true, y_prob)) / len(y_true), 4)


def compute_roc_auc(y_true: List[int], y_prob: List[float]) -> float:
    """Computes Area Under ROC Curve via Mann-Whitney U rank statistic."""
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.50

    paired = sorted(zip(y_prob, y_true), key=lambda item: item[0])
    rank_sum_pos = 0.0
    for rank, (_, label) in enumerate(paired, start=1):
        if label == 1:
            rank_sum_pos += rank

    u_stat = rank_sum_pos - (n_pos * (n_pos + 1)) / 2.0
    auc = u_stat / (n_pos * n_neg)
    return round(float(auc), 4)


def compute_pr_auc(y_true: List[int], y_prob: List[float]) -> float:
    """Computes Area Under Precision-Recall Curve (Average Precision)."""
    n_pos = sum(y_true)
    if n_pos == 0:
        return 0.0

    # Sort descending by predicted probability
    paired = sorted(zip(y_prob, y_true), key=lambda item: item[0], reverse=True)
    tp = 0
    fp = 0
    ap = 0.0

    for _, label in paired:
        if label == 1:
            tp += 1
            ap += tp / (tp + fp)
        else:
            fp += 1

    return round(ap / n_pos, 4)


def compute_calibration_curve(
    y_true: List[int],
    y_prob: List[float],
    n_bins: int = 5,
) -> Dict[str, Any]:
    """Calculates binned calibration information and Expected Calibration Error (ECE)."""
    n = len(y_true)
    if n == 0:
        return {"ece": 0.0, "bins": []}

    bin_width = 1.0 / n_bins
    bins_data: List[Dict[str, Any]] = []
    total_ece = 0.0

    for b in range(n_bins):
        b_low = b * bin_width
        b_high = (b + 1) * bin_width
        # Include upper boundary in last bin
        bin_items = [
            (y, p) for y, p in zip(y_true, y_prob)
            if (b_low <= p < b_high) or (b == n_bins - 1 and b_low <= p <= b_high)
        ]
        count = len(bin_items)
        if count > 0:
            mean_prob = sum(p for _, p in bin_items) / count
            empirical_pos = sum(y for y, _ in bin_items) / count
            diff = abs(mean_prob - empirical_pos)
            total_ece += (count / n) * diff
            bins_data.append({
                "range": [round(b_low, 2), round(b_high, 2)],
                "count": count,
                "mean_predicted_probability": round(mean_prob, 4),
                "empirical_positive_rate": round(empirical_pos, 4),
                "calibration_gap": round(diff, 4),
            })
        else:
            bins_data.append({
                "range": [round(b_low, 2), round(b_high, 2)],
                "count": 0,
                "mean_predicted_probability": round((b_low + b_high) / 2.0, 4),
                "empirical_positive_rate": 0.0,
                "calibration_gap": 0.0,
            })

    return {
        "expected_calibration_error": round(total_ece, 4),
        "bins": bins_data,
    }


def compute_classification_metrics(y_true: List[int], y_prob: List[float], threshold: float = 0.50) -> Dict[str, float]:
    """Binary classification accuracy, precision, recall, and F1."""
    y_pred = [1 if p >= threshold else 0 for p in y_prob]
    n = len(y_true)
    if n == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    acc = (tp + tn) / n
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
    }


def evaluate_escalation(
    model_dir: str = "models/escalation",
    output_file: Optional[str] = "models/escalation/metrics.json",
    seed: int = 42,
    case_count: int = 40,
) -> Dict[str, Any]:
    """Runs evaluation on held-out synthetic test records."""
    set_seed(seed)
    m_path = Path(model_dir)

    print("=" * 74)
    print("  AAROH — Escalation Assessment Model Evaluation (Slice 3.8 Revision)")
    print("=" * 74)
    print(f"Model Directory:    {model_dir}")
    print(f"Supervision Notice: {LABEL_DISCLAIMER}")
    print(f"Random Seed:        {seed}")
    print("-" * 74)

    # 1. Load Model
    model = EscalationAssessmentModel(seed=seed)
    weights_path = m_path / "weights"
    if weights_path.exists():
        with open(weights_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model.weights = data["weights"]
        model.intercept = data["intercept"]
        model.feature_names = data.get("feature_names", model.feature_names)
        model.is_fitted = True
        print(f"Loaded weights and intercept from {weights_path}")
    else:
        print(f"Warning: {weights_path} not found, using calibrated baseline weights.")

    # Load config if available
    config_path = m_path / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg_data = json.load(f)
        model.config = EscalationConfig(
            target_horizon_days=cfg_data.get("target_horizon_days", DEFAULT_TARGET_HORIZON_DAYS),
            threshold_low_moderate=cfg_data.get("threshold_low_moderate", 0.40),
            threshold_moderate_high=cfg_data.get("threshold_moderate_high", 0.75),
            min_confidence_threshold=cfg_data.get("min_confidence_threshold", 0.30),
        )

    # 2. Build Evaluation Records
    eval_records = build_synthetic_escalation_records(case_count=case_count, seed=seed + 999)
    _, test_records = split_escalation_records_by_case(eval_records, val_ratio=0.5, seed=seed + 999)
    print(f"Loaded {len(test_records)} held-out case records for evaluation")

    # 3. Predict on Held-out Records
    y_true: List[int] = []
    y_prob: List[float] = []
    risk_levels: List[str] = []
    confidences: List[float] = []

    for r in test_records:
        out = model.predict_escalation(r)
        for k in out.keys():
            enforce_escalation_boundary(k)

        y_true.append(r.synthetic_escalation_target if r.synthetic_escalation_target is not None else 0)
        prob = out["escalation_probability"] if out["escalation_probability"] is not None else 0.0
        y_prob.append(prob)
        if out["risk_level"]:
            risk_levels.append(out["risk_level"])
        confidences.append(out["confidence"])

    # 4. Calibration & Discrimination Metrics
    brier = compute_brier_score(y_true, y_prob)
    roc_auc = compute_roc_auc(y_true, y_prob)
    pr_auc = compute_pr_auc(y_true, y_prob)
    calib_curve = compute_calibration_curve(y_true, y_prob, n_bins=5)
    class_metrics = compute_classification_metrics(y_true, y_prob)

    # Risk Distribution
    risk_dist = {
        "LOW": risk_levels.count("LOW"),
        "MODERATE": risk_levels.count("MODERATE"),
        "HIGH": risk_levels.count("HIGH"),
    }
    n_total = len(test_records)
    risk_pcts = {k: round(100.0 * v / n_total, 1) for k, v in risk_dist.items()} if n_total else {}

    report: Dict[str, Any] = {
        "model_type": "logistic_regression_escalation_model",
        "sample_count": n_total,
        "target_horizon_days": model.config.target_horizon_days,
        "calibration": {
            "brier_score": brier,
            "expected_calibration_error": calib_curve["expected_calibration_error"],
            "calibration_bins": calib_curve["bins"],
        },
        "discrimination": {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
        },
        "classification": class_metrics,
        "risk_level_distribution": {
            "counts": risk_dist,
            "percentages": risk_pcts,
        },
        "mean_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "label_disclaimer": LABEL_DISCLAIMER,
        "smoke_test_disclaimer": SMOKE_TEST_DISCLAIMER,
    }

    # Print Report
    print("\n" + "-" * 74)
    print("                     ESCALATION EVALUATION REPORT")
    print("-" * 74)
    print(f"Validation Samples:               {n_total}")
    print(f"Target Horizon Days:              {model.config.target_horizon_days}")
    print(f"ROC-AUC:                          {roc_auc:.4f}")
    print(f"PR-AUC:                           {pr_auc:.4f}")
    print(f"Brier Score:                      {brier:.4f}")
    print(f"Expected Calibration Error (ECE): {calib_curve['expected_calibration_error']:.4f}")
    print(f"Accuracy:                         {class_metrics['accuracy']:.4f}")
    print(f"Precision:                        {class_metrics['precision']:.4f}")
    print(f"Recall:                           {class_metrics['recall']:.4f}")
    print(f"F1 Score:                         {class_metrics['f1']:.4f}")
    print(f"Risk Distribution (Counts):       {risk_dist}")
    print(f"Risk Distribution (%):            {risk_pcts}")
    print(f"Mean Evidence-Based Confidence:   {report['mean_confidence']:.4f}")

    print("\nCalibration Bins:")
    for b in calib_curve["bins"]:
        print(f"  Range {b['range']} | Count: {b['count']:2d} | Mean Prob: {b['mean_predicted_probability']:.2f} | Observed Rate: {b['empirical_positive_rate']:.2f} | Gap: {b['calibration_gap']:.4f}")

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
    evaluate_escalation(
        model_dir=args.model_dir,
        output_file=args.output_file,
        seed=args.seed,
        case_count=args.case_count,
    )


if __name__ == "__main__":
    main()
