"""Reusable data ingestion, validation, and normalization utilities (Slice 3.2).

Provides robust loaders, Unicode normalizers, schema validators, deterministic sorting,
and statistics generation for auxiliary training datasets.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import unicodedata
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

# Invisible formatting characters to strip (BOM, zero-width space, bidi controls)
# Note: ZERO WIDTH JOINER (\u200D) and ZERO WIDTH NON-JOINER (\u200C) are preserved for Indic scripts.
INVISIBLE_CHARS = frozenset(
    {
        "\ufeff",  # Zero-width no-break space / BOM
        "\u200b",  # Zero-width space
        "\u200e",  # Left-to-right mark
        "\u200f",  # Right-to-left mark
        "\u202a",  # Left-to-right embedding
        "\u202b",  # Right-to-left embedding
        "\u202c",  # Pop directional formatting
        "\u202d",  # Left-to-right override
        "\u202e",  # Right-to-left override
    }
)


def normalize_text(
    text: Optional[str],
    unicode_form: str = "NFKC",
    strip: bool = True,
) -> str:
    """Normalizes Unicode text, removes invisible noise, and normalizes whitespace.

    Preserves Indic scripts, conjuncts, and multilingual characters.
    """
    if not text:
        return ""

    normalized = unicodedata.normalize(unicode_form, str(text))
    # Strip invisible formatting controls
    cleaned_chars = [c for c in normalized if c not in INVISIBLE_CHARS]
    cleaned = "".join(cleaned_chars)

    if strip:
        # Collapse multiple internal whitespace runs into a single space
        return " ".join(cleaned.split())
    return cleaned


def load_csv_records(
    file_path: Path | str,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> tuple[list[str], list[dict[str, Any]]]:
    """Loads a CSV file and returns its headers and rows as dictionary mappings.

    Handles UTF-8 with BOM automatically.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    # Use utf-8-sig to automatically handle any BOM present
    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError(f"Failed to read headers from CSV: {path}")
        headers = [str(h) for h in reader.fieldnames]
        records = [dict(row) for row in reader]

    return headers, records


def load_tsv_records(
    file_path: Path | str,
    encoding: str = "utf-8",
    default_columns: Optional[Sequence[str]] = None,
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    """Loads a TSV file, detecting whether it has a header or is headerless.

    If headerless and default_columns is provided, maps rows to default_columns.
    Returns: (has_header, headers, records)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"TSV file not found: {path}")

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        first_row = next(reader, None)
        if first_row is None:
            return False, [], []

        # Heuristic detection: if default_columns are provided, check if first_row equals default_columns
        has_header = False
        if default_columns:
            cleaned_first = [c.strip().lower() for c in first_row]
            cleaned_defaults = [c.strip().lower() for c in default_columns]
            if cleaned_first == cleaned_defaults:
                has_header = True

        if has_header:
            headers = first_row
            records = [dict(zip(headers, row)) for row in reader]
        else:
            # First row is data
            if default_columns and len(default_columns) == len(first_row):
                headers = list(default_columns)
            else:
                headers = [f"col_{i}" for i in range(len(first_row))]
            records = [dict(zip(headers, first_row))]
            for row in reader:
                if len(row) == len(headers):
                    records.append(dict(zip(headers, row)))
                elif len(row) > 0:
                    # Pad or truncate row safely
                    padded = (row + [None] * len(headers))[: len(headers)]
                    records.append(dict(zip(headers, padded)))

    return has_header, headers, records


def write_jsonl(
    records: Iterable[Mapping[str, Any]],
    output_path: Path | str,
    encoding: str = "utf-8",
) -> int:
    """Writes records to a JSON Lines file deterministically with UTF-8 encoding.

    Ensures parent directories exist. Preserves multilingual characters (ensure_ascii=False).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(path, mode="w", encoding=encoding) as f:
        for record in records:
            line = json.dumps(record, ensure_ascii=False)
            f.write(f"{line}\n")
            count += 1

    return count


def read_jsonl(
    file_path: Path | str,
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Reads a JSON Lines file into a list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    records: list[dict[str, Any]] = []
    with open(path, mode="r", encoding=encoding) as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                records.append(json.loads(line_str))
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed JSON at {path}:{line_num}: {err}") from err

    return records


def validate_required_columns(
    available_columns: Iterable[str],
    required_columns: Iterable[str],
    dataset_name: str,
) -> None:
    """Validates that all required columns are present in the available columns.

    Fails with a clear descriptive error if required columns are missing.
    """
    avail = {c.strip().lower() for c in available_columns if c}
    req = [c.strip() for c in required_columns if c]
    missing = [c for c in req if c.lower() not in avail]

    if missing:
        raise ValueError(
            f"Dataset '{dataset_name}' schema validation failed: "
            f"missing required column(s): {missing}. Available columns: {sorted(avail)}"
        )


def check_missing_fields(
    record: Mapping[str, Any],
    fields: Sequence[str],
) -> list[str]:
    """Identifies fields whose values are None or empty strings."""
    missing: list[str] = []
    for f in fields:
        val = record.get(f)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(f)
    return missing


def deterministic_sort(
    records: list[dict[str, Any]],
    key_fields: Sequence[str],
) -> list[dict[str, Any]]:
    """Sorts records deterministically based on one or more key fields."""
    def _sort_key(item: dict[str, Any]) -> tuple[str, ...]:
        return tuple(str(item.get(k, "")) for k in key_fields)

    return sorted(records, key=_sort_key)


def compute_dataset_stats(
    dataset_name: str,
    records: list[dict[str, Any]],
    label_field: Optional[str] = None,
    split_name: Optional[str] = None,
    language: Optional[str] = None,
) -> dict[str, Any]:
    """Computes summary statistics for a dataset split."""
    total_samples = len(records)
    label_counts: dict[str, int] = {}
    missing_value_counts: dict[str, int] = {}

    if records:
        all_keys = list(records[0].keys())
        for k in all_keys:
            missing_value_counts[k] = 0

        for r in records:
            for k in all_keys:
                v = r.get(k)
                if v is None or (isinstance(v, str) and not v.strip()):
                    missing_value_counts[k] += 1

            if label_field and label_field in r:
                val = r[label_field]
                if isinstance(val, list):
                    for item in val:
                        label_counts[str(item)] = label_counts.get(str(item), 0) + 1
                elif val is not None:
                    label_counts[str(val)] = label_counts.get(str(val), 0) + 1

    stats: dict[str, Any] = {
        "dataset": dataset_name,
        "sample_count": total_samples,
        "language": language or "unknown",
        "missing_values": missing_value_counts,
    }
    if split_name:
        stats["split"] = split_name
    if label_counts:
        stats["label_counts"] = dict(sorted(label_counts.items(), key=lambda x: x[0]))

    return stats


def save_json(
    data: Mapping[str, Any],
    output_path: Path | str,
    indent: int = 2,
) -> None:
    """Saves structured data to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
