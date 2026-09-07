"""Mental Health Language Model package (Slice 3.3).

Screening-oriented representation encoder producing:
- mental_health_embedding (latent language representation)

Strict Boundaries:
- Does NOT predict PHQ scores
- Does NOT predict GAD scores
- Does NOT perform clinical diagnosis
"""

from backend.ml.training.models.mental_health_language.dataset import (
    MindBridgeDataset,
    load_mindbridge_records,
)
from backend.ml.training.models.mental_health_language.model import (
    DEFAULT_MENTAL_HEALTH_BACKBONE,
    MentalHealthLanguageModel,
)

__all__ = [
    "MentalHealthLanguageModel",
    "MindBridgeDataset",
    "load_mindbridge_records",
    "DEFAULT_MENTAL_HEALTH_BACKBONE",
]
