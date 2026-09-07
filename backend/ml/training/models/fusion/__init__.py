"""Multimodal Feature Fusion Module (Slice 3.5).

Exports:
- MultimodalFusionModel: The dual-mode feature fusion network.
- MultimodalFusionDataset: The dataset and dataloader builder for multimodal records.
- MultimodalInputRecord: Container for tabular, text, and audio interaction signals.
- build_synthetic_multimodal_records: Utility for reproducible verification.
- split_multimodal_records_by_case: Case-level deterministic splitting preventing leakage.
- enforce_fusion_boundary: Clinical boundary enforcement function.
"""

from backend.ml.training.models.common import enforce_fusion_boundary
from backend.ml.training.models.fusion.dataset import (
    MultimodalFusionDataset,
    MultimodalInputRecord,
    build_synthetic_multimodal_records,
    split_multimodal_records_by_case,
)
from backend.ml.training.models.fusion.model import (
    DISTILBERT_PARAM_COUNT,
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    FROZEN_BACKBONES_PARAM_COUNT,
    FUSION_EMBEDDING_DIM,
    VALID_EXECUTION_MODES,
    MultimodalFusionModel,
    WAV2VEC2_PARAM_COUNT,
)

__all__ = [
    "MultimodalFusionModel",
    "MultimodalFusionDataset",
    "MultimodalInputRecord",
    "build_synthetic_multimodal_records",
    "split_multimodal_records_by_case",
    "enforce_fusion_boundary",
    "FUSION_EMBEDDING_DIM",
    "DISTILBERT_PARAM_COUNT",
    "WAV2VEC2_PARAM_COUNT",
    "FROZEN_BACKBONES_PARAM_COUNT",
    "EXECUTION_MODE_FALLBACK",
    "EXECUTION_MODE_PYTORCH_FROZEN",
    "EXECUTION_MODE_PYTORCH_FINETUNE",
    "VALID_EXECUTION_MODES",
]
