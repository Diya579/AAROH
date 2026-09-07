"""Text Emotion Model package (Slice 3.3).

Compact multilingual transformer producing:
- emotion_probabilities (28 classes)
- emotion_embedding (latent representation)
"""

from backend.ml.training.models.text_emotion.dataset import (
    GOEMOTIONS_TAXONOMY,
    ID_TO_LABEL,
    LABEL_TO_ID,
    TextEmotionDataset,
    load_combined_emotion_records,
)
from backend.ml.training.models.text_emotion.model import (
    DEFAULT_TEXT_EMOTION_BACKBONE,
    TextEmotionModel,
)

__all__ = [
    "TextEmotionModel",
    "TextEmotionDataset",
    "load_combined_emotion_records",
    "GOEMOTIONS_TAXONOMY",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
    "DEFAULT_TEXT_EMOTION_BACKBONE",
]
