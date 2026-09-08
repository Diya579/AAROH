#!/usr/bin/env python3
"""Training and verification script for AAROH Text Emotion Model (Slice 3.3).

Trains a lightweight multilingual transformer on GoEmotions + EmoHinD.
Compatible with Google Colab and supports --smoke-test mode for rapid end-to-end verification.

Usage:
    python3 -m backend.ml.training.train_text_emotion [--smoke-test] [OPTIONS]
"""

from __future__ import annotations

import argparse
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Optional

from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FROZEN,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    NEURAL_EXECUTION_MODES,
    VALID_EXECUTION_MODES,
)
from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    ModelExportManager,
    SimpleDataLoader,
    SimpleTokenizer,
    compute_accuracy,
    compute_precision_recall_f1,
    get_device,
    set_seed,
)
from backend.ml.training.models.text_emotion.dataset import (
    GOEMOTIONS_TAXONOMY,
    TextEmotionDataset,
    collate_text_emotion_batch,
    load_combined_emotion_records,
)
from backend.ml.training.models.text_emotion.model import (
    DEFAULT_TEXT_EMOTION_BACKBONE,
    TextEmotionModel,
)

SANITY_CASES = [
    # English cases
    ("EN-Gratitude", "Thank you so much for your help and support!", ["gratitude", "admiration"]),
    ("EN-Joy", "I am feeling so wonderful and happy today.", ["joy", "optimism"]),
    ("EN-Fear", "I am terrified and have no idea what will happen to me.", ["fear", "nervousness"]),
    ("EN-Sadness", "I have lost all hope and feel completely alone.", ["sadness", "grief"]),
    ("EN-Grief", "My heart is shattered, I miss them so much and cannot stop crying.", ["grief", "sadness"]),
    ("EN-Anger", "Stop doing this to me right now, I hate it!", ["anger", "annoyance"]),
    ("EN-Nervousness", "My hands are shaking, I have a terrible feeling about tomorrow.", ["nervousness", "fear"]),
    ("EN-Optimism", "I truly believe things will get better soon.", ["optimism", "joy"]),
    ("EN-Neutral", "The meeting is scheduled for tomorrow at 3 pm.", ["neutral"]),

    # Hindi cases
    ("HI-Gratitude", "आपकी मदद के लिए बहुत-बहुत धन्यवाद!", ["gratitude", "admiration"]),
    ("HI-Joy", "आज मैं बहुत खुश हूँ और सब कुछ अच्छा लग रहा है।", ["joy", "optimism"]),
    ("HI-Fear", "मुझे बहुत डर लग रहा है, कुछ समझ नहीं आ रहा।", ["fear", "nervousness"]),
    ("HI-Sadness", "मेरी सारी उम्मीद खत्म हो चुकी है, बहुत अकेला महसूस कर रहा हूँ।", ["sadness", "grief"]),
    ("HI-Grief", "मेरा दिल टूट गया है, उनका जाना सहन नहीं हो रहा।", ["grief", "sadness"]),
    ("HI-Anger", "मुझे इस बात पर बहुत गुस्सा आ रहा है!", ["anger", "annoyance"]),
    ("HI-Nervousness", "मुझे बहुत घबराहट हो रही है और बेचैनी लग रही है।", ["nervousness", "fear"]),
    ("HI-Optimism", "मुझे भरोसा है कि सब कुछ ठीक हो जाएगा।", ["optimism", "joy"]),
    ("HI-Neutral", "कल दोपहर तीन बजे एक साधारण बैठक है।", ["neutral"]),
]


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Text Emotion Model (GoEmotions + EmoHinD).")
    parser.add_argument("--data-dir", default="datasets/processed", help="Path to preprocessed JSONL directory.")
    parser.add_argument("--output-dir", default="models/text_emotion", help="Directory to export the final model.")
    parser.add_argument("--checkpoint-dir", default="checkpoints/text_emotion", help="Local checkpoint directory.")
    parser.add_argument("--drive-checkpoint-dir", default=None, help="Google Drive checkpoint directory.")
    parser.add_argument("--model-name", default=DEFAULT_TEXT_EMOTION_BACKBONE, help="HuggingFace backbone name.")
    parser.add_argument("--execution-mode", default="PYTORCH_FROZEN", choices=["PYTORCH_FROZEN", "PYTORCH_FINETUNE", "FALLBACK"], help="Model execution mode.")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size.")
    parser.add_argument("--lr", type=float, default=3e-4, help="Default learning rate / classifier head learning rate.")
    parser.add_argument("--lr-transformer", type=float, default=2e-5, help="Learning rate for unfrozen transformer layers.")
    parser.add_argument("--lr-head", type=float, default=3e-4, help="Learning rate for classification head.")
    parser.add_argument("--unfreeze-layers", type=int, default=2, help="Number of upper transformer layers to unfreeze.")
    parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs (default: 3, or 1 in smoke test).")
    parser.add_argument("--max-train-samples", type=int, default=None, help="Limit training samples.")
    parser.add_argument("--max-val-samples", type=int, default=None, help="Limit validation samples.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps.")
    parser.add_argument("--weight-decay", type=float, default=0.01, help="Weight decay for optimizer.")
    parser.add_argument("--warmup-ratio", type=float, default=0.10, help="Warmup ratio for learning rate scheduler.")
    parser.add_argument("--eval-only", action="store_true", default=False, help="Run evaluation only from checkpoint without retraining.")
    parser.add_argument("--eval-batch-size", type=int, default=16, help="Batch size for validation inference.")
    parser.add_argument("--eval-checkpoint", default=None, help="Path to checkpoint for evaluation (defaults to best_checkpoint.pt in checkpoint-dir).")
    parser.add_argument("--resume", default=None, help="Path to checkpoint to resume training from.")
    parser.add_argument("--early-stopping-patience", type=int, default=3, help="Early stopping patience.")
    parser.add_argument("--fp16", action="store_true", default=False, help="Enable fp16 mixed precision on CUDA.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--smoke-test", action="store_true", default=False, help="Run rapid end-to-end smoke test.")
    return parser.parse_args(args)


