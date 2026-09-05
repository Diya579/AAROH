"""Stress Model package (Slice 3.3).

Compact transformer encoder producing:
- stress_probability (binary stress probability)
- stress_embedding (latent representation)

Strict Invariant:
- stress_probability != distress_score
"""

from backend.ml.training.models.stress.dataset import (
    DreadditStressDataset,
    load_dreaddit_records,
)
from backend.ml.training.models.stress.model import (
    DEFAULT_STRESS_BACKBONE,
    StressModel,
)

__all__ = [
    "StressModel",
    "DreadditStressDataset",
    "load_dreaddit_records",
    "DEFAULT_STRESS_BACKBONE",
]
