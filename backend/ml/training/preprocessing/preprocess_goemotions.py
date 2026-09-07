"""GoEmotions dataset ingestion and preprocessing (Slice 3.2).

Detects headerless/headed TSV layout, reads emotions.txt taxonomy dynamically,
normalizes multilabel annotations, and writes standardized JSONL files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.training.preprocessing.common import (
    compute_dataset_stats,
    deterministic_sort,
    load_tsv_records,
    normalize_text,
    write_jsonl,
)

DEFAULT_GOEMOTIONS_TAXONOMY: tuple[str, ...] = (
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


def load_emotions_taxonomy(data_dir: Path | str) -> list[str]:
    """Reads emotions.txt from data_dir if present, otherwise returns default taxonomy."""
    path = Path(data_dir) / "emotions.txt"
    if path.exists():
        with open(path, mode="r", encoding="utf-8") as f:
            emotions = [line.strip() for line in f if line.strip()]
        if emotions:
            return emotions
    return list(DEFAULT_GOEMOTIONS_TAXONOMY)


def detect_goemotions_files(data_dir: Path | str) -> dict[str, Path]:
    """Automatically detects train, dev/valid, and test TSV files in GoEmotions directory."""
    path = Path(data_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"GoEmotions directory does not exist: {path}")

    tsv_files = list(path.glob("*.tsv"))
    if not tsv_files:
        raise FileNotFoundError(f"No TSV files found in GoEmotions directory: {path}")

    splits: dict[str, Path] = {}
    for f in tsv_files:
        name = f.name.lower()
        if "train" in name:
            splits["train"] = f
        elif "dev" in name or "valid" in name:
            splits["dev"] = f
        elif "test" in name:
            splits["test"] = f

    if not splits:
        raise ValueError(
            f"Could not identify train, dev, or test splits in {path}. "
            f"Found files: {[f.name for f in tsv_files]}"
        )

    return splits


def parse_multilabel_ids(raw_labels: Any) -> list[int]:
    """Parses comma-separated or whitespace-separated label IDs into integer list."""
    if isinstance(raw_labels, (list, tuple)):
        return [int(x) for x in raw_labels if str(x).strip().isdigit()]
    if isinstance(raw_labels, (int, float)):
        return [int(raw_labels)]

    s = str(raw_labels).strip().strip("[]").replace(",", " ")
    ids: list[int] = []
    for token in s.split():
        clean = token.strip()
        if clean.isdigit():
            ids.append(int(clean))
    return ids


def preprocess_goemotions_split(
    file_path: Path | str,
    split_name: str,
    taxonomy: Sequence[str],
) -> list[dict[str, Any]]:
    """Loads and standardizes a single GoEmotions TSV split."""
    # Standard official GoEmotions column order: text, label_ids, id
    default_columns = ("text", "labels", "id")
    has_header, headers, rows = load_tsv_records(
        file_path, default_columns=default_columns
    )

    header_lower_map = {h.strip().lower(): h for h in headers}

    # Detect text column
    text_col = None
    for cand in ("text", "comment", "utterance", "col_0"):
        if cand in header_lower_map:
            text_col = header_lower_map[cand]
            break
    if not text_col and headers:
        text_col = headers[0]

    # Detect label column
    label_col = None
    for cand in ("labels", "label", "emotions", "emotion", "col_1"):
        if cand in header_lower_map:
            label_col = header_lower_map[cand]
            break
    if not label_col and len(headers) > 1:
        label_col = headers[1]

    # Detect ID column
    id_col = None
    for cand in ("id", "comment_id", "col_2"):
        if cand in header_lower_map:
            id_col = header_lower_map[cand]
            break

    if not text_col or not label_col:
        raise ValueError(
            f"GoEmotions schema validation failed for {file_path}. "
            f"Unable to resolve text or labels column. Headers: {headers}"
        )

    records: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        raw_text = row.get(text_col, "")
        clean_text = normalize_text(raw_text)

        lbl_ids = parse_multilabel_ids(row.get(label_col))
        emotion_labels = [
            taxonomy[i] if 0 <= i < len(taxonomy) else f"unknown_{i}"
            for i in lbl_ids
        ]

        utt_id = str(row.get(id_col, f"{split_name}_{idx}")) if id_col else f"{split_name}_{idx}"

        record = {
            "dataset": "goemotions",
            "split": split_name,
            "language": "en",
            "text": clean_text,
            "emotion_labels": emotion_labels,
            "label_ids": lbl_ids,
            "id": utt_id,
        }
        records.append(record)

    return deterministic_sort(records, key_fields=["id", "text"])


def process_goemotions(
    data_dir: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Processes all detected GoEmotions splits and writes JSONL outputs."""
    splits = detect_goemotions_files(data_dir)
    taxonomy = load_emotions_taxonomy(data_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stats: dict[str, Any] = {
        "dataset": "goemotions",
        "splits": {},
        "total_samples": 0,
        "language": "en",
        "taxonomy_size": len(taxonomy),
    }

    for split_name, file_path in splits.items():
        records = preprocess_goemotions_split(file_path, split_name, taxonomy)
        out_file = out_dir / f"goemotions_{split_name}.jsonl"
        count = write_jsonl(records, out_file)

        stats = compute_dataset_stats(
            dataset_name="goemotions",
            records=records,
            label_field="emotion_labels",
            split_name=split_name,
            language="en",
        )
        all_stats["splits"][split_name] = stats
        all_stats["total_samples"] += count

    return all_stats
