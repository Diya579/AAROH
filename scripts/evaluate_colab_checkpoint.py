#!/usr/bin/env python3
"""AAROH — Standalone Text Emotion Checkpoint Evaluation Script.

Executes memory-safe batched evaluation from an existing trained checkpoint:
- Preserves PYTORCH_FINETUNE execution mode
- Enforces model.eval() and torch.no_grad()
- Chunks texts into small batches (default: 16)
- Transfers only active batch to CUDA and immediately collects outputs on CPU
- Computes aggregate and language-specific (English vs Hindi) metrics
- Performs threshold sweep
- Evaluates 18 sanity cases (English + Hindi crisis/emotion pairs)
- Verifies fresh model reload and exports evaluation artifacts
- Checks GO / NO-GO acceptance gates

Usage:
    python3 scripts/evaluate_colab_checkpoint.py [OPTIONS]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    multilabel_confusion_matrix,
    precision_recall_fscore_support,
)

from backend.ml.training.models.common import CheckpointManager, set_seed
from backend.ml.training.models.text_emotion.dataset import (
    GOEMOTIONS_TAXONOMY,
    load_combined_emotion_records,
)
from backend.ml.training.models.text_emotion.model import (
    EXECUTION_MODE_PYTORCH_FINETUNE,
    TextEmotionModel,
)
from backend.ml.training.train_text_emotion import load_balanced_split

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AAROH — Text Emotion Checkpoint Evaluation")
    parser.add_argument(
        "--checkpoint-path",
        default="checkpoints/text_emotion/colab_finetune_40k_checkpoints/best_checkpoint.pt",
        help="Path to trained checkpoint (.pt file)",
    )
    parser.add_argument(
        "--data-dir",
        default="datasets/processed",
        help="Path to datasets/processed directory",
    )
    parser.add_argument(
        "--output-dir",
        default="checkpoints/text_emotion/colab_finetune_40k_run",
        help="Path to export verified evaluation artifacts (isolated from production)",
    )
    parser.add_argument(
        "--max-val-samples",
        type=int,
        default=4000,
        help="Number of validation samples to evaluate (exact 50/50 balance)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Memory-safe batch size for inference",
    )
    parser.add_argument(
        "--model-name",
        default="distilbert-base-multilingual-cased",
        help="HuggingFace model backbone",
    )
    parser.add_argument(
        "--execution-mode",
        default=EXECUTION_MODE_PYTORCH_FINETUNE,
        help="Execution mode (default: PYTORCH_FINETUNE)",
    )
    parser.add_argument(
        "--unfreeze-layers",
        type=int,
        default=2,
        help="Number of upper transformer layers unfrozen",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    print("=" * 75)
    print("  AAROH — TEXT EMOTION CHECKPOINT EVALUATION (NO-RETRAIN)")
    print("=" * 75)
    print(f"Checkpoint Path:     {args.checkpoint_path}")
    print(f"Dataset Directory:   {args.data_dir}")
    print(f"Artifact Output Dir: {args.output_dir}")
    print(f"Execution Mode:      {args.execution_mode}")
    print(f"Validation Samples:  {args.max_val_samples}")
    print(f"Batch Size:          {args.batch_size}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Hardware Device:     {device}")
    if device == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU Name:            {props.name} ({round(props.total_memory / (1024**3), 2)} GB VRAM)")
    print("-" * 75)

    # 1. Checkpoint Verification
    ckpt_path = Path(args.checkpoint_path)
    if not ckpt_path.exists():
        print(f"[ERROR] Checkpoint file does not exist: {ckpt_path}")
        sys.exit(1)

    print(f"[1/8] Inspecting checkpoint payload from {ckpt_path}...")
    loaded_ckpt = torch.load(ckpt_path, map_location="cpu")
    print(f"  Checkpoint keys: {list(loaded_ckpt.keys())}")
    print(f"  Recorded Epoch:  {loaded_ckpt.get('epoch')}")
    print(f"  Recorded Step:   {loaded_ckpt.get('global_step')}")
    print(f"  Recorded Metrics:{loaded_ckpt.get('metrics')}")

    # 2. Dataset Loading (Exact 50/50 Language Balance)
    print(f"\n[2/8] Loading validation dataset ({args.max_val_samples} samples)...")
    val_records = load_balanced_split(
        args.data_dir,
        split="valid",
        max_samples=args.max_val_samples,
        seed=args.seed,
    )
    val_en = sum(1 for r in val_records if r.get("language") == "en")
    val_hi = sum(1 for r in val_records if r.get("language") == "hi")
    print(f"  Validation split loaded: {len(val_records)} samples (EN: {val_en}, HI: {val_hi})")
    assert len(val_records) > 0, "No validation records loaded!"

    num_classes = len(GOEMOTIONS_TAXONOMY)
    val_texts = [r.get("text", "") for r in val_records]
    val_true_labels = []
    for r in val_records:
        vec = [0.0] * num_classes
        for lid in r.get("label_ids", []):
            if 0 <= lid < num_classes:
                vec[lid] = 1.0
        val_true_labels.append(vec)
    val_true_matrix = np.array(val_true_labels, dtype=np.float32)

    # 3. Fresh Model Instantiation & Reload
    print(f"\n[3/8] Instantiating fresh TextEmotionModel in '{args.execution_mode}' mode...")
    fresh_model = TextEmotionModel(
        backbone=args.model_name,
        num_classes=num_classes,
        embedding_dim=768,
        execution_mode=args.execution_mode,
        unfreeze_layers=args.unfreeze_layers,
    )
    state_dict_payload = loaded_ckpt.get("model_state_dict", loaded_ckpt)
    fresh_model.load_state_dict(state_dict_payload)
    if fresh_model.torch_model is not None:
        fresh_model.torch_model.to(device)
        fresh_model.torch_model.eval()
    print("  Fresh-process model weights reloaded successfully.")

    # 4. Reload Sanity Step
    print("\n[4/8] Testing basic inference on 2 sanity phrases...")
    test_phrase = ["I am very thankful for this help", "यह बहुत डरावना था"]
    sanity_probe = fresh_model.encode_and_predict(test_phrase, device=device, batch_size=args.batch_size)
    assert len(sanity_probe["emotion_probabilities"]) == 2
    assert len(sanity_probe["emotion_embeddings"][0]) == 768
    print("  ✓ Reloaded inference verified (2 phrases, 768-D embeddings).")

    # 5. Memory-Safe Batched Validation Inference
    print(f"\n[5/8] Running memory-safe batched inference on {len(val_texts)} validation examples...")
    t0 = time.time()
    eval_preds = fresh_model.encode_and_predict(val_texts, device=device, batch_size=args.batch_size)
    pred_prob_dicts = eval_preds["emotion_probabilities"]
    pred_embs = eval_preds["emotion_embeddings"]
    inf_duration = time.time() - t0
    print(f"  ✓ Batched inference completed in {inf_duration:.2f}s ({round(len(val_texts)/inf_duration, 1)} ex/s).")
    print(f"  ✓ Predictions collected: {len(pred_prob_dicts)} | Latent embeddings: {len(pred_embs)}")

    pred_prob_matrix = np.zeros_like(val_true_matrix)
    for i, p_dict in enumerate(pred_prob_dicts):
        for c, name in enumerate(GOEMOTIONS_TAXONOMY):
            pred_prob_matrix[i, c] = p_dict.get(name, 0.0)

    # Compute validation loss in batches on CPU to avoid CUDA OOM
    val_loss = 0.0
    if fresh_model.torch_model is not None and fresh_model.tokenizer is not None:
        print("  Computing validation BCE loss...")
        val_logits_list = []
        with torch.no_grad():
            for vi in range(0, len(val_texts), args.batch_size):
                v_batch_texts = val_texts[vi : vi + args.batch_size]
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
            val_loss = float(
                torch.nn.functional.binary_cross_entropy_with_logits(
                    val_logits_tensor, val_targets_tensor
                ).item()
            )
        print(f"  Validation Loss: {val_loss:.4f}")

    # 6. Aggregate & Language-Specific Evaluation
    print("\n[6/8] Computing aggregate and language-specific metrics (threshold=0.5)...")
    agg_eval = compute_metrics_dict(val_true_matrix, pred_prob_matrix, th=0.5)

    en_indices = [i for i, r in enumerate(val_records) if r.get("language") == "en"]
    hi_indices = [i for i, r in enumerate(val_records) if r.get("language") == "hi"]
    en_eval = compute_metrics_dict(val_true_matrix[en_indices], pred_prob_matrix[en_indices], th=0.5) if en_indices else {}
    hi_eval = compute_metrics_dict(val_true_matrix[hi_indices], pred_prob_matrix[hi_indices], th=0.5) if hi_indices else {}

    # Threshold sweep on Aggregate
    print("  Performing threshold sweep on aggregate macro F1...")
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

    # 7. 18 Sanity-Case Evaluation
    print("\n[7/8] Evaluating 18 Clinical & Crisis Sanity Test Cases...")
    sanity_texts = [c[1] for c in SANITY_CASES]
    sanity_preds = fresh_model.encode_and_predict(sanity_texts, device=device, batch_size=args.batch_size)
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

    # 8. Export Evaluation Artifacts
    print(f"\n[8/8] Exporting verified artifacts to '{args.output_dir}'...")
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
    }

    hyperparams = {
        "checkpoint_source": str(ckpt_path),
        "execution_mode": args.execution_mode,
        "model_name": args.model_name,
        "unfreeze_layers": args.unfreeze_layers,
        "val_samples": len(val_records),
        "batch_size": args.batch_size,
    }

    export_path = fresh_model.save(
        output_dir=args.output_dir,
        metrics=eval_metrics,
        hyperparameters=hyperparams,
    )
    exp_dir = Path(args.output_dir)
    exported_files = {
        "weights": (exp_dir / "pytorch_model.bin").exists(),
        "tokenizer": (exp_dir / "tokenizer.json").exists() or (exp_dir / "tokenizer_config.json").exists(),
        "config.json": (exp_dir / "config.json").exists(),
        "label_mapping.json": (exp_dir / "label_mapping.json").exists(),
        "metadata.json": (exp_dir / "metadata.json").exists(),
        "metrics.json": (exp_dir / "metrics.json").exists(),
    }
    if args.execution_mode != "FALLBACK":
        exported_files["transformer_config.json"] = (exp_dir / "transformer_config.json").exists()
    all_exported_files_exist = all(exported_files.values())

    # Gate evaluations
    gate_micro = agg_eval["micro_f1"] >= 0.40
    gate_macro = agg_eval["macro_f1"] >= 0.30
    gate_zero_rec = agg_eval["zero_recall_classes_count"] <= 12
    gate_en_micro = en_eval.get("micro_f1", 0.0) >= 0.35
    gate_hi_micro = hi_eval.get("micro_f1", 0.0) >= 0.35
    num_sanity_passed = sum(1 for sc in sanity_results if sc["matched_top3"])
    gate_sanity = num_sanity_passed >= 12
    all_gates_passed = gate_micro and gate_macro and gate_zero_rec and gate_en_micro and gate_hi_micro and gate_sanity

    # =========================================================================
    # FORMAL REPORTING AS REQUESTED BY ML ARCHITECT
    # =========================================================================
    print("\n" + "#" * 75)
    print("  AAROH — FINAL VALIDATION & FORENSIC EVALUATION REPORT")
    print("#" * 75)

    print("\n1. AGGREGATE MICRO F1:")
    print(f"   Micro Precision: {agg_eval['micro_precision']}")
    print(f"   Micro Recall:    {agg_eval['micro_recall']}")
    print(f"   Micro F1:        {agg_eval['micro_f1']}")

    print("\n2. AGGREGATE MACRO F1:")
    print(f"   Macro Precision: {agg_eval['macro_precision']}")
    print(f"   Macro Recall:    {agg_eval['macro_recall']}")
    print(f"   Macro F1:        {agg_eval['macro_f1']}")

    print("\n3. ENGLISH METRICS (N={}):".format(en_eval.get("samples_evaluated", 0)))
    print(f"   Micro F1:        {en_eval.get('micro_f1')}")
    print(f"   Macro F1:        {en_eval.get('macro_f1')}")
    print(f"   Micro Precision: {en_eval.get('micro_precision')}")
    print(f"   Micro Recall:    {en_eval.get('micro_recall')}")

    print("\n4. HINDI METRICS (N={}):".format(hi_eval.get("samples_evaluated", 0)))
    print(f"   Micro F1:        {hi_eval.get('micro_f1')}")
    print(f"   Macro F1:        {hi_eval.get('macro_f1')}")
    print(f"   Micro Precision: {hi_eval.get('micro_precision')}")
    print(f"   Micro Recall:    {hi_eval.get('micro_recall')}")

    print("\n5. PER-CLASS PRECISION / RECALL / F1 (at threshold=0.5):")
    print(f"   {'Class Name':<16} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'Support':<7} | {'Pred Pos':<8}")
    print("   " + "-" * 62)
    for c_name in GOEMOTIONS_TAXONOMY:
        cm = agg_eval["per_class_metrics"][c_name]
        print(f"   {c_name:<16} | {cm['precision']:<7.4f} | {cm['recall']:<7.4f} | {cm['f1']:<7.4f} | {cm['support']:<7} | {cm['predicted_positives']:<8}")

    print("\n6. ZERO-RECALL CLASSES:")
    print(f"   Overall Zero-Recall Count: {agg_eval['zero_recall_classes_count']} / 28")
    print(f"   Zero-Recall Classes:       {agg_eval['zero_recall_classes']}")
    hi_zero_rec = hi_eval.get("zero_recall_classes", [])
    print(f"   Hindi Zero-Recall Count:   {len(hi_zero_rec)} / 28")
    print(f"   Hindi Zero-Recall Classes: {hi_zero_rec}")

    print("\n7. BEST THRESHOLD & MACRO F1 CURVE:")
    print(f"   Optimal Threshold:         {best_th}")
    print(f"   Macro F1 at Optimal Th:    {round(best_th_macro_f1, 4)}")
    print("   Threshold curve:")
    for th_k, th_v in threshold_search.items():
        print(f"     th={th_k}: Macro F1 = {th_v}")

    print("\n8. CALIBRATION & PROBABILITY METRICS:")
    print(f"   Mean Brier Score:          {agg_eval['mean_brier_score']}")
    print(f"   Validation BCE Loss:       {round(val_loss, 4)}")
    print(f"   Exact Match Accuracy:      {agg_eval['exact_match_accuracy']}")

    print("\n9. 18 CLINICAL & CRISIS SANITY-CASE RESULTS:")
    for sc in sanity_results:
        status_sym = "✓ PASS" if sc["matched_top3"] else "✗ FAIL"
        top3_fmt = ", ".join([f"{k} ({v:.3f})" for k, v in sc["top3"]])
        print(f"   [{sc['id']:<14}] {status_sym} | Expected: {' / '.join(sc['expected']):<22}")
        print(f"       Text:  \"{sc['text']}\"")
        print(f"       Top-3: {top3_fmt}")

    print(f"\n10. FRESH-PROCESS RELOAD & BATCHED INFERENCE SUCCESS:")
    print(f"   Fresh Model Reload:        True")
    print(f"   Batched Inference (BS={args.batch_size}): True")
    print(f"   CUDA OOM Avoided:          True")
    print(f"   Total Inference Time:      {inf_duration:.2f}s ({len(val_texts)} samples)")

    print(f"\n11. EXPORTED ARTIFACT VERIFICATION ({args.output_dir}):")
    print(f"   All files exist:           {all_exported_files_exist}")
    for fname, fexists in exported_files.items():
        print(f"     - {fname:<25}: {'✓ Present' if fexists else '✗ Missing'}")

    print("\n12. ACCEPTANCE GATES VERDICT:")
    print(f"   [Gate 1] Aggregate Micro F1 >= 0.40:        {'✓ PASS' if gate_micro else '✗ FAIL'} ({agg_eval['micro_f1']})")
    print(f"   [Gate 2] Aggregate Macro F1 >= 0.30:        {'✓ PASS' if gate_macro else '✗ FAIL'} ({agg_eval['macro_f1']})")
    print(f"   [Gate 3] Zero-Recall Classes <= 12:         {'✓ PASS' if gate_zero_rec else '✗ FAIL'} ({agg_eval['zero_recall_classes_count']})")
    print(f"   [Gate 4] English Micro F1 >= 0.35:          {'✓ PASS' if gate_en_micro else '✗ FAIL'} ({en_eval.get('micro_f1')})")
    print(f"   [Gate 5] Hindi Micro F1 >= 0.35:            {'✓ PASS' if gate_hi_micro else '✗ FAIL'} ({hi_eval.get('micro_f1')})")
    print(f"   [Gate 6] Sanity Cases Passed >= 12/18:      {'✓ PASS' if gate_sanity else '✗ FAIL'} ({num_sanity_passed}/18)")
    print(f"   --------------------------------------------------------")
    print(f"   FINAL ARCHITECT VERDICT:                    {'>>> GO <<<' if all_gates_passed else '>>> NO-GO <<<'}")
    print("#" * 75 + "\n")


if __name__ == "__main__":
    main()
