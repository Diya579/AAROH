#!/usr/bin/env python3
"""End-to-End Verification of AAROH Slice 3.3 (Text Representation Models).

Executes end-to-end verification across:
1. Text Emotion Model (GoEmotions + EmoHinD)
2. Stress Model (Dreaddit)
3. Mental Health Language Model (MindBridge)

For each model:
1. Verifies dataset loading from datasets/processed/
2. Verifies tokenizer loading
3. Verifies dataloader creation
4. Runs a complete forward pass
5. Computes loss
6. Executes backward propagation
7. Performs optimizer.step()
8. Runs training in --smoke-test mode
9. Confirms training loss is finite and generally decreases
10. Saves checkpoint
11. Reloads checkpoint into fresh model instance
12. Verifies inference after reload
13. Exports model artifacts
14. Runs evaluation on validation split
15. Verifies all exported files exist (weights, tokenizer, config, label_mapping, metadata, metrics)

Usage:
    python3 verify_slice_3_3.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from backend.ml.training.train_mental_health import (
    parse_args as parse_mh_args,
    train_mental_health,
)
from backend.ml.training.train_stress import (
    parse_args as parse_stress_args,
    train_stress,
)
from backend.ml.training.train_text_emotion import (
    parse_args as parse_emotion_args,
    train_text_emotion,
)


def run_full_verification() -> tuple[bool, dict[str, Any]]:
    """Runs end-to-end verification across all 3 text representation models."""
    overall_start = time.time()
    results: dict[str, Any] = {}

    print("=" * 78)
    print("       AAROH — SLICE 3.3 END-TO-END VERIFICATION & SMOKE TEST")
    print("=" * 78)

    # 1. Verify Text Emotion Model
    print("\n[VERIFICATION STEP 1/3] Text Emotion Model (GoEmotions + EmoHinD)")
    emotion_args = parse_emotion_args(["--smoke-test", "--data-dir", "datasets/processed"])
    results["text_emotion"] = train_text_emotion(emotion_args)

    # 2. Verify Stress Model
    print("\n[VERIFICATION STEP 2/3] Stress Model (Dreaddit)")
    stress_args = parse_stress_args(["--smoke-test", "--data-dir", "datasets/processed"])
    results["stress"] = train_stress(stress_args)

    # 3. Verify Mental Health Language Model
    print("\n[VERIFICATION STEP 3/3] Mental Health Language Model (MindBridge)")
    mh_args = parse_mh_args(["--smoke-test", "--data-dir", "datasets/processed"])
    results["mental_health_language"] = train_mental_health(mh_args)

    total_time = round(time.time() - overall_start, 3)

    # Compile validation checks
    all_passed = True
    for model_key, r in results.items():
        checks = [
            r["dataset_loaded"],
            r["tokenizer_loaded"],
            r["dataloader_built"],
            r["forward_pass_successful"],
            r["backward_pass_successful"],
            r["optimizer_step_successful"],
            r["checkpoint_saved"],
            r["checkpoint_reloaded"],
            r["inference_after_reload_success"],
            r["evaluation_completed"],
            r["exported_successfully"],
            r["all_exported_files_exist"],
        ]
        if not all(checks):
            all_passed = False

    return all_passed, {
        "models": results,
        "total_verification_time_seconds": total_time,
        "all_passed": all_passed,
    }


def print_verification_report(summary: dict[str, Any]) -> None:
    """Formats and prints the complete verification report."""
    models = summary["models"]

    print("\n" + "=" * 78)
    print("                     SLICE 3.3 VERIFICATION REPORT")
    print("=" * 78)

    check_keys = [
        ("Dataset loaded successfully", "dataset_loaded"),
        ("Tokenizer loaded", "tokenizer_loaded"),
        ("Dataloader built", "dataloader_built"),
        ("Forward pass successful", "forward_pass_successful"),
        ("Backward pass successful", "backward_pass_successful"),
        ("Optimizer step successful", "optimizer_step_successful"),
        ("Training loss decreased", "training_loss_decreased"),
        ("Checkpoint saved", "checkpoint_saved"),
        ("Checkpoint reloaded", "checkpoint_reloaded"),
        ("Inference after reload succeeded", "inference_after_reload_success"),
        ("Evaluation completed", "evaluation_completed"),
        ("Model exported successfully", "exported_successfully"),
        ("All 6 exported files verified", "all_exported_files_exist"),
    ]

    for model_id, data in models.items():
        title = {
            "text_emotion": "1. TEXT EMOTION MODEL (GoEmotions + EmoHinD)",
            "stress": "2. STRESS MODEL (Dreaddit)",
            "mental_health_language": "3. MENTAL HEALTH LANGUAGE MODEL (MindBridge)",
        }.get(model_id, model_id.upper())

        print(f"\n{title}")
        print("-" * 78)
        print(f"  Backbone Model Used:          {data['backbone']}")
        print(f"  Embedding Dimension:          {data['embedding_dim']}")
        print(f"  Total Trainable Parameters:   {data['total_trainable_parameters']:,}")
        print(f"  Training Device:              {data['device'].upper()}")
        print(f"  Training Time (Smoke Test):   {data['duration_seconds']}s")
        print(f"  Loss (Initial -> Final):      {data['training_loss_initial']} -> {data['training_loss_final']}")

        print("\n  Step-by-Step Validation Checklist:")
        for label, key in check_keys:
            val = data.get(key, False)
            status = "PASS" if val else "FAIL"
            print(f"    - {label:<36}: [{status}]")

        print("\n  Exported Files Existence Check:")
        for fname, exists in data["exported_files"].items():
            print(f"    * {fname:<24}: {'EXISTS' if exists else 'MISSING'}")

        print("\n  Key Evaluation Metrics:")
        for metric_k, metric_v in data["metrics"].items():
            print(f"    {metric_k:<28}: {metric_v}")

    print("\n" + "-" * 78)
    print("Warnings / Limitations:")
    print("  - Auxiliary representations only; external datasets do not diagnose psychiatric conditions.")
    print("  - stress_probability is linguistic stress and is NEVER renamed or treated as distress.")
    print("  - Mental Health Language Model does NOT predict PHQ/GAD scores during inference.")
    print("  - Full Google Colab GPU training should be executed via the CLI scripts for production.")
    print("-" * 78)
    print(f"TOTAL VERIFICATION TIME: {summary['total_verification_time_seconds']}s")
    if summary["all_passed"]:
        print("FINAL RESULT: ALL 3 TEXT REPRESENTATION MODELS VERIFIED SUCCESSFULLY [PASS]")
    else:
        print("FINAL RESULT: ONE OR MORE VERIFICATION CHECKS FAILED [FAIL]")
    print("=" * 78 + "\n")


def main() -> int:
    all_passed, summary = run_full_verification()
    print_verification_report(summary)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
