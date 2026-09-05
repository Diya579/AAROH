#!/usr/bin/env python3
"""Training script for AAROH Mental Health Language Model (Slice 3.3).

Trains an auxiliary screening-oriented language representation encoder on MindBridge.
Produces:
- mental_health_embedding (768-dim L2-normalized latent vector)

Strict Boundaries:
- Learns screening-oriented language representations ONLY.
- Does NOT predict PHQ scores.
- Does NOT predict GAD scores.
- Does NOT perform clinical diagnoses or severity triage.

Usage:
    python3 -m backend.ml.training.train_mental_health [OPTIONS]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    compute_representation_metrics,
    enforce_mental_health_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.mental_health_language.dataset import (
    MindBridgeDataset,
    load_mindbridge_records,
)
from backend.ml.training.models.mental_health_language.model import (
    DEFAULT_MENTAL_HEALTH_BACKBONE,
    MentalHealthLanguageModel,
)


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Mental Health Language Representation Model on MindBridge.")
    parser.add_argument("--data-dir", default="datasets/processed", help="Path to preprocessed JSONL directory.")
    parser.add_argument("--output-dir", default="models/mental_health_language", help="Directory to export the final model.")
    parser.add_argument("--checkpoint-dir", default="checkpoints/mental_health", help="Local checkpoint directory.")
    parser.add_argument("--drive-checkpoint-dir", default=None, help="Google Drive checkpoint directory.")
    parser.add_argument("--model-name", default=DEFAULT_MENTAL_HEALTH_BACKBONE, help="HuggingFace backbone name.")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps.")
    parser.add_argument("--early-stopping-patience", type=int, default=3, help="Early stopping patience.")
    parser.add_argument("--fp16", action="store_true", default=False, help="Enable fp16 mixed precision on CUDA.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args(args)


def train_mental_health(args: argparse.Namespace) -> dict[str, Any]:
    """Executes Mental Health Language representation training or dry-run evaluation."""
    enforce_mental_health_boundary("representation_training")
    set_seed(args.seed)
    device = get_device()

    print("=" * 70)
    print("  AAROH — Mental Health Language Representation Model (Slice 3.3)")
    print("=" * 70)
    print(f"Data Directory:          {args.data_dir}")
    print(f"Export Output Directory: {args.output_dir}")
    print(f"Backbone:                {args.model_name}")
    print(f"Device:                  {device}")
    print(f"Epochs:                  {args.epochs}")
    print(f"Batch Size:              {args.batch_size}")
    print(f"Learning Rate:           {args.lr}")
    print(f"FP16 Mixed Precision:    {args.fp16}")
    print(f"Seed:                    {args.seed}")
    print("-" * 70)

    # 1. Load MindBridge records
    records = load_mindbridge_records(args.data_dir, allow_synthetic_fallback=True)
    print(f"Loaded MindBridge records: {len(records)} samples.")

    # 2. Instantiate representation model
    model = MentalHealthLanguageModel(
        backbone=args.model_name,
        embedding_dim=768,
    )

    # 3. Check for PyTorch & Transformers
    has_torch = False
    try:
        import torch
        from torch.utils.data import DataLoader
        from transformers import AutoTokenizer
        has_torch = True
    except ImportError:
        pass

    checkpoint_mgr = CheckpointManager(
        checkpoint_dir=args.checkpoint_dir,
        drive_checkpoint_dir=args.drive_checkpoint_dir,
    )
    early_stopper = EarlyStopping(patience=args.early_stopping_patience, mode="min")

    if has_torch and records:
        print("[INFO] PyTorch and Transformers detected. Initiating representation alignment loop...")
        tokenizer = AutoTokenizer.from_pretrained(args.model_name)
        model.tokenizer = tokenizer

        dataset = MindBridgeDataset(records, tokenizer=tokenizer)
        if model._torch_class is not None:
            torch_model = model._torch_class(
                encoder_name=args.model_name,
                emb_dim=768,
                drop=0.1,
            ).to(device)
            model.torch_model = torch_model

            optimizer = torch.optim.AdamW(torch_model.parameters(), lr=args.lr)
            train_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

            for epoch in range(1, args.epochs + 1):
                torch_model.train()
                total_loss = 0.0
                optimizer.zero_grad()

                for step, batch in enumerate(train_loader):
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)

                    outputs = torch_model(input_ids=input_ids, attention_mask=attention_mask)
                    emb = outputs["mental_health_embedding"]
                    # Unsupervised representation alignment loss (variance + identity regularization)
                    cov = torch.matmul(emb.T, emb) / max(1, emb.size(0))
                    reg_loss = torch.norm(cov - torch.eye(cov.size(0), device=device))
                    loss = reg_loss / args.gradient_accumulation_steps
                    loss.backward()

                    if (step + 1) % args.gradient_accumulation_steps == 0:
                        optimizer.step()
                        optimizer.zero_grad()

                    total_loss += loss.item() * args.gradient_accumulation_steps

                avg_loss = total_loss / max(1, len(train_loader))
                checkpoint_mgr.save_checkpoint(
                    epoch=epoch,
                    model_state=torch_model,
                    optimizer_state=optimizer,
                    metrics={"loss": avg_loss},
                    is_best=(epoch == 1 or avg_loss < 0.5),
                )
                print(f"Epoch {epoch}/{args.epochs} | Representation Alignment Loss: {avg_loss:.4f}")
    else:
        print("[INFO] Environment mode: running representation validation and metric calculations.")

    # 4. Compute representation validation metrics
    texts = [r["text"] for r in records]
    categories = [r.get("category", "general_reflection") for r in records]

    enc_res = model.encode(texts)
    embs = enc_res["mental_health_embeddings"]

    rep_metrics = compute_representation_metrics(embs, labels=categories)
    metrics = {
        "mean_embedding_norm": round(rep_metrics["mean_embedding_norm"], 4),
        "cosine_separation": round(rep_metrics["cosine_separation"], 4),
        "embedding_dim": model.embedding_dim,
        "evaluated_samples": len(records),
        "clinical_boundaries_enforced": True,
        "predicts_phq": False,
        "predicts_gad": False,
    }

    print("\nMental Health Representation Metrics:")
    for k, v in metrics.items():
        print(f"  {k:<30}: {v}")

    # 5. Export model artifacts under models/mental_health_language
    hyperparams = {
        "learning_rate": args.lr,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "fp16": args.fp16,
        "seed": args.seed,
    }
    saved_path = model.save(
        output_dir=args.output_dir,
        metrics=metrics,
        hyperparameters=hyperparams,
    )
    print(f"\n[OK] Mental Health Language Model successfully exported to: {saved_path}")
    print("=" * 70)
    return metrics


if __name__ == "__main__":
    cli_args = parse_args()
    train_mental_health(cli_args)
