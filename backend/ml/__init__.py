"""AAROH ML subsystem.

Slice 1 defines the nested inference contract, processing status, result
source, configurable prediction horizon, and confidence/abstention
interfaces. Callers receive a Python dict. This package does not write to
PostgreSQL and does not replace the existing ``features/`` or ``risk/``
baseline.
"""

from backend.ml.config import DEFAULT_TARGET_HORIZON_DAYS, InferenceConfig
from backend.ml.contract import (
    DistressOutput,
    ExplanationOutput,
    MlInferenceResult,
    ModelOutput,
    PredictionOutput,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.inference.service import infer
from backend.ml.policies import (
    ConfidenceAbstentionPolicy,
    EvidenceContext,
    ThresholdConfidencePolicy,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)

__all__ = [
    "DEFAULT_TARGET_HORIZON_DAYS",
    "ConfidenceAbstentionPolicy",
    "DistressOutput",
    "EvidenceContext",
    "ExplanationOutput",
    "InferenceConfig",
    "MlInferenceResult",
    "ModelOutput",
    "PredictionOutput",
    "PreprocessedInteraction",
    "ProcessingStatus",
    "ResultSource",
    "RiskLevel",
    "ThresholdConfidencePolicy",
    "Trajectory",
    "infer",
    "preprocess_interaction",
]
