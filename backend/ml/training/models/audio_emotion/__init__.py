"""Audio Emotion Representation Model package (Slice 3.4).

Lightweight speech audio encoder based on facebook/wav2vec2-base trained on RAVDESS.
Produces:
- audio_emotion_probabilities (8 classes)
- audio_embedding (768-dim latent vector)
"""

from backend.ml.training.models.audio_emotion.dataset import (
    DEFAULT_TARGET_DURATION_SECONDS,
    DEFAULT_TARGET_SAMPLE_RATE,
    DEFAULT_TARGET_SAMPLES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    RAVDESS_EMOTIONS,
    RavdessDataset,
    load_and_preprocess_wav,
    split_ravdess_records_by_actor,
)
from backend.ml.training.models.audio_emotion.model import (
    DEFAULT_AUDIO_BACKBONE,
    AudioEmotionModel,
)

__all__ = [
    "AudioEmotionModel",
    "RavdessDataset",
    "load_and_preprocess_wav",
    "split_ravdess_records_by_actor",
    "RAVDESS_EMOTIONS",
    "EMOTION_TO_ID",
    "ID_TO_EMOTION",
    "DEFAULT_AUDIO_BACKBONE",
    "DEFAULT_TARGET_SAMPLE_RATE",
    "DEFAULT_TARGET_DURATION_SECONDS",
    "DEFAULT_TARGET_SAMPLES",
]
