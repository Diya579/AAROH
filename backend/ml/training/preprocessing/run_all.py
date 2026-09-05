"""Orchestration script for dataset ingestion and preprocessing (Slice 3.2).

Runs all dataset preprocessors (EmoInHindi, GoEmotions, Dreaddit, RAVDESS),
writes standardized JSONL files to datasets/processed/, and outputs dataset_statistics.json.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from backend.ml.training.preprocessing.common import save_json
from backend.ml.training.preprocessing.preprocess_dreaddit import process_dreaddit
from backend.ml.training.preprocessing.preprocess_emoinhindi import process_emoinhindi
from backend.ml.training.preprocessing.preprocess_goemotions import process_goemotions
from backend.ml.training.preprocessing.preprocess_ravdess import process_ravdess


def run_all_preprocessing(
    base_data_dir: Path | str = "datasets",
    output_dir: Path | str = "datasets/processed",
) -> dict[str, Any]:
    """Runs all dataset ingestion pipelines and compiles dataset_statistics.json."""
    base_path = Path(base_data_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting AAROH Dataset Ingestion & Preprocessing (Slice 3.2)")
    print(f"Base data directory: {base_path.resolve()}")
    print(f"Output directory:    {out_path.resolve()}\n")

    combined_stats: dict[str, Any] = {
        "pipeline_version": "3.2.0",
        "datasets": {},
        "summary": {
            "total_samples": 0,
            "datasets_processed": [],
        },
    }

    # 1. EmoInHindi
    emoinhindi_dir = base_path / "emoinhindi"
    if emoinhindi_dir.exists():
        print("-> Ingesting EmoInHindi...")
        try:
            emoinhindi_stats = process_emoinhindi(emoinhindi_dir, out_path)
            combined_stats["datasets"]["emoinhindi"] = emoinhindi_stats
            combined_stats["summary"]["total_samples"] += emoinhindi_stats["total_samples"]
            combined_stats["summary"]["datasets_processed"].append("emoinhindi")
            print(f"   [OK] EmoInHindi processed: {emoinhindi_stats['total_samples']} samples across splits.")
        except Exception as err:
            print(f"   [FAIL] EmoInHindi failed: {err}", file=sys.stderr)
            raise
    else:
        print(f"   [SKIP] EmoInHindi directory not found: {emoinhindi_dir}")

    # 2. GoEmotions
    goemotions_dir = base_path / "goemotions"
    if goemotions_dir.exists():
        print("-> Ingesting GoEmotions...")
        try:
            goemotions_stats = process_goemotions(goemotions_dir, out_path)
            combined_stats["datasets"]["goemotions"] = goemotions_stats
            combined_stats["summary"]["total_samples"] += goemotions_stats["total_samples"]
            combined_stats["summary"]["datasets_processed"].append("goemotions")
            print(f"   [OK] GoEmotions processed: {goemotions_stats['total_samples']} samples across splits.")
        except Exception as err:
            print(f"   [FAIL] GoEmotions failed: {err}", file=sys.stderr)
            raise
    else:
        print(f"   [SKIP] GoEmotions directory not found: {goemotions_dir}")

    # 3. Dreaddit
    dreaddit_dir = base_path / "dreaddit"
    if dreaddit_dir.exists():
        print("-> Ingesting Dreaddit...")
        try:
            dreaddit_stats = process_dreaddit(dreaddit_dir, out_path)
            combined_stats["datasets"]["dreaddit"] = dreaddit_stats
            combined_stats["summary"]["total_samples"] += dreaddit_stats["total_samples"]
            combined_stats["summary"]["datasets_processed"].append("dreaddit")
            print(f"   [OK] Dreaddit processed: {dreaddit_stats['total_samples']} samples.")
        except Exception as err:
            print(f"   [FAIL] Dreaddit failed: {err}", file=sys.stderr)
            raise
    else:
        print(f"   [SKIP] Dreaddit directory not found: {dreaddit_dir}")

    # 4. RAVDESS
    ravdess_dir = base_path / "ravdess"
    if ravdess_dir.exists():
        print("-> Ingesting RAVDESS...")
        try:
            ravdess_stats = process_ravdess(ravdess_dir, out_path)
            combined_stats["datasets"]["ravdess"] = ravdess_stats
            combined_stats["summary"]["total_samples"] += ravdess_stats["total_samples"]
            combined_stats["summary"]["datasets_processed"].append("ravdess")
            print(f"   [OK] RAVDESS processed: {ravdess_stats['total_samples']} audio files across {ravdess_stats.get('actor_count', 0)} actors.")
        except Exception as err:
            print(f"   [FAIL] RAVDESS failed: {err}", file=sys.stderr)
            raise
    else:
        print(f"   [SKIP] RAVDESS directory not found: {ravdess_dir}")

    # Save aggregated statistics
    stats_file = out_path / "dataset_statistics.json"
    save_json(combined_stats, stats_file)
    print(f"\nSaved dataset statistics to: {stats_file}")
    print(f"Total processed samples across all datasets: {combined_stats['summary']['total_samples']}\n")

    return combined_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AAROH dataset preprocessing pipeline (Slice 3.2).")
    parser.add_argument("--data-dir", default="datasets", help="Root directory of raw datasets.")
    parser.add_argument("--output-dir", default="datasets/processed", help="Directory for processed outputs.")
    args = parser.parse_args()

    run_all_preprocessing(base_data_dir=args.data_dir, output_dir=args.output_dir)
