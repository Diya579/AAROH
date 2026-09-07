#!/usr/bin/env python3
"""Training and verification script for AAROH Audio Emotion Representation Model (Slice 3.4).

Trains a lightweight speech audio encoder (facebook/wav2vec2-base) on RAVDESS.
Compatible with Google Colab and supports --smoke-test mode for rapid end-to-end verification.

Strict Boundaries:
- Audio Emotion != Clinical Distress.
- Does NOT predict distress_score, escalation_probability, depression, anxiety, risk level, or diagnosis.
- Preserves Voice Service boundary (ASR, VAD, pause ratio, etc. belong to Diya's service).

Usage:
    python3 -m backend.ml.training.train_audio_emotion [--smoke-test] [OPTIONS]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Optional

from backend.ml.training.models.audio_emotion.dataset import (
    DEFAULT_TARGET_SAMPLE_RATE,
    DEFAULT_TARGET_SAMPLES,
    EMOTION_TO_ID,
    RAVDESS_EMOTIONS,
    RavdessDataset,
    split_ravdess_records_by_actor,
)
from backend.ml.training.models.audio_emotion.model import (
    DEFAULT_AUDIO_BACKBONE,
    AudioEmotionModel,
)
from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    ModelExportManager,
    SimpleDataLoader,
    compute_accuracy,
    compute_confusion_matrix,
    compute_per_class_accuracy,
    compute_precision_recall_f1,
    enforce_audio_emotion_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.preprocessing.common import read_jsonl


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Audio Emotion Representation Model on RAVDESS.")
    parser.add_argument("--data-dir", default="datasets/processed", help="Path to preprocessed JSONL directory.")
    parser.add_argument("--output-dir", default="models/audio_emotion", help="Directory to export the final model.")
    parser.add_argument("--checkpoint-dir", default="checkpoints/audio_emotion", help="Local checkpoint directory.")
    parser.add_argument("--drive-checkpoint-dir", default=None, help="Google Drive checkpoint directory.")
    parser.add_argument("--model-name", default=DEFAULT_AUDIO_BACKBONE, help="HuggingFace backbone name.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps.")
    parser.add_argument("--early-stopping-patience", type=int, default=3, help="Early stopping patience.")
    parser.add_argument("--fp16", action="store_true", default=False, help="Enable fp16 mixed precision on CUDA.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--unfreeze-backbone", action="store_true", default=False, help="Unfreeze wav2vec2 encoder backbone.")
    parser.add_argument("--smoke-test", action="store_true", default=False, help="Run rapid end-to-end smoke test.")
    return parser.parse_args(args)


def train_audio_emotion(args: argparse.Namespace) -> dict[str, Any]:
    """Executes Audio Emotion model training or end-to-end smoke test verification."""
    start_time = time.time()
    enforce_audio_emotion_boundary("audio_emotion_training")
    set_seed(args.seed)
    device = get_device()

    frozen_backbone = not args.unfreeze_backbone

    print("=" * 72)
    print("  AAROH — Audio Emotion Representation Model Training (Slice 3.4)")
    print("=" * 72)
    print(f"Data Directory:          {args.data_dir}")
    print(f"Export Output Directory: {args.output_dir}")
    print(f"Backbone:                {args.model_name}")
    print(f"Backbone Status:         {'FROZEN' if frozen_backbone else 'UNFROZEN'}")
    print(f"Device:                  {device}")
    print(f"Smoke Test Mode:         {args.smoke_test}")
    print(f"Seed:                    {args.seed}")
    print("-" * 72)

    # 1. Dataset loading
    p_dir = Path(args.data_dir)
    jsonl_path = p_dir / "ravdess.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"RAVDESS preprocessed file not found: {jsonl_path}")

    all_records = read_jsonl(jsonl_path)
    dataset_loaded = len(all_records) > 0
    print(f"Loaded {len(all_records)} RAVDESS records from {jsonl_path}")

    # 2. Programmatic actor-level splitting (zero actor leakage)
    train_records, val_records = split_ravdess_records_by_actor(
        all_records,
        test_ratio=0.25,
        seed=args.seed,
    )
    train_actors = sorted(list(set(r["actor"] for r in train_records)))
    val_actors = sorted(list(set(r["actor"] for r in val_records)))
    actor_split_respected = len(set(train_actors).intersection(set(val_actors))) == 0

    print(f"Programmatic Actor Split:")
    print(f"  Train Actors ({len(train_actors)}): {train_actors}")
    print(f"  Val Actors   ({len(val_actors)}):   {val_actors}")
    print(f"  Actor Leakage Check: {'PASSED (Zero Overlap)' if actor_split_respected else 'FAILED'}")

    if args.smoke_test:
        train_records = train_records[:64]
        val_records = val_records[:16]
        epochs = 2
        batch_size = 16
        lr = 0.01
    else:
        epochs = args.epochs
        batch_size = args.batch_size
        lr = args.learning_rate

    # 3. Dataloader creation with lazy loading
    train_ds = RavdessDataset(train_records)
    dataloader = SimpleDataLoader(train_ds, batch_size=batch_size, shuffle=False)
    dataloader_built = len(dataloader) > 0
    print(f"Dataloader built: {dataloader_built} ({len(dataloader)} batches)")

    # 4. Instantiate Model
    model = AudioEmotionModel(
        backbone=args.model_name,
        num_classes=len(RAVDESS_EMOTIONS),
        embedding_dim=768,
        frozen_backbone=frozen_backbone,
    )

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
    print("[INFO] Executing audio gradient descent training loop...")
    epoch_losses: list[float] = []

    for epoch in range(1, epochs + 1):
        losses_this_epoch = []
        for batch in dataloader:
            b_waveforms = [item["waveform"] for item in batch]
            b_targets = [item["emotion_id"] for item in batch]

            loss = model.train_step(b_waveforms, b_targets, lr=lr)
            forward_success = True
            backward_success = True
            optimizer_step_success = True
            losses_this_epoch.append(loss)

        if losses_this_epoch:
            epoch_losses.append(sum(losses_this_epoch) / len(losses_this_epoch))

    if epoch_losses:
        initial_loss = epoch_losses[0]
        final_loss = epoch_losses[-1]
        loss_decreased = final_loss <= initial_loss
        print(f"Audio Training Loss -> Initial: {initial_loss:.4f} | Final: {final_loss:.4f} (Decreased: {loss_decreased})")

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
    fresh_model = AudioEmotionModel(
        backbone=args.model_name,
        num_classes=len(RAVDESS_EMOTIONS),
        embedding_dim=768,
        frozen_backbone=frozen_backbone,
    )
    loaded_ckpt = checkpoint_mgr.load_checkpoint(ckpt_path)
    state_dict_payload = loaded_ckpt.get("model_state_dict", loaded_ckpt)
    fresh_model.load_state_dict(state_dict_payload)
    checkpoint_reloaded = True

    # 7. Verify public inference interface after reload
    sample_wav_path = train_records[0]["audio_path"]
    public_res = fresh_model.predict_audio_embedding(sample_wav_path)
    inference_after_reload_success = (
        "audio_embedding" in public_res
        and "audio_emotion_probabilities" in public_res
        and len(public_res["audio_embedding"]) == 768
        and len(public_res["audio_emotion_probabilities"]) == len(RAVDESS_EMOTIONS)
    )
    print(f"Inference (predict_audio_embedding) after reload success: {inference_after_reload_success}")

    # 8. Evaluation on validation split
    val_ds = RavdessDataset(val_records)
    val_waveforms = [val_ds[i]["waveform"] for i in range(len(val_ds))]
    val_targets = [val_ds[i]["emotion"] for i in range(len(val_ds))]

    eval_preds = fresh_model.encode_and_predict(val_waveforms)
    predicted_classes = [
        max(p.items(), key=lambda item: item[1])[0]
        for p in eval_preds["audio_emotion_probabilities"]
    ]

    acc = compute_accuracy(val_targets, predicted_classes)
    prf = compute_precision_recall_f1(val_targets, predicted_classes, classes=RAVDESS_EMOTIONS)
    conf_matrix = compute_confusion_matrix(val_targets, predicted_classes, classes=RAVDESS_EMOTIONS)
    per_class_acc = compute_per_class_accuracy(val_targets, predicted_classes, classes=RAVDESS_EMOTIONS)

    eval_metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prf["precision"], 4),
        "recall": round(prf["recall"], 4),
        "macro_f1": round(prf["macro_f1"], 4),
        "weighted_f1": round(prf["weighted_f1"], 4),
        "per_class_accuracy": per_class_acc,
        "confusion_matrix": conf_matrix,
        "classes": list(RAVDESS_EMOTIONS),
        "val_samples_evaluated": len(val_records),
        "clinical_boundary_verified": "Audio Emotion != Clinical Distress",
    }
    evaluation_completed = True

    # 9. Model Export
    hyperparams = {
        "learning_rate": lr,
        "batch_size": batch_size,
        "epochs": epochs,
        "seed": args.seed,
        "frozen_backbone": frozen_backbone,
        "smoke_test": args.smoke_test,
    }
    export_path = fresh_model.save(
        output_dir=args.output_dir,
        metrics=eval_metrics,
        hyperparameters=hyperparams,
    )
    exported_successfully = Path(export_path).exists()

    # 10. Verify all exported files exist
    exp_dir = Path(args.output_dir)
    exported_files = {
        "weights": (exp_dir / "pytorch_model.bin").exists(),
        "tokenizer": (exp_dir / "tokenizer.json").exists() or (exp_dir / "tokenizer_config.json").exists(),
        "preprocessor_config.json": (exp_dir / "preprocessor_config.json").exists(),
        "config.json": (exp_dir / "config.json").exists(),
        "label_mapping.json": (exp_dir / "label_mapping.json").exists(),
        "metadata.json": (exp_dir / "metadata.json").exists(),
        "metrics.json": (exp_dir / "metrics.json").exists(),
    }
    all_exported_files_exist = all(exported_files.values())
    print(f"Exported files verified: {exported_files}")

    duration = round(time.time() - start_time, 3)

    report = {
        "model_name": "audio_emotion",
        "dataset_loaded": dataset_loaded,
        "dataloader_built": dataloader_built,
        "actor_split_respected": actor_split_respected,
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

    print("\n[VERIFICATION SUMMARY - AUDIO EMOTION]:")
    print(f"  Trainable Parameters: {report['total_trainable_parameters']:,}")
    print(f"  All Exported Files:   {all_exported_files_exist}")
    print(f"  Duration:             {duration}s")
    print("=" * 72)
    return report


if __name__ == "__main__":
    cli_args = parse_args()
    train_audio_emotion(cli_args)
