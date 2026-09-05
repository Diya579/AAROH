"""EmoInHindi dataset ingestion and preprocessing (Slice 3.2).

Detects the actual CSV layout for EmoInHindi, validates schemas, preserves dialogue
and utterance boundaries without inventing missing values, and normalizes into JSONL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.training.preprocessing.common import (
    compute_dataset_stats,
    deterministic_sort,
    load_csv_records,
    normalize_text,
    validate_required_columns,
    write_jsonl,
)

# Standard 28-class GoEmotions / EmoInHindi emotion taxonomy
EMOINHINDI_EMOTIONS: tuple[str, ...] = (
    "admiration",
    "amusement",
    "anger",
    "annoyance",
    "approval",
    "caring",
    "confusion",
    "curiosity",
    "desire",
    "disappointment",
    "disapproval",
    "disgust",
    "embarrassment",
    "excitement",
    "fear",
    "gratitude",
    "grief",
    "joy",
    "love",
    "nervousness",
    "optimism",
    "pride",
    "realization",
    "relief",
    "remorse",
    "sadness",
    "surprise",
    "neutral",
)


def parse_label_ids(raw_label: Any) -> list[int]:
    """Robustly parses label representations into a list of integer IDs.

    Handles bracketed array strings like '[27]', '[ 8 20]', '[2, 14]', integers, and lists.
    """
    if isinstance(raw_label, (list, tuple)):
        return [int(x) for x in raw_label if str(x).strip().isdigit()]
    if isinstance(raw_label, (int, float)):
        return [int(raw_label)]

    s = str(raw_label).strip().strip("[]").replace(",", " ")
    ids: list[int] = []
    for token in s.split():
        token_clean = token.strip()
        if token_clean.isdigit():
            ids.append(int(token_clean))
    return ids


def map_labels_to_names(
    label_ids: Sequence[int],
    taxonomy: Sequence[str] = EMOINHINDI_EMOTIONS,
) -> list[str]:
    """Maps integer label IDs to emotion names according to the taxonomy."""
    names: list[str] = []
    for idx in label_ids:
        if 0 <= idx < len(taxonomy):
            names.append(taxonomy[idx])
        else:
            names.append(f"unknown_{idx}")
    return names


def detect_emoinhindi_files(data_dir: Path | str) -> dict[str, Path]:
    """Automatically detects train, valid/dev, and test CSV files in the directory."""
    path = Path(data_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"EmoInHindi directory does not exist: {path}")

    csv_files = list(path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in EmoInHindi directory: {path}")

    splits: dict[str, Path] = {}
    for f in csv_files:
        name = f.name.lower()
        if "train" in name:
            splits["train"] = f
        elif "valid" in name or "dev" in name:
            splits["valid"] = f
        elif "test" in name:
            splits["test"] = f

    if not splits:
        raise ValueError(
            f"Could not identify train, valid, or test splits in {path}. "
            f"Found files: {[f.name for f in csv_files]}"
        )

    return splits


def preprocess_emoinhindi_split(
    file_path: Path | str,
    split_name: str,
) -> list[dict[str, Any]]:
    """Loads and normalizes a single EmoInHindi split CSV into standardized records."""
    headers, rows = load_csv_records(file_path)

    # 1. Detect column names dynamically
    header_lower_map = {h.strip().lower(): h for h in headers}

    # Detect text column
    text_col = None
    for cand in ("text", "utterance", "sentence", "content"):
        if cand in header_lower_map:
            text_col = header_lower_map[cand]
            break
    if not text_col:
        raise ValueError(
            f"EmoInHindi schema validation error: missing text column in {file_path}. "
            f"Headers detected: {headers}"
        )

    # Detect labels column
    label_col = None
    for cand in ("labels", "label", "emotion", "emotions"):
        if cand in header_lower_map:
            label_col = header_lower_map[cand]
            break
    if not label_col:
        raise ValueError(
            f"EmoInHindi schema validation error: missing labels column in {file_path}. "
            f"Headers detected: {headers}"
        )

    # Detect utterance ID column
    id_col = None
    for cand in ("id", "utterance_id", "comment_id"):
        if cand in header_lower_map:
            id_col = header_lower_map[cand]
            break

    # Detect dialogue metadata if present
    dialogue_col = None
    for cand in ("dialogue_id", "conv_id", "conversation_id"):
        if cand in header_lower_map:
            dialogue_col = header_lower_map[cand]
            break

    # Detect intensity if present
    intensity_col = None
    for cand in ("emotion_intensity", "intensity"):
        if cand in header_lower_map:
            intensity_col = header_lower_map[cand]
            break

    # Detect previous turns if present
    turns_col = None
    for cand in ("previous_turns", "context"):
        if cand in header_lower_map:
            turns_col = header_lower_map[cand]
            break

    records: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        raw_text = row.get(text_col, "")
        clean_text = normalize_text(raw_text)

        # Parse labels
        lbl_ids = parse_label_ids(row.get(label_col))
        emotion_names = map_labels_to_names(lbl_ids)
        primary_emotion = emotion_names[0] if emotion_names else "neutral"

        # Utterance ID
        utt_id = str(row.get(id_col, f"{split_name}_{idx}")) if id_col else f"{split_name}_{idx}"

        # Dialogue ID (preserve actual value if present, else None without inventing)
        dialogue_id = row.get(dialogue_col) if dialogue_col else None

        # Intensity (preserve actual value if present, else None)
        intensity_val = None
        if intensity_col and row.get(intensity_col) is not None:
            try:
                intensity_val = float(row[intensity_col])
            except (ValueError, TypeError):
                intensity_val = str(row[intensity_col])

        # Previous turns (preserve actual turns if present, else empty list)
        previous_turns = []
        if turns_col and row.get(turns_col):
            raw_turns = row[turns_col]
            if isinstance(raw_turns, list):
                previous_turns = raw_turns
            else:
                previous_turns = [str(raw_turns)]

        record: dict[str, Any] = {
            "dataset": "emoinhindi",
            "split": split_name,
            "language": "hi",
            "dialogue_id": dialogue_id,
            "utterance_id": utt_id,
            "text": clean_text,
            "emotion": primary_emotion,
            "emotion_intensity": intensity_val,
            "previous_turns": previous_turns,
            "emotion_labels": emotion_names,
            "label_ids": lbl_ids,
        }
        records.append(record)

    # Sort deterministically by utterance_id
    return deterministic_sort(records, key_fields=["utterance_id", "text"])


def process_emoinhindi(
    data_dir: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Processes all detected EmoInHindi splits and saves JSONL files.

    Returns combined dataset statistics.
    """
    splits = detect_emoinhindi_files(data_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stats: dict[str, Any] = {
        "dataset": "emoinhindi",
        "splits": {},
        "total_samples": 0,
        "language": "hi",
    }

    for split_name, file_path in splits.items():
        records = preprocess_emoinhindi_split(file_path, split_name)
        out_file = out_dir / f"emoinhindi_{split_name}.jsonl"
        count = write_jsonl(records, out_file)

        stats = compute_dataset_stats(
            dataset_name="emoinhindi",
            records=records,
            label_field="emotion",
            split_name=split_name,
            language="hi",
        )
        all_stats["splits"][split_name] = stats
        all_stats["total_samples"] += count

    return all_stats
