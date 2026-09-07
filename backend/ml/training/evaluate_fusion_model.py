"""Evaluation script for Multimodal Feature Fusion Model (Slice 3.5).

Evaluates:
- Tabular feature reconstruction error (MSE) over held-out cases.
- Modality gating distribution across available modalities.
- Robustness to missing modalities (100% audio missing, 100% text missing).
- Embedding norm validation (unit L2 sphere).
- Strict clinical boundary compliance (zero distress/escalation/diagnosis).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.ml.training.models.common import enforce_fusion_boundary
from backend.ml.training.models.fusion.dataset import (
    MultimodalInputRecord,
    build_synthetic_multimodal_records,
    split_multimodal_records_by_case,
)
from backend.ml.training.models.fusion.model import MultimodalFusionModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Multimodal Feature Fusion Model (Slice 3.5)")
    parser.add_argument("--model-dir", type=str, default="models/multimodal_fusion", help="Model directory")
    parser.add_argument("--data-dir", type=str, default="datasets/processed", help="Processed datasets directory")
    parser.add_argument("--output-file", type=str, default=None, help="Optional output JSON destination")
    parser.add_argument("--seed", type=int, default=42, help="Evaluation random seed")
    return parser.parse_args()


def evaluate_fusion_model(
    model_dir: str = "models/multimodal_fusion",
    data_dir: str = "datasets/processed",
    output_file: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Runs comprehensive evaluation on the multimodal feature fusion model."""
    print("=" * 72)
    print("  AAROH — Multimodal Feature Fusion Evaluation (Slice 3.5)")
    print("=" * 72)

    model_path = Path(model_dir)
    weights_path = model_path / "weights"
    config_path = model_path / "config.json"

    if not weights_path.exists() or not config_path.exists():
        raise FileNotFoundError(
            f"Model artifacts not found in '{model_dir}'. Run train_multimodal_fusion.py first."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    fusion_dim = config_data.get("fusion_dim", 256)
    model = MultimodalFusionModel(fusion_dim=fusion_dim, seed=seed)

    # Load weights
    with open(weights_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    model.W_tab = state["W_tab"]
    model.b_tab = state["b_tab"]
    model.W_text = state["W_text"]
    model.b_text = state["b_text"]
    model.W_audio = state["W_audio"]
    model.b_audio = state["b_audio"]
    model.W_gate = state["W_gate"]
    model.b_gate = state["b_gate"]
    model.W_fusion = state["W_fusion"]
    model.b_fusion = state["b_fusion"]
    model.W_recon = state["W_recon"]
    model.b_recon = state["b_recon"]

    # Generate held-out validation cases
    all_records = build_synthetic_multimodal_records(count=120, seed=seed)
    _, val_records = split_multimodal_records_by_case(all_records, val_ratio=0.3, seed=seed)

    print(f"Loaded {len(val_records)} validation interaction records across {len(set(r.case_id for r in val_records))} held-out cases.")

    # 1. Standard Evaluation on Observed Data
    recon_losses: List[float] = []
    tab_gate_weights: List[float] = []
    text_gate_weights: List[float] = []
    audio_gate_weights: List[float] = []
    embeddings: List[List[float]] = []

    for rec in val_records:
        res = model.fuse(rec)
        emb = res["fused_embedding"]
        embeddings.append(emb)

        tab_gate_weights.append(res["modality_weights"]["tabular"])
        text_gate_weights.append(res["modality_weights"]["text"])
        audio_gate_weights.append(res["modality_weights"]["audio"])

        if rec.tabular_features is not None:
            recon = res["reconstructed_tabular"]
            errs = []
            for j, val in enumerate(rec.tabular_features):
                if val is not None and j < len(recon):
                    d = recon[j] - val
                    errs.append(d * d)
            if errs:
                recon_losses.append(sum(errs) / len(errs))

    mean_recon_loss = sum(recon_losses) / len(recon_losses) if recon_losses else 0.0
    mean_tab_gate = sum(tab_gate_weights) / len(tab_gate_weights) if tab_gate_weights else 0.0
    mean_text_gate = sum(text_gate_weights) / len(text_gate_weights) if text_gate_weights else 0.0
    mean_audio_gate = sum(audio_gate_weights) / len(audio_gate_weights) if audio_gate_weights else 0.0

    # 2. Missing Modality Stress Testing
    # Test A: 100% missing audio
    missing_audio_audio_weights: List[float] = []
    for rec in val_records:
        rec_no_audio = MultimodalInputRecord(
            case_id=rec.case_id,
            interaction_date=rec.interaction_date,
            tabular_features=rec.tabular_features,
            text_response=rec.text_response,
            text_emotion_probabilities=rec.text_emotion_probabilities,
            text_emotion_embedding=rec.text_emotion_embedding,
            stress_probability=rec.stress_probability,
            stress_embedding=rec.stress_embedding,
            mental_health_embedding=rec.mental_health_embedding,
            audio_path=None,
            audio_waveform=None,
            audio_emotion_probabilities=None,
            audio_embedding=None,
        )
        res_no_audio = model.fuse(rec_no_audio)
        missing_audio_audio_weights.append(res_no_audio["modality_weights"]["audio"])

    audio_zero_when_missing = all(w == 0.0 for w in missing_audio_audio_weights)

    # Test B: 100% missing text
    missing_text_text_weights: List[float] = []
    for rec in val_records:
        rec_no_text = MultimodalInputRecord(
            case_id=rec.case_id,
            interaction_date=rec.interaction_date,
            tabular_features=rec.tabular_features,
            text_response=None,
            text_emotion_probabilities=None,
            text_emotion_embedding=None,
            stress_probability=None,
            stress_embedding=None,
            mental_health_embedding=None,
            audio_path=rec.audio_path,
            audio_waveform=rec.audio_waveform,
            audio_emotion_probabilities=rec.audio_emotion_probabilities,
            audio_embedding=rec.audio_embedding,
        )
        res_no_text = model.fuse(rec_no_text)
        missing_text_text_weights.append(res_no_text["modality_weights"]["text"])

    text_zero_when_missing = all(w == 0.0 for w in missing_text_text_weights)

    # 3. Representation Metrics
    mean_norm = sum(math.sqrt(sum(x * x for x in emb)) for emb in embeddings) / len(embeddings) if embeddings else 1.0

    # Cosine dispersion across distinct cases
    case_embeddings: Dict[str, List[float]] = {}
    for rec, emb in zip(val_records, embeddings):
        if rec.case_id not in case_embeddings:
            case_embeddings[rec.case_id] = emb

    case_list = list(case_embeddings.values())
    pairwise_similarities: List[float] = []
    for i in range(len(case_list)):
        for j in range(i + 1, len(case_list)):
            dot = sum(a * b for a, b in zip(case_list[i], case_list[j]))
            pairwise_similarities.append(dot)
    mean_pairwise_similarity = sum(pairwise_similarities) / len(pairwise_similarities) if pairwise_similarities else 0.0
    cosine_diversity = round(1.0 - mean_pairwise_similarity, 4)

    # 4. Clinical Boundary Enforcement Check
    clinical_boundaries_verified = True
    for rec in val_records[:5]:
        out = model.fuse(rec)
        for forbidden in ["distress_score", "escalation_probability", "risk_level", "clinical_diagnosis", "diagnosis"]:
            if forbidden in out:
                clinical_boundaries_verified = False
                raise ValueError(f"CRITICAL BOUNDARY VIOLATION: '{forbidden}' found in fuse() output!")

    report = {
        "validation_samples": len(val_records),
        "mean_reconstruction_loss": round(mean_recon_loss, 4),
        "mean_gate_tabular": round(mean_tab_gate, 4),
        "mean_gate_text": round(mean_text_gate, 4),
        "mean_gate_audio": round(mean_audio_gate, 4),
        "mean_embedding_norm": round(mean_norm, 4),
        "cosine_diversity": cosine_diversity,
        "audio_zero_when_missing": audio_zero_when_missing,
        "text_zero_when_missing": text_zero_when_missing,
        "clinical_boundaries_verified": clinical_boundaries_verified,
    }

    print("\n" + "-" * 72)
    print("                     EVALUATION REPORT")
    print("-" * 72)
    print(f"Validation Samples:               {report['validation_samples']}")
    print(f"Tabular Reconstruction Error:     {report['mean_reconstruction_loss']:.4f}")
    print(f"Average Tabular Gate Weight:      {report['mean_gate_tabular']:.4f}")
    print(f"Average Text Gate Weight:         {report['mean_gate_text']:.4f}")
    print(f"Average Audio Gate Weight:        {report['mean_gate_audio']:.4f}")
    print(f"Mean Fused Embedding Norm:        {report['mean_embedding_norm']:.4f}")
    print(f"Cross-Case Representation Diversity: {report['cosine_diversity']:.4f}")
    print(f"Missing Audio Respected (0.0 w):  {report['audio_zero_when_missing']}")
    print(f"Missing Text Respected (0.0 w):   {report['text_zero_when_missing']}")
    print(f"Clinical Boundaries Enforced:     {report['clinical_boundaries_verified']}")
    print("=" * 72)

    if output_file:
        out_f = Path(output_file)
        out_f.parent.mkdir(parents=True, exist_ok=True)
        with open(out_f, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved evaluation metrics to: {output_file}")

    return report


if __name__ == "__main__":
    cli_args = parse_args()
    evaluate_fusion_model(
        model_dir=cli_args.model_dir,
        data_dir=cli_args.data_dir,
        output_file=cli_args.output_file,
        seed=cli_args.seed,
    )
