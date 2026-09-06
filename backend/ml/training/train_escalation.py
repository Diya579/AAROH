"""Training script for Interpretable Logistic Regression Escalation Assessment Model (Slice 3.8 Revision).

Supports:
- Local verification / Smoke-test execution with synthetic demonstration records.
- Configurable target horizon days and risk thresholds via EscalationConfig.
- Strict case-level splitting with zero data leakage.
- Optimization of binary cross-entropy loss.
- Checkpoint save, reload, and verification.
- Export of standard production artifacts.

Strict Invariants:
- Supervised ONLY using SYNTHETIC DEMONSTRATION LABELS (NOT CLINICAL GROUND TRUTH).
- Produces an operational assessment signal only, NOT a clinical diagnosis.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure workspace root is in sys.path
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from backend.ml.training.models.common import (
    enforce_escalation_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.escalation.dataset import (
    DEFAULT_TARGET_HORIZON_DAYS,
    DEFAULT_THRESHOLD_LOW_MODERATE,
    DEFAULT_THRESHOLD_MODERATE_HIGH,
    LABEL_DISCLAIMER,
    SMOKE_TEST_DISCLAIMER,
    EscalationConfig,
    EscalationInputRecord,
    build_synthetic_escalation_records,
    split_escalation_records_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.escalation.model import (
    DEFAULT_MODEL_VERSION,
    EscalationAssessmentModel,
)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Logistic Regression Escalation Assessment Model (Slice 3.8)")
    parser.add_argument("--output-dir", type=str, default="models/escalation", help="Export destination")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/escalation", help="Local checkpoint directory")
    parser.add_argument("--drive-checkpoint-dir", type=str, default=None, help="Google Drive checkpoint directory")
    parser.add_argument("--target-horizon-days", type=int, default=DEFAULT_TARGET_HORIZON_DAYS, help="Target horizon in days")
    parser.add_argument("--threshold-low-moderate", type=float, default=DEFAULT_THRESHOLD_LOW_MODERATE, help="Low/moderate boundary")
    parser.add_argument("--threshold-moderate-high", type=float, default=DEFAULT_THRESHOLD_MODERATE_HIGH, help="Moderate/high boundary")
    parser.add_argument("--epochs", type=int, default=150, help="Training iterations")
    parser.add_argument("--lr", type=float, default=0.08, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--smoke-test", action="store_true", help="Run fast smoke test")
    return parser.parse_args(args)


def train_escalation_model(args: argparse.Namespace) -> Dict[str, Any]:
    """Runs training and verification pipeline for Escalation Assessment Model."""
    start_time = time.time()
    set_seed(args.seed)

    print("=" * 74)
    print("  AAROH — Escalation Assessment Model Training (Slice 3.8 Revision)")
    print("=" * 74)
    print(f"Model:                   Interpretable Calibrated Logistic Regression")
    print(f"Export Destination:      {args.output_dir}")
    print(f"Target Horizon:          {args.target_horizon_days} days")
    print(f"Risk Thresholds:         Low < {args.threshold_low_moderate} <= Mod < {args.threshold_moderate_high} <= High")
    print(f"Supervision Notice:      {LABEL_DISCLAIMER}")
    print(f"Smoke Test Mode:         {args.smoke_test}")
    print("-" * 74)

    # 1. Prepare Synthetic Records
    case_count = 24 if args.smoke_test else 80
    records = build_synthetic_escalation_records(case_count=case_count, seed=args.seed)
    print(f"Generated {len(records)} synthetic demonstration records")

    # 2. Case-Level Splitting (Strict Leakage Prevention)
    train_recs, val_recs = split_escalation_records_by_case(records, val_ratio=0.25, seed=args.seed)
    train_cases = set(r.case_id for r in train_recs)
    val_cases = set(r.case_id for r in val_recs)
    print(f"Programmatic Case Split:")
    print(f"  Train Cases ({len(train_cases)}): {sorted(list(train_cases))}")
    print(f"  Val Cases   ({len(val_cases)}):   {sorted(list(val_cases))}")
    validate_no_case_leakage(train_recs, val_recs)
    print("  Case Leakage Check: PASSED (Zero Overlap)")

    # 3. Model Configuration & Instantiation
    config = EscalationConfig(
        target_horizon_days=args.target_horizon_days,
        threshold_low_moderate=args.threshold_low_moderate,
        threshold_moderate_high=args.threshold_moderate_high,
    )
    model = EscalationAssessmentModel(config=config, seed=args.seed)

    # 4. Training (Gradient Descent on Binary Cross-Entropy)
    epochs = 20 if args.smoke_test else args.epochs
    fit_metrics = model.fit(train_recs, epochs=epochs, lr=args.lr)
    init_loss = fit_metrics["initial_loss"]
    final_loss = fit_metrics["final_loss"]
    loss_decreased = final_loss <= init_loss

    print(f"Optimization Completed: Loss {init_loss} -> {final_loss} (Decreased: {loss_decreased})")

    # 5. Checkpointing
    chk_dir = Path(args.checkpoint_dir)
    chk_dir.mkdir(parents=True, exist_ok=True)
    chk_file = chk_dir / "checkpoint_escalation.pt"
    model.save_checkpoint(chk_file, metrics={"initial_loss": init_loss, "final_loss": final_loss})
    chk_saved = chk_file.exists()

    if args.drive_checkpoint_dir:
        drive_path = Path(args.drive_checkpoint_dir)
        drive_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(chk_file, drive_path / chk_file.name)
        print(f"Synced checkpoint to Google Drive: {drive_path / chk_file.name}")

    # 6. Reload & Verification of predict_escalation
    reloaded_model = EscalationAssessmentModel(config=config, seed=args.seed + 99)
    reloaded_model.load_checkpoint(chk_file)

    sample_rec = val_recs[0]
    sample_inf = reloaded_model.predict_escalation(sample_rec)
    for k in sample_inf.keys():
        enforce_escalation_boundary(k)

    inf_after_reload = (
        "case_id" in sample_inf
        and "prediction_date" in sample_inf
        and "escalation_probability" in sample_inf
        and "target_horizon_days" in sample_inf
        and "confidence" in sample_inf
        and "risk_level" in sample_inf
        and "explanation" in sample_inf
        and "model_version" in sample_inf
        and sample_inf["target_horizon_days"] == args.target_horizon_days
        and sample_inf["risk_level"] in ("LOW", "MODERATE", "HIGH")
    )

    reloaded_model.seed = args.seed
    # 7. Export Production Artifacts
    export_paths = reloaded_model.export(
        output_dir=args.output_dir,
        metrics={
            "initial_loss": init_loss,
            "final_loss": final_loss,
            "loss_decreased": loss_decreased,
            "target_horizon_days": args.target_horizon_days,
            "smoke_test": args.smoke_test,
        },
    )
    exported_all = all(os.path.exists(p) for p in export_paths.values())

    duration = round(time.time() - start_time, 2)
    return {
        "escalation": {
            "dataset_loaded": len(records) > 0,
            "case_split_respected": len(train_cases.intersection(val_cases)) == 0,
            "forward_pass_successful": True,
            "training_loss_initial": init_loss,
            "training_loss_final": final_loss,
            "training_loss_decreased": loss_decreased,
            "checkpoint_saved": chk_saved,
            "checkpoint_reloaded": True,
            "inference_after_reload_success": inf_after_reload,
            "exported_successfully": exported_all,
            "all_exported_files_exist": exported_all,
            "export_paths": export_paths,
            "duration_seconds": duration,
            "model_type": "logistic_regression",
            "target_horizon_days": args.target_horizon_days,
            "num_features": len(model.feature_names),
            "sample_inference": sample_inf,
        }
    }


def main() -> None:
    args = parse_args()
    summary = train_escalation_model(args)
    data = summary["escalation"]
    print("\n" + "=" * 74)
    print("           ESCALATION ASSESSMENT TRAINING SUMMARY")
    print("=" * 74)
    print(f"  Model Type:                       {data['model_type']}")
    print(f"  Target Horizon Days:              {data['target_horizon_days']}")
    print(f"  Features Count:                   {data['num_features']}")
    print(f"  Training Time:                    {data['duration_seconds']}s")
    print(f"  Loss (Initial -> Final):          {data['training_loss_initial']} -> {data['training_loss_final']}")
    print(f"  All Exported Files Exist:         {data['all_exported_files_exist']}")
    print("=" * 74 + "\n")


if __name__ == "__main__":
    main()
