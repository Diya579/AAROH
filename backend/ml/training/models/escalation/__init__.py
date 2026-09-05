"""AAROH Escalation Assessment Model Package (Slice 3.8 Revision).

Exported Symbols:
- EscalationAssessmentModel: Interpretable Logistic Regression escalation model
- EscalationInputRecord: Unified input representation with None != 0 preservation
- EscalationConfig: Configurable horizon and risk level thresholds
- Synthetic demonstration generators and case-level splitters
- Evidence quality and temporal leakage protection
"""

from backend.ml.contract import ProcessingStatus, ResultSource, RiskLevel, Trajectory
from backend.ml.training.models.common import enforce_escalation_boundary
from backend.ml.training.models.escalation.dataset import (
    DEFAULT_MIN_CONFIDENCE_THRESHOLD,
    DEFAULT_TARGET_HORIZON_DAYS,
    DEFAULT_THRESHOLD_LOW_MODERATE,
    DEFAULT_THRESHOLD_MODERATE_HIGH,
    ESCALATION_FEATURE_NAMES,
    LABEL_DISCLAIMER,
    SMOKE_TEST_DISCLAIMER,
    ConfidencePolicyConfig,
    EscalationConfig,
    EscalationInputRecord,
    build_synthetic_escalation_records,
    determine_synthetic_escalation_target,
    filter_interactions_by_cutoff,
    split_escalation_records_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.escalation.model import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_VERSION,
    EscalationAssessmentModel,
)

__all__ = [
    "EscalationAssessmentModel",
    "EscalationInputRecord",
    "EscalationConfig",
    "ConfidencePolicyConfig",
    "ESCALATION_FEATURE_NAMES",
    "build_synthetic_escalation_records",
    "determine_synthetic_escalation_target",
    "filter_interactions_by_cutoff",
    "split_escalation_records_by_case",
    "validate_no_case_leakage",
    "enforce_escalation_boundary",
    "DEFAULT_MODEL_VERSION",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_TARGET_HORIZON_DAYS",
    "DEFAULT_THRESHOLD_LOW_MODERATE",
    "DEFAULT_THRESHOLD_MODERATE_HIGH",
    "DEFAULT_MIN_CONFIDENCE_THRESHOLD",
    "RiskLevel",
    "ProcessingStatus",
    "ResultSource",
    "Trajectory",
    "LABEL_DISCLAIMER",
    "SMOKE_TEST_DISCLAIMER",
]
