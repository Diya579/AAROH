"""Evaluation script for Dynamic Distress Model (Slice 3.6).

Evaluates:
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Pearson Correlation (r)
- Distress Level Distribution (LOW, MODERATE, HIGH, CRITICAL counts & percentages)
- Threshold Classification Accuracy (predicted level vs. synthetic ground truth level)
- Latent Distress Embedding Norm Invariant (unit sphere: norm = 1.0)
- Clinical Boundary Enforcement across all outputs

Strict Notice:
- Evaluated on SYNTHETIC DEMONSTRATION LABELS ONLY (NOT CLINICAL GROUND TRUTH).
- Does NOT predict clinical diagnosis, escalation, or future risk.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.ml.training.models.common import enforce_distress_boundary, set_seed
from backend.ml.training.models.distress.dataset import (
    LABEL_DISCLAIMER,
    DistressInputRecord,
    build_synthetic_distress_records,
    split_distress_records_by_case,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_THRESHOLDS,
    DynamicDistressModel,
)


SMOKE_TEST_DISCLAIMER = (
    "Smoke-test metrics are intended only to verify that the training, "
    "checkpointing, inference, and evaluation pipelines function correctly. "
    "They are NOT indicators of real-world model performance."
)

SYNTHETIC_LABELS_DISCLAIMER = (
    "Synthetic demonstration labels are used solely for engineering verification "
    "and architecture validation. They are NOT clinical ground truth."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Dynamic Distress Model (Slice 3.6)")
    parser.add_argument("--model-dir", type=str, default="models/distress", help="Exported model directory")
    parser.add_argument("--output-file", type=str, default="models/distress/metrics.json", help="Path to write evaluation metrics")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for evaluation split")
    parser.add_argument("--sample-count", type=int, default=80, help="Evaluation sample count")
    return parser.parse_args()


def evaluate_distress(
    model_dir: str = "models/distress",
    output_file: Optional[str] = "models/distress/metrics.json",
    seed: int = 42,
    sample_count: int = 80,
) -> Dict[str, Any]:
    """Runs evaluation for Dynamic Distress Model on held-out synthetic test records."""
    set_seed(seed)
    m_path = Path(model_dir)

    print("=" * 72)
    print("  AAROH — Dynamic Distress Model Evaluation (Slice 3.6)")
    print("=" * 72)
    print(f"Model Directory:    {model_dir}")
    print(f"Supervision Notice: {LABEL_DISCLAIMER}")
    print(f"Random Seed:        {seed}")
    print("-" * 72)

    # 1. Load model configuration & weights (reading versioned thresholds if present)
    cfg_file = m_path / "config.json" if (m_path / "config.json").exists() else (m_path / "thresholds.json" if (m_path / "thresholds.json").exists() else None)
    if (m_path / "pytorch_model.bin").exists():
        model = DynamicDistressModel.load_from_artifact(m_path, device="cpu")
    else:
        model = DynamicDistressModel(seed=seed, config_path=cfg_file)
    weights_path = m_path / "weights"
    if weights_path.exists():
        with open(weights_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        model.W_proj = state["W_proj"]
        model.b_proj = state["b_proj"]
        model.W_res1 = state["W_res1"]
        model.b_res1 = state["b_res1"]
        model.W_res2 = state["W_res2"]
        model.b_res2 = state["b_res2"]
        model.W_reg1 = state["W_reg1"]
        model.b_reg1 = state["b_reg1"]
        model.W_reg2 = state["W_reg2"]
        model.b_reg2 = state["b_reg2"]
        print(f"Successfully loaded exported weights from {weights_path}")
    else:
        print(f"Warning: {weights_path} not found; evaluating with initialized model weights.")

    # 2. Build held-out records (using independent seed and case splitting)
    records = build_synthetic_distress_records(count=sample_count, seed=seed + 999)
    _, test_records = split_distress_records_by_case(records, val_ratio=0.4, seed=seed + 999)
    test_cases = sorted(list(set(r.case_id for r in test_records)))
    print(f"Loaded {len(test_records)} evaluation records across {len(test_cases)} held-out cases: {test_cases}")

    # 3. Perform inference
    predictions: List[float] = []
    targets: List[float] = []
    pred_levels: List[str] = []
    true_levels: List[str] = []
    embedding_norms: List[float] = []

    for rec in test_records:
        out = model.predict_distress(rec)

        # Validate clinical boundaries on every record
        for k in out.keys():
            enforce_distress_boundary(k)

        p_score = out["distress_score"]
        p_lvl = out["distress_level"]
        emb = out["distress_embedding"]
        norm = math.sqrt(sum(x * x for x in emb))

        t_score = rec.synthetic_distress_score if rec.synthetic_distress_score is not None else 0.5
        t_lvl = model.map_score_to_level(t_score)

        predictions.append(p_score)
        targets.append(t_score)
        pred_levels.append(p_lvl)
        true_levels.append(t_lvl)
        embedding_norms.append(norm)

    n = len(predictions)

    # 4. Compute Metrics
    # MAE & RMSE
    mae = sum(abs(p - t) for p, t in zip(predictions, targets)) / n if n else 0.0
    rmse = math.sqrt(sum((p - t) ** 2 for p, t in zip(predictions, targets)) / n) if n else 0.0

    # Pearson Correlation (r)
    mean_p = sum(predictions) / n if n else 0.0
    mean_t = sum(targets) / n if n else 0.0
    num = sum((p - mean_p) * (t - mean_t) for p, t in zip(predictions, targets))
    den = math.sqrt(sum((p - mean_p) ** 2 for p in predictions) * sum((t - mean_t) ** 2 for t in targets))
    pearson_r = (num / den) if den > 1e-12 else 0.0

    # Threshold Classification Accuracy & Level Metrics
    correct_matches = sum(1 for p_l, t_l in zip(pred_levels, true_levels) if p_l == t_l)
    threshold_accuracy = (correct_matches / n) if n else 0.0

    from sklearn.metrics import precision_recall_fscore_support
    levels_order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    p_ma, r_ma, f1_ma, _ = precision_recall_fscore_support(
        true_levels, pred_levels, labels=levels_order, average="macro", zero_division=0
    )
    p_wt, r_wt, f1_wt, _ = precision_recall_fscore_support(
        true_levels, pred_levels, labels=levels_order, average="weighted", zero_division=0
    )
    p_per, r_per, f1_per, sup_per = precision_recall_fscore_support(
        true_levels, pred_levels, labels=levels_order, average=None, zero_division=0
    )
    per_level_metrics = {
        lvl: {
            "precision": round(float(p_per[i]), 4),
            "recall": round(float(r_per[i]), 4),
            "f1": round(float(f1_per[i]), 4),
            "support": int(sup_per[i]),
        }
        for i, lvl in enumerate(levels_order)
    }

    # Distress Level Distribution
    level_counts = {lvl: pred_levels.count(lvl) for lvl in levels_order}
    level_pcts = {lvl: round(count / n * 100.0, 1) for lvl, count in level_counts.items()}

    mean_emb_norm = sum(embedding_norms) / n if n else 1.0

    report = {
        "model_type": "dynamic_distress_model",
        "validation_samples": n,
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "pearson_correlation": round(float(pearson_r), 4),
        "threshold_accuracy": round(float(threshold_accuracy), 4),
        "macro_precision": round(float(p_ma), 4),
        "macro_recall": round(float(r_ma), 4),
        "macro_f1": round(float(f1_ma), 4),
        "weighted_f1": round(float(f1_wt), 4),
        "per_level_metrics": per_level_metrics,
        "distress_level_distribution": {
            "counts": level_counts,
            "percentages": level_pcts,
        },
        "mean_distress_embedding_norm": round(float(mean_emb_norm), 4),
        "clinical_boundaries_enforced": True,
        "supervision_notice": LABEL_DISCLAIMER,
        "smoke_test_notice": SMOKE_TEST_DISCLAIMER,
        "synthetic_labels_notice": SYNTHETIC_LABELS_DISCLAIMER,
    }

    print("\n------------------------------------------------------------------------")
    print("                     EVALUATION REPORT")
    print("------------------------------------------------------------------------")
    print(f"Validation Samples:               {n}")
    print(f"Mean Absolute Error (MAE):        {report['mae']:.4f}")
    print(f"Root Mean Squared Error (RMSE):   {report['rmse']:.4f}")
    print(f"Pearson Correlation (r):          {report['pearson_correlation']:.4f}")
    print(f"Threshold Accuracy:               {report['threshold_accuracy']:.4f} ({correct_matches}/{n})")
    print(f"Macro F1 (Threshold Levels):      {report['macro_f1']:.4f} (Precision: {report['macro_precision']:.4f}, Recall: {report['macro_recall']:.4f})")
    print(f"Weighted F1:                      {report['weighted_f1']:.4f}")
    print(f"Distress Level Distribution:      {level_counts}")
    print(f"Distress Level Percentages:       {level_pcts}")
    print("\n--- Per-Level Metrics ---")
    for lvl in levels_order:
        plm = per_level_metrics[lvl]
        print(f"  {lvl:<9} | Precision: {plm['precision']:.4f} | Recall: {plm['recall']:.4f} | F1: {plm['f1']:.4f} | Support: {plm['support']}")
    print(f"\nMean Distress Embedding Norm:     {report['mean_distress_embedding_norm']:.4f}")
    print(f"Clinical Boundaries Enforced:     {report['clinical_boundaries_enforced']}")
    print("-" * 72)
    print("                     SMOKE-TEST EVALUATION NOTICE")
    print("-" * 72)
    print(f"* {SMOKE_TEST_DISCLAIMER}")
    print(f"* {SYNTHETIC_LABELS_DISCLAIMER}")
    print("========================================================================")

    if output_file:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved evaluation metrics to {output_file}")

    return report


def main() -> None:
    args = parse_args()
    evaluate_distress(
        model_dir=args.model_dir,
        output_file=args.output_file,
        seed=args.seed,
        sample_count=args.sample_count,
    )


if __name__ == "__main__":
    main()
