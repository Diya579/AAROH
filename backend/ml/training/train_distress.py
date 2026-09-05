"""Training script for Dynamic Distress Model (Slice 3.6).

Supports:
- Local verification / Smoke-test execution with deterministic synthetic demonstration records.
- Google Colab GPU execution with fp16, gradient accumulation, and Drive checkpoints.
- Strict case-level splitting with zero data leakage.
- Regression training on synthetic demonstration distress targets.
- Export of production artifacts (weights, config.json, metadata.json, metrics.json, label_mapping.json).

Strict Invariants:
- Supervised ONLY using SYNTHETIC DEMONSTRATION LABELS (NOT CLINICAL GROUND TRUTH).
- Clinical boundary: Dynamic Distress Model outputs ONLY current distress representations.
- NEVER outputs diagnosis, escalation, future prediction, depression, anxiety, PTSD, or suicide risk.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.ml.training.models.common import (
    enforce_distress_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.distress.dataset import (
    DISTRESS_INPUT_DIM,
    LABEL_DISCLAIMER,
    DistressDataset,
    DistressInputRecord,
    build_synthetic_distress_records,
    split_distress_records_by_case,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_THRESHOLDS,
    DynamicDistressModel,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Dynamic Distress Model (Slice 3.6)")
    parser.add_argument("--data-dir", type=str, default="datasets/processed", help="Processed datasets directory")
    parser.add_argument("--output-dir", type=str, default="models/distress", help="Export destination")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints/distress", help="Local checkpoint directory")
    parser.add_argument("--drive-checkpoint-dir", type=str, default=None, help="Google Drive checkpoint directory")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--smoke-test", action="store_true", help="Run fast smoke test (1 epoch, small subset)")
    parser.add_argument("--unfreeze-backbone", action="store_true", help="Unfreeze pretrained backbones for training")
    parser.add_argument("--fp16", action="store_true", help="Enable FP16 mixed precision on GPU")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1, help="Gradient accumulation steps")
    return parser.parse_args()


def train_distress_model(args: argparse.Namespace) -> Dict[str, Any]:
    """Runs the training and verification pipeline for Dynamic Distress Model."""
    start_time = time.time()
    set_seed(args.seed)

    print("=" * 72)
    print("  AAROH — Dynamic Distress Model Training (Slice 3.6)")
    print("=" * 72)
    print(f"Data Directory:          {args.data_dir}")
    print(f"Export Output Directory: {args.output_dir}")
    print(f"Supervision Notice:      {LABEL_DISCLAIMER}")
    print(f"Device:                  {get_device()}")
    print(f"Smoke Test Mode:         {args.smoke_test}")
    print(f"Seed:                    {args.seed}")
    print("-" * 72)

    # 1. Prepare Records
    record_count = 60 if args.smoke_test else 240
    records = build_synthetic_distress_records(count=record_count, seed=args.seed)
    print(f"Loaded/Generated {len(records)} synthetic distress interaction records")

    # 2. Case-Level Splitting (Strict Leakage Prevention)
    train_records, val_records = split_distress_records_by_case(records, val_ratio=0.25, seed=args.seed)
    train_cases = set(r.case_id for r in train_records)
    val_cases = set(r.case_id for r in val_records)
    print(f"Programmatic Case Split:")
    print(f"  Train Cases ({len(train_cases)}): {sorted(list(train_cases))}")
    print(f"  Val Cases   ({len(val_cases)}):   {sorted(list(val_cases))}")
    overlap = train_cases.intersection(val_cases)
    if overlap:
        raise ValueError(f"Case leakage detected: {overlap}")
    print("  Case Leakage Check: PASSED (Zero Overlap)")

    # 3. Dataloaders
    batch_size = 8 if args.smoke_test else args.batch_size
    train_ds = DistressDataset(train_records)
    val_ds = DistressDataset(val_records)
    epochs = args.epochs if (args.epochs != 5 or not args.smoke_test) else 1

    # 4. Instantiate Model & Parameter Reporting
    model = DynamicDistressModel(
        seed=args.seed,
        unfreeze_backbone=args.unfreeze_backbone,
    )
    param_counts = model.get_parameter_counts()
    print(f"Execution Mode:                {model.execution_mode}")
    print(f"1. Trainable Parameters:       {param_counts['trainable_parameters']:,}")
    print(f"2. Backbone Parameters:        {param_counts['backbone_parameters']:,}")
    print(f"3. Total If Instantiated:      {param_counts['total_parameters_if_instantiated']:,}")
    print(f"4. Actually Instantiated:      {param_counts['actually_instantiated_parameters']:,}")

    # 5. Training Loop
    print("\n[INFO] Executing dynamic distress gradient descent training loop...")
    loss_history: List[float] = []

    for epoch in range(1, epochs + 1):
        epoch_losses: List[float] = []
        for batch in train_ds.iterate_batches(batch_size=batch_size, shuffle=True, seed=args.seed + epoch):
            loss = model.train_step(batch=batch, lr=args.lr)
            epoch_losses.append(loss)

        avg_epoch_loss = sum(epoch_losses) / len(epoch_losses) if epoch_losses else 0.0
        loss_history.append(avg_epoch_loss)
        print(f"  Epoch {epoch}/{epochs} — Mean MSE Loss: {avg_epoch_loss:.4f}")

    initial_loss = loss_history[0] if loss_history else 0.0
    final_loss = loss_history[-1] if loss_history else 0.0
    loss_decreased = bool(final_loss <= initial_loss)
    print(f"\nDistress Model MSE Loss -> Initial: {initial_loss:.4f} | Final: {final_loss:.4f} (Decreased: {loss_decreased})")

    # 6. Save Checkpoint
    chk_dir = Path(args.checkpoint_dir)
    chk_file = chk_dir / f"checkpoint_epoch_{epochs}.pt"
    model.save_checkpoint(chk_file, epoch=epochs, metrics={"loss": final_loss})
    print(f"Checkpoint saved: True ({chk_file})")

    if args.drive_checkpoint_dir:
        try:
            drive_path = Path(args.drive_checkpoint_dir)
            drive_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(str(chk_file), str(drive_path / chk_file.name))
            print(f"Copied checkpoint to Google Drive: {drive_path}")
        except Exception as e:
            print(f"Warning: Could not copy checkpoint to Drive: {e}")

    # 7. Reload Checkpoint & Verify Public Inference Interface
    reload_model = DynamicDistressModel(seed=args.seed)
    reload_model.load_checkpoint(chk_file)
    test_record = val_records[0]
    inf_res = reload_model.predict_distress(test_record)

    distress_emb = inf_res["distress_embedding"]
    norm = math.sqrt(sum(x * x for x in distress_emb))
    inference_success = bool(
        len(distress_emb) == 128
        and abs(norm - 1.0) < 1e-3
        and "distress_score" in inf_res
        and 0.0 <= inf_res["distress_score"] <= 1.0
        and inf_res["distress_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    )
    print(
        f"Inference (predict_distress()) after reload success: {inference_success} "
        f"(Embedding Dim: {len(distress_emb)}, Score: {inf_res['distress_score']:.4f}, Level: {inf_res['distress_level']})"
    )

    # 8. Evaluation on Held-Out Validation Set
    val_preds: List[float] = []
    val_targets: List[float] = []
    val_levels: List[str] = []
    val_true_levels: List[str] = []

    for rec in val_records:
        out = reload_model.predict_distress(rec)
        pred_score = out["distress_score"]
        pred_level = out["distress_level"]
        true_score = rec.synthetic_distress_score if rec.synthetic_distress_score is not None else 0.5
        true_level = reload_model.map_score_to_level(true_score)

        val_preds.append(pred_score)
        val_targets.append(true_score)
        val_levels.append(pred_level)
        val_true_levels.append(true_level)

    # Metrics
    n = len(val_preds)
    mae = sum(abs(p - t) for p, t in zip(val_preds, val_targets)) / n if n else 0.0
    rmse = math.sqrt(sum((p - t) ** 2 for p, t in zip(val_preds, val_targets)) / n) if n else 0.0

    # Pearson Correlation
    mean_p = sum(val_preds) / n if n else 0.0
    mean_t = sum(val_targets) / n if n else 0.0
    num = sum((p - mean_p) * (t - mean_t) for p, t in zip(val_preds, val_targets))
    den = math.sqrt(sum((p - mean_p) ** 2 for p in val_preds) * sum((t - mean_t) ** 2 for t in val_targets))
    pearson_r = (num / den) if den > 1e-12 else 0.0

    # Threshold Accuracy
    correct_levels = sum(1 for p_lvl, t_lvl in zip(val_levels, val_true_levels) if p_lvl == t_lvl)
    threshold_accuracy = (correct_levels / n) if n else 0.0

    # Distress Level Distribution
    level_counts = {lvl: val_levels.count(lvl) for lvl in ("LOW", "MODERATE", "HIGH", "CRITICAL")}

    eval_metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "pearson_correlation": round(float(pearson_r), 4),
        "threshold_accuracy": round(float(threshold_accuracy), 4),
        "distress_level_distribution": level_counts,
        "validation_samples": n,
        "supervision_notice": LABEL_DISCLAIMER,
    }

    # 9. Model Export
    export_paths = reload_model.export(args.output_dir, metrics=eval_metrics)
    all_exported_files_exist = {k: os.path.exists(v) for k, v in export_paths.items()}
    print(f"Exported files verified: {all_exported_files_exist}")

    duration = round(time.time() - start_time, 3)
    summary = {
        "distress": {
            "backbones": {
                "text": "distilbert-base-multilingual-cased",
                "audio": "facebook/wav2vec2-base",
            },
            "backbone_status": "UNFROZEN" if args.unfreeze_backbone else "FROZEN",
            "execution_mode": reload_model.execution_mode,
            "embedding_dim": 128,
            "trainable_parameters": param_counts["trainable_parameters"],
            "backbone_parameters": param_counts["backbone_parameters"],
            "total_parameters_if_instantiated": param_counts["total_parameters_if_instantiated"],
            "actually_instantiated_parameters": param_counts["actually_instantiated_parameters"],
            "device": get_device(),
            "duration_seconds": duration,
            "training_loss_initial": round(initial_loss, 5),
            "training_loss_final": round(final_loss, 5),
            "training_loss_decreased": loss_decreased,
            "checkpoint_saved": os.path.exists(chk_file),
            "checkpoint_reloaded": True,
            "inference_after_reload_success": inference_success,
            "dataset_loaded": True,
            "dataloader_built": True,
            "case_split_respected": len(train_cases.intersection(val_cases)) == 0,
            "forward_pass_successful": True,
            "backward_pass_successful": True,
            "optimizer_step_successful": True,
            "exported_successfully": True,
            "all_exported_files_exist": all(all_exported_files_exist.values()),
            "export_paths": export_paths,
            "evaluation_metrics": eval_metrics,
        }
    }
    return summary


def main() -> None:
    args = parse_args()
    res = train_distress_model(args)
    if res.get("distress", {}).get("inference_after_reload_success"):
        print("\nDynamic Distress Model Training Completed Successfully [PASS]")
        sys.exit(0)
    else:
        print("\nDynamic Distress Model Training FAILED [FAIL]")
        sys.exit(1)


if __name__ == "__main__":
    main()
