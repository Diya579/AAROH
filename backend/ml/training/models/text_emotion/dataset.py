"""Text Emotion Dataset loader combining GoEmotions and EmoHinD (Slice 3.3).

Consumes processed JSONL files from datasets/processed/:
- goemotions_{split}.jsonl (English)
- goemotions_hindi_adaptation_{split}.jsonl (Hindi)

Maps to standard 28-class GoEmotions emotion taxonomy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from backend.ml.training.preprocessing.common import read_jsonl

GOEMOTIONS_TAXONOMY: tuple[str, ...] = (
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

LABEL_TO_ID: dict[str, int] = {name: idx for idx, name in enumerate(GOEMOTIONS_TAXONOMY)}
ID_TO_LABEL: dict[int, str] = {idx: name for idx, name in enumerate(GOEMOTIONS_TAXONOMY)}


def load_combined_emotion_records(
    processed_dir: Path | str,
    split: str = "train",
    include_english: bool = True,
    include_hindi: bool = True,
) -> list[dict[str, Any]]:
    """Loads and combines GoEmotions and EmoHinD processed JSONL records for a given split."""
    p_dir = Path(processed_dir)
    records: list[dict[str, Any]] = []

    # Map split names
    en_split = "dev" if split in ("valid", "dev") else split
    hi_split = "valid" if split in ("valid", "dev") else split

    # 1. English GoEmotions
    if include_english:
        en_file = p_dir / f"goemotions_{en_split}.jsonl"
        if en_file.exists():
            en_records = read_jsonl(en_file)
            records.extend(en_records)

    # 2. Hindi EmoHinD (GoEmotions Hindi Adaptation)
    if include_hindi:
        hi_file = p_dir / f"goemotions_hindi_adaptation_{hi_split}.jsonl"
        if hi_file.exists():
            hi_records = read_jsonl(hi_file)
            records.extend(hi_records)

    return records


class TextEmotionDataset:
    """Dataset wrapper for Text Emotion training and evaluation."""

    def __init__(
        self,
        records: Sequence[dict[str, Any]],
        tokenizer: Optional[Any] = None,
        max_length: int = 128,
        num_classes: int = len(GOEMOTIONS_TAXONOMY),
    ) -> None:
        self.records = list(records)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.num_classes = num_classes

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        rec = self.records[idx]
        text = str(rec.get("text", "")).strip()

        # Multi-hot label vector of length 28
        label_vec = [0.0] * self.num_classes
        label_ids = rec.get("label_ids") or []
        for lid in label_ids:
            if isinstance(lid, int) and 0 <= lid < self.num_classes:
                label_vec[lid] = 1.0

        # Primary emotion label index
        primary_emotion = rec.get("emotion")
        primary_id = LABEL_TO_ID.get(primary_emotion, LABEL_TO_ID.get("neutral", 27))

        sample: dict[str, Any] = {
            "text": text,
            "label_vec": label_vec,
            "primary_id": primary_id,
            "utterance_id": rec.get("utterance_id") or rec.get("id", str(idx)),
            "language": rec.get("language", "en"),
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
