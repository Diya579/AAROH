#!/usr/bin/env python3
"""Standalone verification script for the official EmoInHindi conversational dataset.

Verifies the presence and structural validity of the official multi-turn
conversational EmoInHindi dataset against expected specifications:
- Approximately 1,814 dialogues
- Approximately 44,247 utterances
- 16 emotion classes
- Dialogue IDs
- Conversational turn ordering
- Emotion intensity labels
- Hindi text (Devanagari script)

Usage:
    python3 verify_real_emoinhindi.py [--data-dir PATH]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


EXPECTED_SPEC = {
    "dialogues_approx": 1814,
    "utterances_approx": 44247,
    "emotion_classes_count": 16,
    "has_dialogue_ids": True,
    "has_turn_ordering": True,
    "has_intensity": True,
    "has_hindi_text": True,
}

DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")


def check_is_hindi(text: str) -> bool:
    """Checks if text contains Devanagari characters."""
    return bool(DEVANAGARI_REGEX.search(text))


def verify_emoinhindi_dataset(
    data_dir: Path | str = "datasets/emoinhindi",
) -> tuple[bool, dict[str, Any]]:
    """Inspects and verifies the official EmoInHindi dataset directory.

    Returns:
        (is_valid, report_dict)
    """
    target_path = Path(data_dir)
    report: dict[str, Any] = {
        "target_path": str(target_path),
        "exists": False,
        "is_valid": False,
        "is_goemotions_hindi_misplaced": False,
        "checks": {},
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    if not target_path.exists():
        report["errors"].append(
            f"Dataset directory '{target_path}' does not exist. "
            "The official EmoInHindi conversational dataset has not yet been placed in the repository."
        )
        return False, report

    report["exists"] = True

    # Find candidate files (.csv, .tsv, .json, .jsonl)
    data_files = [
        p for p in target_path.glob("*.*")
        if p.suffix.lower() in {".csv", ".tsv", ".json", ".jsonl"}
    ]

    if not data_files:
        report["errors"].append(
            f"No data files (.csv, .tsv, .json, .jsonl) found in '{target_path}'."
        )
        return False, report

    # Check if files match GoEmotions Hindi adaptation (emoHi-*.csv)
    file_names = {p.name.lower() for p in data_files}
    if any(name.startswith("emohi-") for name in file_names):
        report["is_goemotions_hindi_misplaced"] = True
        report["errors"].append(
            "Found 'emoHi-*' files which belong to the GoEmotions Hindi adaptation "
            "(single-turn translated comments with 28 GoEmotions classes), NOT the "
            "official EmoInHindi conversational dataset."
        )

    # Inspect records across all data files
    total_utterances = 0
    dialogue_ids: set[str] = set()
    found_dialogue_col = False
    found_turn_col = False
    found_intensity_col = False
    emotion_labels: set[str] = set()
    hindi_utterance_count = 0

    for file_path in data_files:
        try:
            if file_path.suffix.lower() in {".csv", ".tsv"}:
                delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    fieldnames = [fn.lower().strip() for fn in (reader.fieldnames or [])]

                    # Check headers
                    if any("dialogue" in fn or "conv" in fn for fn in fieldnames):
                        found_dialogue_col = True
                    if any("turn" in fn or "order" in fn or "utt_id" in fn for fn in fieldnames):
                        found_turn_col = True
                    if any("intensity" in fn or "weight" in fn for fn in fieldnames):
                        found_intensity_col = True

                    for row in reader:
                        total_utterances += 1
                        # Check dialogue id
                        for k, v in row.items():
                            k_low = (k or "").lower()
                            if "dialogue" in k_low or "conv" in k_low:
                                if v:
                                    dialogue_ids.add(str(v).strip())
                            if "emotion" in k_low or "label" in k_low:
                                if v:
                                    emotion_labels.add(str(v).strip().lower())
                            if "text" in k_low or "utterance" in k_low or "sentence" in k_low:
                                if v and check_is_hindi(str(v)):
                                    hindi_utterance_count += 1
            elif file_path.suffix.lower() in {".json", ".jsonl"}:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        row = json.loads(line)
                        total_utterances += 1
                        if "dialogue_id" in row:
                            found_dialogue_col = True
                            if row["dialogue_id"]:
                                dialogue_ids.add(str(row["dialogue_id"]))
                        if "turn" in row or "turn_id" in row or "previous_turns" in row:
                            found_turn_col = True
                        if "intensity" in row or "emotion_intensity" in row:
                            found_intensity_col = True
                        if "emotion" in row and row["emotion"]:
                            emotion_labels.add(str(row["emotion"]).lower())
                        if "text" in row and check_is_hindi(str(row["text"])):
                            hindi_utterance_count += 1
        except Exception as e:
            report["warnings"].append(f"Could not read {file_path.name}: {e}")

    num_dialogues = len(dialogue_ids)
    num_emotions = len(emotion_labels)

    report["stats"] = {
        "files_found": [p.name for p in data_files],
        "total_utterances": total_utterances,
        "num_dialogues": num_dialogues,
        "num_emotion_classes": num_emotions,
        "hindi_utterance_ratio": (hindi_utterance_count / total_utterances) if total_utterances > 0 else 0.0,
    }

    # Evaluate checks
    check_dialogues = 1500 <= num_dialogues <= 2200
    check_utterances = 38000 <= total_utterances <= 50000
    check_emotions = (num_emotions == 16) or (14 <= num_emotions <= 18)
    check_has_dialogue_ids = found_dialogue_col and num_dialogues > 0
    check_has_turn_ordering = found_turn_col
    check_has_intensity = found_intensity_col
    check_hindi = (hindi_utterance_count / total_utterances >= 0.5) if total_utterances > 0 else False

    report["checks"] = {
        "dialogues (~1,814)": {
            "expected": "~1,814",
            "observed": num_dialogues,
            "passed": check_dialogues,
        },
        "utterances (~44,247)": {
            "expected": "~44,247",
            "observed": total_utterances,
            "passed": check_utterances,
        },
        "emotion_classes (16)": {
            "expected": 16,
            "observed": num_emotions,
            "passed": check_emotions,
        },
        "dialogue_ids": {
            "expected": True,
            "observed": check_has_dialogue_ids,
            "passed": check_has_dialogue_ids,
        },
        "conversational_turn_ordering": {
            "expected": True,
            "observed": check_has_turn_ordering,
            "passed": check_has_turn_ordering,
        },
        "emotion_intensity": {
            "expected": True,
            "observed": check_has_intensity,
            "passed": check_has_intensity,
        },
        "hindi_devanagari_text": {
            "expected": ">= 50% Hindi",
            "observed": f"{report['stats']['hindi_utterance_ratio']:.1%}",
            "passed": check_hindi,
        },
    }

    all_passed = (
        not report["is_goemotions_hindi_misplaced"]
        and check_dialogues
        and check_utterances
        and check_emotions
        and check_has_dialogue_ids
        and check_has_turn_ordering
        and check_has_intensity
        and check_hindi
    )
    report["is_valid"] = all_passed

    if not all_passed and not report["errors"]:
        failed_checks = [k for k, v in report["checks"].items() if not v["passed"]]
        report["errors"].append(
            f"Dataset does not match official EmoInHindi specifications. Failed checks: {failed_checks}"
        )

    return all_passed, report


def print_report(report: dict[str, Any]) -> None:
    """Prints a formatted validation report to stdout."""
    print("=" * 72)
    print("  AAROH — Official EmoInHindi Dataset Validation Report")
    print("=" * 72)
    print(f"Target Directory : {report['target_path']}")
    print(f"Directory Exists : {'YES' if report['exists'] else 'NO'}")

    if report["is_goemotions_hindi_misplaced"]:
        print("\n[WARNING] MISPLACED DATASET DETECTED:")
        print("  The target directory contains GoEmotions Hindi adaptation files (emoHi-*),")
        print("  which is a 28-class single-turn comment dataset, NOT the official EmoInHindi")
        print("  conversational dataset.")

    print("\nExpected vs. Observed Specifications:")
    print("-" * 72)
    print(f"{'Specification':<32} {'Expected':<16} {'Observed':<14} {'Status'}")
    print("-" * 72)

    checks = report.get("checks", {})
    if checks:
        for spec_name, check_data in checks.items():
            status = "PASS" if check_data["passed"] else "FAIL"
            print(
                f"{spec_name:<32} {str(check_data['expected']):<16} "
                f"{str(check_data['observed']):<14} [{status}]"
            )
    else:
        print("  No files available to inspect.")

    print("-" * 72)

    if report.get("errors"):
        print("\nValidation Errors:")
        for err in report["errors"]:
            print(f"  ❌ {err}")

    if report.get("warnings"):
        print("\nValidation Warnings:")
        for warn in report["warnings"]:
            print(f"  ⚠️  {warn}")

    print("=" * 72)
    if report["is_valid"]:
        print("RESULT: VALID — Official EmoInHindi dataset verified successfully.")
    else:
        print("RESULT: INVALID / MISSING — Official EmoInHindi dataset not present or invalid.")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the official EmoInHindi conversational dataset."
    )
    parser.add_argument(
        "--data-dir",
        default="datasets/emoinhindi",
        help="Path to the EmoInHindi dataset directory (default: datasets/emoinhindi)",
    )
    args = parser.parse_args()

    # If default datasets/emoinhindi doesn't exist, also try datasets/real_emoinhindi as fallback check
    target_dir = args.data_dir
    if target_dir == "datasets/emoinhindi" and not Path(target_dir).exists():
        if Path("datasets/real_emoinhindi").exists():
            target_dir = "datasets/real_emoinhindi"

    is_valid, report = verify_emoinhindi_dataset(target_dir)
    print_report(report)

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
