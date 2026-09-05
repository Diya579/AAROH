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
from backend.ml.features import (
    BehaviouralFeatures,
    EngagementConfig,
    EngagementFeatures,
    LongitudinalConfig,
    LongitudinalFeatures,
    LongitudinalTrend,
    TextFeatures,
    extract_behavioural_features,
    extract_engagement_features,
    extract_longitudinal_features,
    extract_text_features,
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
    "BehaviouralFeatures",
    "ConfidenceAbstentionPolicy",
    "DistressOutput",
    "EngagementConfig",
    "EngagementFeatures",
    "EvidenceContext",
    "ExplanationOutput",
    "InferenceConfig",
    "LongitudinalConfig",
    "LongitudinalFeatures",
    "LongitudinalTrend",
    "MlInferenceResult",
    "ModelOutput",
    "PredictionOutput",
    "PreprocessedInteraction",
    "ProcessingStatus",
    "ResultSource",
    "RiskLevel",
    "TextFeatures",
    "ThresholdConfidencePolicy",
    "Trajectory",
    "extract_behavioural_features",
    "extract_engagement_features",
    "extract_longitudinal_features",
    "extract_text_features",
    "infer",
    "preprocess_interaction",
]
