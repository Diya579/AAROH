"""Placeholder preprocessing module for the official EmoInHindi conversational dataset.

The official EmoInHindi dataset is a multi-turn conversational emotion dataset
comprising ~1,814 dialogues, ~44,247 utterances, 16 emotion classes, dialogue IDs,
conversational turn ordering, and emotion intensity labels.

This module is a placeholder and will be fully implemented when the official
conversational dataset files are placed in the repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


REAL_EMOINHINDI_EMOTIONS: tuple[str, ...] = (
    # 16 emotion classes of the official conversational EmoInHindi dataset
    "anger",
    "anticipation",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "surprise",
    "trust",
    "neutral",
    "love",
    "pride",
    "relief",
    "remorse",
    "shame",
    "contempt",
    "enthusiasm",
)


def preprocess_real_emoinhindi_split(
    file_path: Path | str,
    split_name: str,
) -> list[dict[str, Any]]:
    """Preprocess a split of the official EmoInHindi conversational dataset.

    Raises:
        NotImplementedError: Explaining that the official conversational dataset
            has not yet been placed in the repository.
    """
    raise NotImplementedError(
        "The official EmoInHindi conversational dataset (~1,814 dialogues, "
        "~44,247 utterances, 16 emotion classes, dialogue IDs, conversational "
        "turn ordering, and emotion intensity labels) has not yet been placed "
        "in the repository. Once placed under 'datasets/emoinhindi' or "
        "'datasets/real_emoinhindi', this module will ingest and preprocess it."
    )


def process_real_emoinhindi(
    data_dir: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Process all splits of the official EmoInHindi conversational dataset.

    Raises:
        NotImplementedError: Explaining that the official conversational dataset
            has not yet been placed in the repository.
    """
    raise NotImplementedError(
        "The official EmoInHindi conversational dataset (~1,814 dialogues, "
        "~44,247 utterances, 16 emotion classes, dialogue IDs, conversational "
        "turn ordering, and emotion intensity labels) has not yet been placed "
        "in the repository. Use process_goemotions_hindi_adaptation for the "
        "current Hindi adaptation dataset in datasets/goemotions_hindi_adaptation."
    )
