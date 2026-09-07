"""AAROH Text Representation Models Package (Slice 3.3).

Provides representation encoders:
- Text Emotion Model (GoEmotions + EmoHinD)
- Stress Model (Dreaddit)
- Mental Health Language Model (MindBridge)
"""

from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    ModelExportManager,
    ModelMetadata,
    compute_accuracy,
    compute_precision_recall_f1,
    compute_representation_metrics,
    compute_roc_auc,
    enforce_mental_health_boundary,
    enforce_stress_boundary,
    get_device,
    set_seed,
)

__all__ = [
    "ModelMetadata",
    "ModelExportManager",
    "CheckpointManager",
    "EarlyStopping",
    "set_seed",
    "get_device",
    "compute_accuracy",
    "compute_precision_recall_f1",
    "compute_roc_auc",
    "compute_representation_metrics",
    "enforce_stress_boundary",
    "enforce_mental_health_boundary",
]
