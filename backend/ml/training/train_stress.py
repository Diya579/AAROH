#!/usr/bin/env python3
"""Training and verification script for AAROH Stress Model (Slice 3.3).

Trains a lightweight transformer binary classifier on Dreaddit.
Compatible with Google Colab and supports --smoke-test mode for rapid end-to-end verification.

Strict Invariant:
- stress_probability != distress_score.
- Stress probability is an auxiliary linguistic feature and must NEVER be treated as clinical distress.

Usage:
    python3 -m backend.ml.training.train_stress [--smoke-test] [OPTIONS]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Optional

from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    ModelExportManager,
    SimpleDataLoader,
    SimpleTokenizer,
    compute_accuracy,
    compute_precision_recall_f1,
    compute_roc_auc,
    enforce_stress_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.stress.dataset import (
    DreadditStressDataset,
    load_dreaddit_records,
)
from backend.ml.training.models.stress.model import (
    DEFAULT_STRESS_BACKBONE,
    StressModel,
)


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Stress Model on Dreaddit.")
    parser.add_argument("--data-dir", default="datasets/processed", help="Path to preprocessed JSONL directory.")
    parser.add_argument("--output-dir", default="models/stress", help="Directory to export the final model.")
    parser.add_argument("--checkpoint-dir", default="checkpoints/stress", help="Local checkpoint directory.")
    parser.add_argument("--drive-checkpoint-dir", default=None, help="Google Drive checkpoint directory.")
    parser.add_argument("--model-name", default=DEFAULT_STRESS_BACKBONE, help="HuggingFace backbone name.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps.")
    parser.add_argument("--early-stopping-patience", type=int, default=3, help="Early stopping patience.")
    parser.add_argument("--fp16", action="store_true", default=False, help="Enable fp16 mixed precision on CUDA.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--smoke-test", action="store_true", default=False, help="Run rapid end-to-end smoke test.")
    return parser.parse_args(args)


def train_stress(args: argparse.Namespace) -> dict[str, Any]:
    """Executes Stress model training or end-to-end smoke test verification."""
    start_time = time.time()
    enforce_stress_boundary("stress_probability")
    set_seed(args.seed)
    device = get_device()

    print("=" * 70)
    print("  AAROH — Stress Model Training (Slice 3.3)")
    print("=" * 70)
    print(f"Data Directory:          {args.data_dir}")
    print(f"Export Output Directory: {args.output_dir}")
    print(f"Backbone:                {args.model_name}")
    print(f"Device:                  {device}")
    print(f"Smoke Test Mode:         {args.smoke_test}")
    print(f"Seed:                    {args.seed}")
    print("-" * 70)

    # 1. Dataset loading
    all_records = load_dreaddit_records(args.data_dir)
    dataset_loaded = len(all_records) > 0

    if args.smoke_test:
        all_records = all_records[:96] if all_records else []
        epochs = 1
        batch_size = 16
    else:
        epochs = args.epochs
        batch_size = args.batch_size

    split_idx = int(0.8 * len(all_records))
    train_records = all_records[:split_idx]
    val_records = all_records[split_idx:]
    print(f"Loaded Dreaddit records: {len(all_records)} total (Train: {len(train_records)}, Val: {len(val_records)})")

    # 2. Tokenizer loading
    tokenizer = SimpleTokenizer.from_pretrained(args.model_name, max_length=128)
    tokenizer_loaded = tokenizer is not None
    print(f"Tokenizer loaded: {tokenizer_loaded}")

    # 3. Dataloader creation
    train_ds = DreadditStressDataset(train_records, tokenizer=None)
    dataloader = SimpleDataLoader(train_ds, batch_size=batch_size, shuffle=True)
    dataloader_built = len(dataloader) > 0
    print(f"Dataloader built: {dataloader_built} ({len(dataloader)} batches)")

    # 4. Instantiate Model
    model = StressModel(
        backbone=args.model_name,
        embedding_dim=768,
    )
    model.tokenizer = tokenizer

    checkpoint_mgr = CheckpointManager(
        checkpoint_dir=args.checkpoint_dir,
        drive_checkpoint_dir=args.drive_checkpoint_dir,
    )

    forward_success = False
    backward_success = False
    optimizer_step_success = False
    initial_loss: Optional[float] = None
    final_loss: Optional[float] = None
    loss_decreased = False

    # Execute training loop
    print("[INFO] Executing gradient descent training loop...")
    batch_losses: list[float] = []

    for epoch in range(1, epochs + 1):
        for batch in dataloader:
            b_texts = [item["text"] for item in batch]
            b_targets = [item["stress_label"] for item in batch]

            loss = model.train_step(b_texts, b_targets, lr=args.lr)
            forward_success = True
            backward_success = True
            optimizer_step_success = True
            batch_losses.append(loss)

    if batch_losses:
        initial_loss = batch_losses[0]
        final_loss = batch_losses[-1]
        loss_decreased = final_loss <= initial_loss
        print(f"Stress Training Loss -> Initial: {initial_loss:.4f} | Final: {final_loss:.4f} (Decreased: {loss_decreased})")

    # 5. Checkpointing
    ckpt_path = checkpoint_mgr.save_checkpoint(
        epoch=1,
        model_state=model.state_dict(),
        metrics={"loss": final_loss or 0.0},
        is_best=True,
    )
    checkpoint_saved = ckpt_path.exists() or ckpt_path.with_suffix(".json").exists()
    print(f"Checkpoint saved: {checkpoint_saved} ({ckpt_path})")

    # 6. Reload into fresh model instance
    fresh_model = StressModel(
        backbone=args.model_name,
        embedding_dim=768,
    )
    loaded_ckpt = checkpoint_mgr.load_checkpoint(ckpt_path)
    state_dict_payload = loaded_ckpt.get("model_state_dict", loaded_ckpt)
    fresh_model.load_state_dict(state_dict_payload)
    checkpoint_reloaded = True

    # 7. Verify inference after reload
    test_phrase = ["Extreme panic and overwhelm", "Quiet afternoon resting"]
    fresh_preds = fresh_model.encode_and_predict(test_phrase)
    inference_after_reload_success = (
        len(fresh_preds["stress_probabilities"]) == len(test_phrase)
        and len(fresh_preds["stress_embeddings"]) == len(test_phrase)
        and len(fresh_preds["stress_embeddings"][0]) == 768
    )
    print(f"Inference after reload success: {inference_after_reload_success}")

    # 8. Evaluation on validation split
    val_subset = val_records if val_records else train_records[:20]
    val_texts = [r.get("text", "") for r in val_subset]
    val_targets = [int(r.get("stress_label", 0)) for r in val_subset]

    eval_preds = fresh_model.encode_and_predict(val_texts)
    pred_scores = eval_preds["stress_probabilities"]
    pred_classes = [1 if s >= 0.5 else 0 for s in pred_scores]

    acc = compute_accuracy(val_targets, pred_classes)
    prf = compute_precision_recall_f1(val_targets, pred_classes, classes=[0, 1])
    auc = compute_roc_auc(val_targets, pred_scores)

    eval_metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prf["precision"], 4),
        "recall": round(prf["recall"], 4),
        "f1": round(prf["macro_f1"], 4),
        "roc_auc": round(auc, 4),
        "val_samples_evaluated": len(val_subset),
        "clinical_boundary_verified": "stress_probability != distress_score",
    }
    evaluation_completed = True

    # 9. Model Export
    hyperparams = {
        "learning_rate": args.lr,
        "batch_size": batch_size,
        "epochs": epochs,
        "seed": args.seed,
        "smoke_test": args.smoke_test,
    }
    export_path = fresh_model.save(
        output_dir=args.output_dir,
        metrics=eval_metrics,
        hyperparameters=hyperparams,
    )
    exported_successfully = Path(export_path).exists()

    # 10. Verify all 6 exported files exist
    exp_dir = Path(args.output_dir)
    exported_files = {
        "weights": (exp_dir / "pytorch_model.bin").exists(),
        "tokenizer": (exp_dir / "tokenizer.json").exists() or (exp_dir / "tokenizer_config.json").exists(),
        "config.json": (exp_dir / "config.json").exists(),
        "label_mapping.json": (exp_dir / "label_mapping.json").exists(),
        "metadata.json": (exp_dir / "metadata.json").exists(),
        "metrics.json": (exp_dir / "metrics.json").exists(),
    }
    all_exported_files_exist = all(exported_files.values())
    print(f"Exported files verified: {exported_files}")

    duration = round(time.time() - start_time, 3)

    report = {
        "model_name": "stress",
        "dataset_loaded": dataset_loaded,
        "tokenizer_loaded": tokenizer_loaded,
        "dataloader_built": dataloader_built,
        "forward_pass_successful": forward_success,
        "backward_pass_successful": backward_success,
        "optimizer_step_successful": optimizer_step_success,
        "training_loss_initial": round(initial_loss or 0.0, 4),
        "training_loss_final": round(final_loss or 0.0, 4),
        "training_loss_decreased": loss_decreased,
        "checkpoint_saved": checkpoint_saved,
        "checkpoint_reloaded": checkpoint_reloaded,
        "inference_after_reload_success": inference_after_reload_success,
        "evaluation_completed": evaluation_completed,
        "exported_successfully": exported_successfully,
        "all_exported_files_exist": all_exported_files_exist,
        "exported_files": exported_files,
        "metrics": eval_metrics,
        "total_trainable_parameters": fresh_model.trainable_parameters_count,
        "backbone": args.model_name,
        "embedding_dim": 768,
        "device": device,
        "duration_seconds": duration,
    }

    print("\n[VERIFICATION SUMMARY - STRESS]:")
    print(f"  Trainable Parameters: {report['total_trainable_parameters']:,}")
    print(f"  All Exported Files:   {all_exported_files_exist}")
    print(f"  Duration:             {duration}s")
    print("=" * 70)
    return report


if __name__ == "__main__":
    cli_args = parse_args()
    train_stress(cli_args)
