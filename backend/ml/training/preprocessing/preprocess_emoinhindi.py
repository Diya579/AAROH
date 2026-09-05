"""EmoInHindi / GoEmotions Hindi Adaptation compatibility layer.

NOTE: The dataset formerly stored in 'datasets/emoinhindi/' has been identified
as a Hindi adaptation of GoEmotions and renamed to 'datasets/goemotions_hindi_adaptation/'.
Its dedicated preprocessing module is now:
    backend.ml.training.preprocessing.preprocess_goemotions_hindi_adaptation

This module is maintained for backward compatibility. It re-exports all symbols
from `preprocess_goemotions_hindi_adaptation` and maps legacy `emoinhindi` functions
to their updated counterparts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.ml.training.preprocessing.preprocess_goemotions_hindi_adaptation import (
    GOEMOTIONS_HINDI_EMOTIONS,
    detect_goemotions_hindi_adaptation_files,
    map_labels_to_names,
    parse_label_ids,
    preprocess_goemotions_hindi_adaptation_split,
    process_goemotions_hindi_adaptation,
)

# Aliases for backward compatibility
EMOINHINDI_EMOTIONS = GOEMOTIONS_HINDI_EMOTIONS
detect_emoinhindi_files = detect_goemotions_hindi_adaptation_files
preprocess_emoinhindi_split = preprocess_goemotions_hindi_adaptation_split
process_emoinhindi = process_goemotions_hindi_adaptation

__all__ = [
    "EMOINHINDI_EMOTIONS",
    "GOEMOTIONS_HINDI_EMOTIONS",
    "detect_emoinhindi_files",
    "detect_goemotions_hindi_adaptation_files",
    "map_labels_to_names",
    "parse_label_ids",
    "preprocess_emoinhindi_split",
    "preprocess_goemotions_hindi_adaptation_split",
    "process_emoinhindi",
    "process_goemotions_hindi_adaptation",
]