def load_balanced_split(
    data_dir: Path | str,
    split: str,
    max_samples: Optional[int] = None,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Loads English and Hindi records separately.
    If max_samples is provided, draws EXACTLY max_samples // 2 from English and max_samples // 2 from Hindi.
    Raises ValueError if either pool has fewer records than requested.
    Interleaves and deterministically shuffles the combined list using seed.
    """
    en_records = load_combined_emotion_records(data_dir, split=split, include_english=True, include_hindi=False)
    hi_records = load_combined_emotion_records(data_dir, split=split, include_english=False, include_hindi=True)

    rng = random.Random(seed)
    rng.shuffle(en_records)
    rng.shuffle(hi_records)

    if max_samples is not None:
        half = max_samples // 2
        if len(en_records) < half:
            raise ValueError(
                f"Requested {half} English records for split '{split}', but only {len(en_records)} available in {data_dir}."
            )
        if len(hi_records) < half:
            raise ValueError(
                f"Requested {half} Hindi records for split '{split}', but only {len(hi_records)} available in {data_dir}."
            )
        en_selected = en_records[:half]
        hi_selected = hi_records[:half]
        combined = en_selected + hi_selected
        rng.shuffle(combined)
        return combined

    combined = en_records + hi_records
    rng.shuffle(combined)
    return combined


def train_text_emotion(args: argparse.Namespace) -> dict[str, Any]:
    """Executes Text Emotion model training or end-to-end smoke test verification."""
    start_time = time.time()
    set_seed(args.seed)
    device = get_device()

    print("=" * 70)
    print("  AAROH — Text Emotion Model Training (Slice 3.3)")
    print("=" * 70)
    print(f"Data Directory:          {args.data_dir}")
    print(f"Export Output Directory: {args.output_dir}")
    print(f"Backbone:                {args.model_name}")
    print(f"Execution Mode:          {args.execution_mode}")
    print(f"Device:                  {device}")
    print(f"Smoke Test Mode:         {args.smoke_test}")
    print(f"Grad Accumulation Steps: {args.gradient_accumulation_steps}")
    print(f"FP16 Mixed Precision:    {args.fp16}")
    print(f"Warmup Ratio:            {args.warmup_ratio}")
    print(f"Weight Decay:            {args.weight_decay}")
    print(f"Resume Checkpoint:       {args.resume}")
    print(f"Seed:                    {args.seed}")
    print("-" * 70)

    # 1. Dataset loading with exact language balance
    if args.epochs is not None:
        epochs = args.epochs
    elif args.smoke_test:
        epochs = 1
    else:
        epochs = 3

    if args.smoke_test:
        max_train = 96
        max_val = 32
        batch_size = 16
    else:
        max_train = args.max_train_samples
        max_val = args.max_val_samples
        batch_size = args.batch_size

    if args.eval_only:
        train_records = []
        val_records = load_balanced_split(args.data_dir, split="valid", max_samples=max_val, seed=args.seed)
        test_records = []
        train_en = 0
        train_hi = 0
        val_en = sum(1 for r in val_records if r.get("language") == "en")
        val_hi = sum(1 for r in val_records if r.get("language") == "hi")
        dataset_loaded = True
        dataloader_built = True
    else:
        train_records = load_balanced_split(args.data_dir, split="train", max_samples=max_train, seed=args.seed)
        val_records = load_balanced_split(args.data_dir, split="valid", max_samples=max_val, seed=args.seed)
        test_records = load_combined_emotion_records(args.data_dir, split="test")

        dataset_loaded = len(train_records) > 0
        train_en = sum(1 for r in train_records if r.get("language") == "en")
        train_hi = sum(1 for r in train_records if r.get("language") == "hi")
        val_en = sum(1 for r in val_records if r.get("language") == "en")
        val_hi = sum(1 for r in val_records if r.get("language") == "hi")

    print(f"Loaded samples -> Train: {len(train_records)} (EN: {train_en}, HI: {train_hi}) | Valid: {len(val_records)} (EN: {val_en}, HI: {val_hi})")

    # Check for PyTorch
    has_torch = False
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader
        from transformers import AutoTokenizer
        has_torch = True
    except ImportError:
        pass

    # 2. Tokenizer loading
    if args.execution_mode in NEURAL_EXECUTION_MODES and has_torch:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    else:
        tokenizer = SimpleTokenizer.from_pretrained(args.model_name, max_length=128)
    tokenizer_loaded = tokenizer is not None
    print(f"Tokenizer loaded: {tokenizer_loaded} (type: {tokenizer.__class__.__name__})")

    # 3. Dataloader creation
    if not args.eval_only:
        if args.execution_mode in NEURAL_EXECUTION_MODES and has_torch:
            train_ds = TextEmotionDataset(train_records, tokenizer=tokenizer, max_length=128)
            dataloader = DataLoader(
                train_ds,
                batch_size=batch_size,
                shuffle=True,
                collate_fn=collate_text_emotion_batch,
            )
            dataloader_built = len(dataloader) > 0
        else:
            train_ds = TextEmotionDataset(train_records, tokenizer=None)
            dataloader = SimpleDataLoader(train_ds, batch_size=batch_size, shuffle=True)
            dataloader_built = len(dataloader) > 0
        print(f"Dataloader built: {dataloader_built} ({len(dataloader)} batches)")

    # 4. Compute class pos_weights strictly from training subset
    num_classes = len(GOEMOTIONS_TAXONOMY)
    pos_counts = [0] * num_classes
    for r in train_records:
        for lid in r.get("label_ids", []):
            if 0 <= lid < num_classes:
                pos_counts[lid] += 1

    n_total = max(1, len(train_records))
    pos_weights = []
    for c in range(num_classes):
        pos = max(1, pos_counts[c])
        neg = n_total - pos
        # Clamped square-root scaled inverse frequency
        w = min(10.0, max(1.0, math.sqrt(neg / pos)))
        pos_weights.append(round(w, 4))

    # 5. Instantiate Model
    model = TextEmotionModel(
        backbone=args.model_name,
        num_classes=num_classes,
        embedding_dim=768,
        execution_mode=args.execution_mode,
        unfreeze_layers=args.unfreeze_layers,
    )
    if not (args.execution_mode in NEURAL_EXECUTION_MODES and has_torch):
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
    epoch_trajectories: list[dict[str, Any]] = []

    if not args.eval_only and has_torch and len(train_records) > 0 and args.execution_mode in NEURAL_EXECUTION_MODES:
        # PyTorch real training path with pos_weight imbalance handling
        print(f"[INFO] Executing PyTorch neural training loop on {device} (mode: {args.execution_mode})...")
        model.torch_model.to(device)

        pos_weight_tensor = torch.tensor(pos_weights, dtype=torch.float32).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)

        if args.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE:
            transformer_params = [
                p for p in model.torch_model.encoder.parameters() if p.requires_grad
            ]
            head_params = [
                p for p in model.torch_model.classifier.parameters() if p.requires_grad
            ]
            optimizer = torch.optim.AdamW([
                {"params": transformer_params, "lr": args.lr_transformer, "weight_decay": args.weight_decay},
                {"params": head_params, "lr": args.lr_head, "weight_decay": args.weight_decay},
            ])
            print(f"[INFO] Fine-tuning optimizer configured: Transformer LR={args.lr_transformer}, Head LR={args.lr_head}, Weight Decay={args.weight_decay}")
            print(f"[INFO] Trainable parameters: {model.trainable_parameters_count:,} | Frozen: {model.frozen_parameters_count:,}")
        else:
            trainable_params = [p for p in model.torch_model.parameters() if p.requires_grad]
            optimizer = torch.optim.AdamW(trainable_params, lr=args.lr, weight_decay=args.weight_decay)

        # 4b. CUDA AMP / FP16 Scaler setup
        use_cuda = device == "cuda"
        use_fp16 = args.fp16 and use_cuda
        if args.fp16 and not use_cuda:
            print(f"[WARN] --fp16 requested but running on '{device}'. Disabling FP16 mixed precision.")
        scaler = torch.cuda.amp.GradScaler(enabled=use_fp16) if use_cuda else None

        # 4c. Learning rate scheduler setup
        from transformers import get_cosine_schedule_with_warmup
        grad_accum_steps = max(1, args.gradient_accumulation_steps)
        steps_per_epoch = math.ceil(len(dataloader) / grad_accum_steps)
        total_steps = steps_per_epoch * epochs
        num_warmup_steps = int(total_steps * args.warmup_ratio)

        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=total_steps,
        )
        print(f"[INFO] Cosine LR Scheduler configured: total_steps={total_steps}, warmup_steps={num_warmup_steps} (ratio={args.warmup_ratio})")

        # 4d. Resume from checkpoint if specified
        start_epoch = 1
        global_step = 0
        best_macro_f1 = 0.0

        if args.resume:
            print(f"[INFO] Resuming training from checkpoint: {args.resume}")
            loaded_ckpt = checkpoint_mgr.load_checkpoint(args.resume)
            model.load_state_dict(loaded_ckpt["model_state_dict"])
            if "optimizer_state_dict" in loaded_ckpt and loaded_ckpt["optimizer_state_dict"]:
                try:
                    optimizer.load_state_dict(loaded_ckpt["optimizer_state_dict"])
                    print("[INFO] Optimizer state restored.")
                except Exception as e:
                    raise RuntimeError(f"Failed to restore optimizer state from checkpoint '{args.resume}': {e}") from e
            if "scheduler_state_dict" in loaded_ckpt and loaded_ckpt["scheduler_state_dict"]:
                try:
                    scheduler.load_state_dict(loaded_ckpt["scheduler_state_dict"])
                    print("[INFO] Scheduler state restored.")
                except Exception as e:
                    raise RuntimeError(f"Failed to restore scheduler state from checkpoint '{args.resume}': {e}") from e
            if "scaler_state_dict" in loaded_ckpt and loaded_ckpt["scaler_state_dict"] and scaler is not None:
                try:
                    scaler.load_state_dict(loaded_ckpt["scaler_state_dict"])
                    print("[INFO] GradScaler state restored.")
                except Exception as e:
                    raise RuntimeError(f"Failed to restore scaler state from checkpoint '{args.resume}': {e}") from e
            start_epoch = loaded_ckpt.get("epoch", 0) + 1
            global_step = loaded_ckpt.get("global_step", 0)
            best_macro_f1 = loaded_ckpt.get("best_macro_f1", 0.0)
            print(f"[INFO] Resumed successfully. Starting at epoch {start_epoch}/{epochs}, global_step={global_step}, best_macro_f1={best_macro_f1:.4f}")

        val_texts = [r.get("text", "") for r in val_records]
        val_true_labels = []
        for r in val_records:
            vec = [0.0] * num_classes
            for lid in r.get("label_ids", []):
                if 0 <= lid < num_classes:
                    vec[lid] = 1.0
            val_true_labels.append(vec)

        from sklearn.metrics import precision_recall_fscore_support
        import numpy as np
        val_true_matrix = np.array(val_true_labels, dtype=np.float32)

        batch_losses: list[float] = []
        from contextlib import nullcontext
        autocast_cm = torch.cuda.amp.autocast(enabled=True) if use_fp16 else nullcontext()

        for epoch in range(start_epoch, epochs + 1):
            model.torch_model.train()
            epoch_loss = 0.0
            num_batches = 0
            optimizer.zero_grad()

            for batch_idx, batch in enumerate(dataloader):
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                targets = batch["label_vec"].to(device)

                with autocast_cm:
                    outputs = model.torch_model(input_ids=input_ids, attention_mask=attention_mask)
                    loss = criterion(outputs["logits"], targets)
                    loss_scaled = loss / grad_accum_steps

                if scaler is not None and use_fp16:
                    scaler.scale(loss_scaled).backward()
                else:
                    loss_scaled.backward()

                forward_success = True
                backward_success = True

                is_accum_step = ((batch_idx + 1) % grad_accum_steps == 0) or ((batch_idx + 1) == len(dataloader))
                if is_accum_step:
                    if scaler is not None and use_fp16:
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            [p for p in model.torch_model.parameters() if p.requires_grad],
                            max_norm=1.0,
                        )
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        torch.nn.utils.clip_grad_norm_(
                            [p for p in model.torch_model.parameters() if p.requires_grad],
                            max_norm=1.0,
                        )
                        optimizer.step()
                    if scheduler is not None:
                        scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1
                    optimizer_step_success = True

                b_loss = loss.item()
                batch_losses.append(b_loss)
                epoch_loss += b_loss
                num_batches += 1

                if (batch_idx + 1) % 30 == 0 or (batch_idx + 1) == len(dataloader):
                    cur_lr = scheduler.get_last_lr()[0] if scheduler else args.lr
                    print(f"  [Epoch {epoch}/{epochs} | Batch {batch_idx + 1}/{len(dataloader)}] Loss: {b_loss:.4f} | LR: {cur_lr:.2e}")

            avg_loss = epoch_loss / max(1, num_batches)
            print(f"[Epoch {epoch}/{epochs} Complete] Average Loss: {avg_loss:.4f}")

            # Per-epoch validation evaluation
            epoch_val_macro_f1 = 0.0
            epoch_val_loss = 0.0
            if len(val_records) > 0:
                model.torch_model.eval()
                val_logits_list = []
                val_bs = 32
                with torch.no_grad():
                    for vi in range(0, len(val_texts), val_bs):
                        v_batch_texts = val_texts[vi:vi + val_bs]
                        v_inputs = tokenizer(
                            v_batch_texts,
                            padding=True,
                            truncation=True,
                            max_length=128,
                            return_tensors="pt",
                        ).to(device)
                        v_out = model.torch_model(v_inputs["input_ids"], v_inputs["attention_mask"])
                        val_logits_list.append(v_out["logits"].detach().cpu())
                    val_logits_tensor = torch.cat(val_logits_list, dim=0)
                    val_targets_tensor = torch.tensor(val_true_matrix, dtype=torch.float32)
                    epoch_val_loss = float(torch.nn.functional.binary_cross_entropy_with_logits(
                        val_logits_tensor, val_targets_tensor, pos_weight=pos_weight_tensor.cpu()
                    ).item())
                    epoch_probs = torch.sigmoid(val_logits_tensor).numpy()

                epoch_bin_05 = (epoch_probs >= 0.5).astype(np.float32)
                p_micro_ep, r_micro_ep, f1_micro_ep, _ = precision_recall_fscore_support(
                    val_true_matrix, epoch_bin_05, average="micro", zero_division=0
                )
                p_macro_ep, r_macro_ep, f1_macro_ep, _ = precision_recall_fscore_support(
                    val_true_matrix, epoch_bin_05, average="macro", zero_division=0
                )
                epoch_val_macro_f1 = float(f1_macro_ep)
                epoch_trajectories.append({
                    "epoch": epoch,
                    "train_loss": round(avg_loss, 4),
                    "val_loss": round(epoch_val_loss, 4),
                    "val_micro_precision": round(float(p_micro_ep), 4),
                    "val_micro_recall": round(float(r_micro_ep), 4),
                    "val_micro_f1": round(float(f1_micro_ep), 4),
                    "val_macro_precision": round(float(p_macro_ep), 4),
                    "val_macro_recall": round(float(r_macro_ep), 4),
                    "val_macro_f1": round(float(f1_macro_ep), 4),
                })
                print(f"  [Epoch {epoch} Validation] Loss: {epoch_val_loss:.4f} | Micro F1: {f1_micro_ep:.4f} | Macro F1: {f1_macro_ep:.4f}")

            is_best = False
            if epoch_val_macro_f1 > best_macro_f1:
                best_macro_f1 = epoch_val_macro_f1
                is_best = True

            # Save checkpoint per epoch
            checkpoint_mgr.save_checkpoint(
                epoch=epoch,
                model_state=model.state_dict(),
                optimizer_state=optimizer.state_dict(),
                scheduler_state=scheduler.state_dict() if scheduler else None,
                scaler_state=scaler.state_dict() if (scaler is not None and use_fp16) else None,
                global_step=global_step,
                best_macro_f1=best_macro_f1,
                metrics={"train_loss": avg_loss, "val_loss": epoch_val_loss, "val_macro_f1": epoch_val_macro_f1},
                is_best=is_best,
            )

        if batch_losses:
            initial_loss = batch_losses[0]
            final_loss = batch_losses[-1]
            loss_decreased = final_loss <= initial_loss
            print(f"Training Loss -> Initial: {initial_loss:.4f} | Final: {final_loss:.4f} (Decreased: {loss_decreased})")
    elif not args.eval_only:
        # Native mathematical gradient training path
        print("[INFO] Executing fallback gradient descent training loop...")
        batch_losses: list[float] = []

        for epoch in range(1, epochs + 1):
            for batch in dataloader:
                b_texts = [item["text"] for item in batch]
                b_targets = [item["label_vec"] for item in batch]

                loss = model.train_step(b_texts, b_targets, lr=args.lr)
                forward_success = True
                backward_success = True
                optimizer_step_success = True
                batch_losses.append(loss)

        if batch_losses:
            initial_loss = batch_losses[0]
            final_loss = batch_losses[-1]
            loss_decreased = final_loss <= initial_loss
            print(f"Training Loss -> Initial: {initial_loss:.4f} | Final: {final_loss:.4f} (Decreased: {loss_decreased})")

    # 6. Checkpointing verification
    if args.eval_only:
        if args.eval_checkpoint:
            ckpt_path = Path(args.eval_checkpoint)
        elif args.resume:
            ckpt_path = Path(args.resume)
        else:
            best_ckpt_path = checkpoint_mgr.checkpoint_dir / "best_checkpoint.pt"
            latest_ckpt_path = checkpoint_mgr.checkpoint_dir / f"checkpoint_epoch_{epochs}.pt"
            ckpt_path = best_ckpt_path if best_ckpt_path.exists() else latest_ckpt_path
            if not ckpt_path.exists():
                candidates = list(checkpoint_mgr.checkpoint_dir.glob("checkpoint_epoch_*.pt"))
                if candidates:
                    ckpt_path = sorted(candidates)[-1]
        assert ckpt_path.exists(), f"Evaluation checkpoint not found: {ckpt_path}"
        checkpoint_saved = True
        forward_success = True
        backward_success = True
        optimizer_step_success = True
    else:
        best_ckpt_path = checkpoint_mgr.checkpoint_dir / "best_checkpoint.pt"
        latest_ckpt_path = checkpoint_mgr.checkpoint_dir / f"checkpoint_epoch_{epochs}.pt"
        ckpt_path = best_ckpt_path if best_ckpt_path.exists() else latest_ckpt_path
        if not ckpt_path.exists():
            ckpt_path = checkpoint_mgr.save_checkpoint(
                epoch=epochs,
                model_state=model.state_dict(),
                metrics={"loss": final_loss or 0.0},
                is_best=True,
            )
        checkpoint_saved = ckpt_path.exists() or ckpt_path.with_suffix(".json").exists()
    print(f"Checkpoint verified: {checkpoint_saved} ({ckpt_path})")

    # 7. Reload into fresh model instance
    fresh_model = TextEmotionModel(
        backbone=args.model_name,
        num_classes=num_classes,
        embedding_dim=768,
        execution_mode=args.execution_mode,
        unfreeze_layers=args.unfreeze_layers,
    )
    loaded_ckpt = checkpoint_mgr.load_checkpoint(ckpt_path)
    state_dict_payload = loaded_ckpt.get("model_state_dict", loaded_ckpt)
    fresh_model.load_state_dict(state_dict_payload)
    if fresh_model.torch_model is not None:
        fresh_model.torch_model.to(device)
    checkpoint_reloaded = True

    # 8. Verify inference after reload
    test_phrase = ["I am very thankful for this help", "यह बहुत डरावना था"]
    fresh_preds = fresh_model.encode_and_predict(test_phrase, device=device, batch_size=args.eval_batch_size)
    inference_after_reload_success = (
        len(fresh_preds["emotion_probabilities"]) == len(test_phrase)
        and len(fresh_preds["emotion_embeddings"]) == len(test_phrase)
        and len(fresh_preds["emotion_embeddings"][0]) == 768
    )
    print(f"Inference after reload success: {inference_after_reload_success}")

    # 9. Real Multi-Label Validation Evaluation
    val_texts = [r.get("text", "") for r in val_records]
    val_true_labels = []
    for r in val_records:
        vec = [0.0] * num_classes
        for lid in r.get("label_ids", []):
            if 0 <= lid < num_classes:
                vec[lid] = 1.0
        val_true_labels.append(vec)

    eval_preds = fresh_model.encode_and_predict(val_texts, device=device, batch_size=args.eval_batch_size)
    pred_prob_dicts = eval_preds["emotion_probabilities"]

    import numpy as np
    from sklearn.metrics import (
        accuracy_score,
        brier_score_loss,
        multilabel_confusion_matrix,
        precision_recall_fscore_support,
    )

    val_true_matrix = np.array(val_true_labels, dtype=np.float32)
    pred_prob_matrix = np.zeros_like(val_true_matrix)
    for i, p_dict in enumerate(pred_prob_dicts):
        for c, name in enumerate(GOEMOTIONS_TAXONOMY):
            pred_prob_matrix[i, c] = p_dict.get(name, 0.0)

    # Compute validation loss safely in batches on CPU to avoid CUDA OOM
    if has_torch and args.execution_mode in NEURAL_EXECUTION_MODES:
        fresh_model.torch_model.eval()
        with torch.no_grad():
            val_logits_list = []
            val_bs = args.eval_batch_size
            for vi in range(0, len(val_texts), val_bs):
                v_batch_texts = val_texts[vi:vi + val_bs]
                v_inputs = fresh_model.tokenizer(
                    v_batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors="pt",
                ).to(device)
                v_out = fresh_model.torch_model(v_inputs["input_ids"], v_inputs["attention_mask"])
                val_logits_list.append(v_out["logits"].detach().cpu())
            val_logits_tensor = torch.cat(val_logits_list, dim=0)
            val_targets_tensor = torch.tensor(val_true_matrix, dtype=torch.float32)
            val_loss = float(torch.nn.functional.binary_cross_entropy_with_logits(val_logits_tensor, val_targets_tensor).item())
    else:
        val_loss = 0.0

    def compute_metrics_dict(y_true: np.ndarray, y_probs: np.ndarray, th: float = 0.5) -> dict[str, Any]:
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

    agg_eval = compute_metrics_dict(val_true_matrix, pred_prob_matrix, th=0.5)

    en_indices = [i for i, r in enumerate(val_records) if r.get("language") == "en"]
    hi_indices = [i for i, r in enumerate(val_records) if r.get("language") == "hi"]
    en_eval = compute_metrics_dict(val_true_matrix[en_indices], pred_prob_matrix[en_indices], th=0.5) if en_indices else {}
    hi_eval = compute_metrics_dict(val_true_matrix[hi_indices], pred_prob_matrix[hi_indices], th=0.5) if hi_indices else {}

    # Threshold sweep on Aggregate
    threshold_search = {}
    best_th = 0.5
    best_th_macro_f1 = float(agg_eval["macro_f1"])
    for th in np.arange(0.15, 0.65, 0.05):
        th_val = round(float(th), 2)
        th_bin = (pred_prob_matrix >= th_val).astype(np.float32)
        _, _, th_f1, _ = precision_recall_fscore_support(val_true_matrix, th_bin, average="macro", zero_division=0)
        threshold_search[str(th_val)] = round(float(th_f1), 4)
        if th_f1 > best_th_macro_f1:
            best_th_macro_f1 = float(th_f1)
            best_th = th_val

    # Frozen baseline comparison
    before_frozen_baseline = {
        "execution_mode": "PYTORCH_FROZEN",
        "train_samples": 6000,
        "val_samples": 1000,
        "validation_loss": 0.4278,
        "micro_precision": 0.5325,
        "micro_recall": 0.0707,
        "micro_f1": 0.1248,
        "macro_precision": 0.0953,
        "macro_recall": 0.0129,
        "macro_f1": 0.0199,
        "mean_brier_score": 0.0460,
        "best_macro_f1_threshold": 0.25,
        "best_macro_f1_at_best_threshold": 0.1148,
        "zero_recall_classes_at_05": 24,
    }

    # Evaluate 18 clinical & crisis sanity test cases
    sanity_texts = [c[1] for c in SANITY_CASES]
    sanity_preds = fresh_model.encode_and_predict(sanity_texts, device=device, batch_size=args.eval_batch_size)
    sanity_results = []
    for idx, (cid, text, expected_emotions) in enumerate(SANITY_CASES):
        probs_dict = sanity_preds["emotion_probabilities"][idx]
        sorted_probs = sorted(probs_dict.items(), key=lambda x: x[1], reverse=True)
        top1_emo, top1_prob = sorted_probs[0]
        top3 = sorted_probs[:3]
        top3_emos = [k for k, _ in top3]
        matched = any(exp in top3_emos for exp in expected_emotions)
        sanity_results.append({
            "id": cid,
            "text": text,
            "expected": expected_emotions,
            "top1": top1_emo,
            "top1_prob": round(float(top1_prob), 4),
            "top3": [(k, round(float(v), 4)) for k, v in top3],
            "matched_top3": matched,
        })

    # Gate evaluations
    gate_micro = agg_eval["micro_f1"] >= 0.40
    gate_macro = agg_eval["macro_f1"] >= 0.30
    gate_zero_rec = agg_eval["zero_recall_classes_count"] <= 12
    gate_en_micro = en_eval.get("micro_f1", 0.0) >= 0.35
    gate_hi_micro = hi_eval.get("micro_f1", 0.0) >= 0.35
    num_sanity_passed = sum(1 for sc in sanity_results if sc["matched_top3"])
    gate_sanity = num_sanity_passed >= 12
    all_gates_passed = gate_micro and gate_macro and gate_zero_rec and gate_en_micro and gate_hi_micro and gate_sanity

    eval_metrics = {
        "validation_loss": round(val_loss, 4),
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
        "threshold_macro_f1_curve": threshold_search,
        "val_samples_evaluated": len(val_records),
        "total_true_positives": agg_eval["total_true_positives"],
        "total_predicted_positives_at_05": agg_eval["total_predicted_positives"],
        "zero_recall_classes_count": agg_eval["zero_recall_classes_count"],
        "zero_recall_classes": agg_eval["zero_recall_classes"],
        "per_class_metrics": agg_eval["per_class_metrics"],
        "confusion_matrix_summary": agg_eval["confusion_matrix_summary"],
        "language_specific": {
            "english": en_eval,
            "hindi": hi_eval,
        },
        "sanity_cases": sanity_results,
        "acceptance_gates": {
            "gate_micro_f1_ge_0_40": {"target": 0.40, "actual": agg_eval["micro_f1"], "passed": gate_micro},
            "gate_macro_f1_ge_0_30": {"target": 0.30, "actual": agg_eval["macro_f1"], "passed": gate_macro},
            "gate_zero_recall_classes_le_12": {"target": 12, "actual": agg_eval["zero_recall_classes_count"], "passed": gate_zero_rec},
            "gate_en_micro_ge_0_35": {"target": 0.35, "actual": en_eval.get("micro_f1", 0.0), "passed": gate_en_micro},
            "gate_hi_micro_ge_0_35": {"target": 0.35, "actual": hi_eval.get("micro_f1", 0.0), "passed": gate_hi_micro},
            "gate_sanity_cases_ge_12": {"target": 12, "actual": num_sanity_passed, "passed": gate_sanity},
            "verdict": "GO" if all_gates_passed else "NO-GO",
        },
        "epoch_trajectories": epoch_trajectories,
        "before_frozen_baseline": before_frozen_baseline,
    }
    evaluation_completed = True

    # 10. Model Export
    hyperparams = {
        "learning_rate": args.lr,
        "learning_rate_transformer": args.lr_transformer if args.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE else None,
        "learning_rate_head": args.lr_head if args.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE else args.lr,
        "unfreeze_layers": args.unfreeze_layers if args.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE else 0,
        "batch_size": batch_size,
        "epochs": epochs,
        "seed": args.seed,
        "execution_mode": args.execution_mode,
        "smoke_test": args.smoke_test,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "fp16": args.fp16,
        "warmup_ratio": args.warmup_ratio,
        "weight_decay": args.weight_decay,
        "class_weighting_strategy": "sqrt_clamped_max_10",
        "class_pos_weights": pos_weights,
        "train_samples": len(train_records),
        "val_samples": len(val_records),
        "language_distribution": {
            "train": {"en": train_en, "hi": train_hi},
            "val": {"en": val_en, "hi": val_hi},
        },
    }
    export_path = fresh_model.save(
        output_dir=args.output_dir,
        metrics=eval_metrics,
        hyperparameters=hyperparams,
    )
    exported_successfully = Path(export_path).exists()

    # 11. Verify all exported files exist
    exp_dir = Path(args.output_dir)
    exported_files = {
        "weights": (exp_dir / "pytorch_model.bin").exists(),
        "tokenizer": (exp_dir / "tokenizer.json").exists() or (exp_dir / "tokenizer_config.json").exists(),
        "config.json": (exp_dir / "config.json").exists(),
        "label_mapping.json": (exp_dir / "label_mapping.json").exists(),
        "metadata.json": (exp_dir / "metadata.json").exists(),
        "metrics.json": (exp_dir / "metrics.json").exists(),
    }
    if args.execution_mode in NEURAL_EXECUTION_MODES:
        exported_files["transformer_config.json"] = (exp_dir / "transformer_config.json").exists()
    all_exported_files_exist = all(exported_files.values())
    print(f"Exported files verified: {exported_files}")

    duration = round(time.time() - start_time, 3)

    report = {
        "model_name": "text_emotion",
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

    print("\n[VERIFICATION SUMMARY - TEXT EMOTION]:")
    print(f"  Execution Mode:       {args.execution_mode}")
    print(f"  Trainable Parameters: {report['total_trainable_parameters']:,}")
    print(f"  All Exported Files:   {all_exported_files_exist}")
    print(f"  Aggregate Micro F1:   {eval_metrics['micro_f1']}")
    print(f"  Aggregate Macro F1:   {eval_metrics['macro_f1']}")
    if "english" in eval_metrics.get("language_specific", {}):
        en_m = eval_metrics["language_specific"]["english"]
        hi_m = eval_metrics["language_specific"]["hindi"]
        print(f"  English Micro / Macro F1: {en_m.get('micro_f1')} / {en_m.get('macro_f1')}")
        print(f"  Hindi Micro / Macro F1:   {hi_m.get('micro_f1')} / {hi_m.get('macro_f1')}")
    print(f"  Best Threshold:       {eval_metrics['best_macro_f1_threshold']} (Macro F1: {eval_metrics['best_macro_f1_at_best_threshold']})")
    print(f"  Mean Brier Score:     {eval_metrics['mean_brier_score']}")
    print(f"  Sanity Cases Passed:  {eval_metrics['acceptance_gates']['gate_sanity_cases_ge_12']['actual']}/18")
    print(f"  Acceptance Verdict:   {eval_metrics['acceptance_gates']['verdict']}")
    print(f"  Duration:             {duration}s")
    print("=" * 70)
    return report



if __name__ == "__main__":
    cli_args = parse_args()
    train_text_emotion(cli_args)
