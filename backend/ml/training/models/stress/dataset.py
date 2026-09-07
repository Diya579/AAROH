"""Dreaddit Stress Dataset loader (Slice 3.3).

Consumes processed JSONL from datasets/processed/dreaddit.jsonl.
Strict Boundary:
- Extracts stress_label (binary: 0 = non-stressed, 1 = stressed).
- NEVER treats stress as clinical distress.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

from backend.ml.training.models.common import enforce_stress_boundary
from backend.ml.training.preprocessing.common import read_jsonl


def load_dreaddit_records(
    processed_dir: Path | str,
    split: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Loads Dreaddit processed JSONL records."""
    p_dir = Path(processed_dir)
    records: list[dict[str, Any]] = []

    # Check for split-specific files or unified file
    if split:
        split_file = p_dir / f"dreaddit_{split}.jsonl"
        if split_file.exists():
            return read_jsonl(split_file)

    unified_file = p_dir / "dreaddit.jsonl"
    if unified_file.exists():
        records = read_jsonl(unified_file)
        if split:
            records = [r for r in records if r.get("split") == split]

    return records


class DreadditStressDataset:
    """Dataset wrapper for Dreaddit social media stress records."""

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
        label = int(rec.get("stress_label", 0))

        sample: dict[str, Any] = {
            "text": text,
            "stress_label": label,
            "utterance_id": rec.get("utterance_id") or rec.get("id", str(idx)),
            "source_subreddit": rec.get("source_subreddit", "unknown"),
        }

        # Tokenize if a tokenizer is available
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
