"""AAROH Dynamic Distress Model (Slice 3.6).

Exported Symbols:
- DynamicDistressModel: Main distress estimation network with dual-mode support
- DistressInputRecord: Container for fused embedding and interaction features
- DistressDataset: In-memory dataset and batch iterator
- split_distress_records_by_case: Deterministic case-level splitting with zero data leakage
- build_synthetic_distress_records: Synthetic demonstration dataset builder
- compute_synthetic_distress_score: Deterministic demonstration label calculator
- Constants: DISTRESS_INPUT_DIM, DISTRESS_EMBEDDING_DIM, DEFAULT_THRESHOLDS, LABEL_DISCLAIMER, Execution Modes
"""

from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    DISTRESS_INPUT_DIM,
    ENGAGEMENT_COUNT,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    DistressDataset,
    DistressInputRecord,
    build_synthetic_distress_records,
    compute_synthetic_distress_score,
    split_distress_records_by_case,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_MODEL_VERSION,
    DEFAULT_THRESHOLDS,
    DISTRESS_EMBEDDING_DIM,
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    INPUT_DIM,
    LEVEL_CRITICAL,
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_MODERATE,
    THRESHOLDS_FILENAME,
    VALID_DISTRESS_LEVELS,
    VALID_EXECUTION_MODES,
    DynamicDistressModel,
    load_thresholds_from_config,
)

__all__ = [
    "DynamicDistressModel",
    "DistressInputRecord",
    "DistressDataset",
    "split_distress_records_by_case",
    "build_synthetic_distress_records",
    "compute_synthetic_distress_score",
    "DISTRESS_INPUT_DIM",
    "DISTRESS_EMBEDDING_DIM",
    "FUSED_EMBEDDING_DIM",
    "BEHAVIOURAL_COUNT",
    "ENGAGEMENT_COUNT",
    "INPUT_DIM",
    "DEFAULT_THRESHOLDS",
    "DEFAULT_MODEL_VERSION",
    "THRESHOLDS_FILENAME",
    "load_thresholds_from_config",
    "LABEL_DISCLAIMER",
    "LEVEL_LOW",
    "LEVEL_MODERATE",
    "LEVEL_HIGH",
    "LEVEL_CRITICAL",
    "VALID_DISTRESS_LEVELS",
    "VALID_EXECUTION_MODES",
    "EXECUTION_MODE_FALLBACK",
    "EXECUTION_MODE_PYTORCH_FROZEN",
    "EXECUTION_MODE_PYTORCH_FINETUNE",
]
