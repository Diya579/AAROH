"""Dreaddit dataset ingestion and preprocessing (Slice 3.2).

Automatically detects Dreaddit CSV files, identifies text and stress-label columns,
ignores author/user identities for privacy, and exports normalized JSONL records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.training.preprocessing.common import (
    compute_dataset_stats,
    deterministic_sort,
    load_csv_records,
    normalize_text,
    write_jsonl,
)


def detect_dreaddit_files(data_dir: Path | str) -> list[Path]:
    """Discovers all CSV files in the Dreaddit directory without hardcoding filenames."""
    path = Path(data_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"Dreaddit directory does not exist: {path}")

    csv_files = sorted(path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in Dreaddit directory: {path}")

    return csv_files


def preprocess_dreaddit_file(file_path: Path | str) -> list[dict[str, Any]]:
    """Loads and normalizes a single Dreaddit CSV file."""
    headers, rows = load_csv_records(file_path)
    header_lower_map = {h.strip().lower(): h for h in headers}

    # Detect text column dynamically
    text_col = None
    for cand in ("text", "post_text", "body", "content", "sentence"):
        if cand in header_lower_map:
            text_col = header_lower_map[cand]
            break

    if not text_col:
        raise ValueError(
            f"Dreaddit schema validation failed: unable to detect text column in {file_path}. "
            f"Available columns: {headers}"
        )

    # Detect stress label column dynamically
    label_col = None
    for cand in ("label", "stress_label", "stress", "is_stress"):
        if cand in header_lower_map:
            label_col = header_lower_map[cand]
            break

    if not label_col:
        raise ValueError(
            f"Dreaddit schema validation failed: unable to detect stress label column in {file_path}. "
            f"Available columns: {headers}"
        )

    # Detect subreddit column dynamically
    sub_col = None
    for cand in ("subreddit", "source_subreddit", "sub"):
        if cand in header_lower_map:
            sub_col = header_lower_map[cand]
            break

    records: list[dict[str, Any]] = []
    for row in rows:
        raw_text = row.get(text_col, "")
        clean_text = normalize_text(raw_text)

        # Parse stress label (0 = not stressed, 1 = stressed)
        raw_lbl = row.get(label_col)
        stress_lbl: Optional[int] = None
        if raw_lbl is not None and str(raw_lbl).strip() != "":
            try:
                stress_lbl = int(float(str(raw_lbl).strip()))
            except (ValueError, TypeError):
                stress_lbl = None

        subreddit_name = str(row.get(sub_col, "unknown")).strip() if sub_col else "unknown"

        # Explicitly omit user/author identifying metadata
        record = {
            "dataset": "dreaddit",
            "language": "en",
            "text": clean_text,
            "stress_label": stress_lbl,
            "source_subreddit": subreddit_name,
        }
        records.append(record)

    return records


def process_dreaddit(
    data_dir: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Processes all detected Dreaddit CSVs and writes unified dreaddit.jsonl."""
    files = detect_dreaddit_files(data_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[dict[str, Any]] = []
    for f in files:
        file_records = preprocess_dreaddit_file(f)
        all_records.extend(file_records)

    # Deterministic sorting by text content and subreddit
    sorted_records = deterministic_sort(all_records, key_fields=["source_subreddit", "text"])

    out_file = out_dir / "dreaddit.jsonl"
    count = write_jsonl(sorted_records, out_file)

    stats = compute_dataset_stats(
        dataset_name="dreaddit",
        records=sorted_records,
        label_field="stress_label",
        language="en",
    )
    stats["files_processed"] = [f.name for f in files]
    stats["total_samples"] = count

    return stats
