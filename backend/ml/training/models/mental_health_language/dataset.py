"""MindBridge Mental Health Language Dataset loader (Slice 3.3).

Consumes processed screening language data.
Strict Boundaries:
- Learns screening-oriented language representations ONLY.
- Does NOT expose or predict PHQ scores, GAD scores, or clinical diagnoses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

from backend.ml.training.models.common import enforce_mental_health_boundary
from backend.ml.training.preprocessing.common import read_jsonl

# Standard screening language categories (domain representations only, no clinical diagnoses)
SCREENING_CATEGORIES: tuple[str, ...] = (
    "affect_expression",
    "sleep_fatigue",
    "social_engagement",
    "anhedonia_interest",
    "cognitive_clarity",
    "general_reflection",
)


def load_mindbridge_records(
    processed_dir: Path | str = "datasets/processed",
    allow_synthetic_fallback: bool = True,
) -> list[dict[str, Any]]:
    """Loads MindBridge screening language records.

    If datasets/processed/mindbridge.jsonl or datasets/mindbridge exists, loads it.
    If not yet placed, provides structured screening text samples for offline dry runs and testing.
    """
    p_dir = Path(processed_dir)
    mindbridge_file = p_dir / "mindbridge.jsonl"

    if mindbridge_file.exists():
        records = read_jsonl(mindbridge_file)
        # Enforce boundary: strip any raw clinical score fields if present
        clean_records = []
        for r in records:
            clean_r = {
                "text": str(r.get("text", "")).strip(),
                "category": r.get("category", "general_reflection"),
                "utterance_id": r.get("utterance_id") or r.get("id", ""),
            }
            clean_records.append(clean_r)
        return clean_records

    # Check raw directory
    raw_dir = Path("datasets/mindbridge")
    if raw_dir.exists():
        data_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.jsonl"))
        if data_files:
            # If raw file exists, read and return
            first_file = data_files[0]
            if first_file.suffix == ".jsonl":
                return read_jsonl(first_file)

    if not allow_synthetic_fallback:
        raise FileNotFoundError(
            f"MindBridge dataset not found under '{processed_dir}/mindbridge.jsonl' "
            "or 'datasets/mindbridge/'. Please place MindBridge dataset files."
        )

    # Standard offline screening language samples for testing and dry-run verification
    synthetic_samples = [
        {"utterance_id": "mb_01", "text": "I have been having trouble sleeping consistently this week.", "category": "sleep_fatigue"},
        {"utterance_id": "mb_02", "text": "Things I normally enjoy just feel flat and uninteresting lately.", "category": "anhedonia_interest"},
        {"utterance_id": "mb_03", "text": "I feel disconnected from my friends and tend to stay alone.", "category": "social_engagement"},
        {"utterance_id": "mb_04", "text": "It feels hard to concentrate on my daily coursework and reading.", "category": "cognitive_clarity"},
        {"utterance_id": "mb_05", "text": "I felt a bit overwhelmed yesterday but rested this morning.", "category": "affect_expression"},
        {"utterance_id": "mb_06", "text": "Had a regular walk in the park today and felt calm.", "category": "general_reflection"},
    ]
    return synthetic_samples


class MindBridgeDataset:
    """Dataset wrapper for MindBridge screening language representation learning."""

    def __init__(
        self,
        records: Sequence[dict[str, Any]],
        tokenizer: Optional[Any] = None,
        max_length: int = 128,
    ) -> None:
        self.records = list(records)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        rec = self.records[idx]
        text = str(rec.get("text", "")).strip()

        # Strictly enforce boundary: no PHQ/GAD scores allowed
        enforce_mental_health_boundary("representation_only")

        sample: dict[str, Any] = {
            "text": text,
            "category": rec.get("category", "general_reflection"),
            "utterance_id": rec.get("utterance_id", str(idx)),
        }

        if self.tokenizer is not None:
            try:
                tokens = self.tokenizer(
                    text,
                    max_length=self.max_length,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt",
                )
                sample["input_ids"] = tokens["input_ids"].squeeze(0)
                sample["attention_mask"] = tokens["attention_mask"].squeeze(0)
            except Exception:
                pass

        return sample
