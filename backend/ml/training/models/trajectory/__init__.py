"""AAROH Longitudinal Trajectory Model Package (Slice 3.7).

Exported Symbols:
- LongitudinalTrajectoryModel: Dual-mode trajectory progression network
- TrajectoryInputRecord: Container for multimodal interaction timestep
- CaseTrajectory: Chronologically sorted interaction sequence with fixed-window support
- TrajectoryDataset: Batch iterator for case trajectories
- Synthetic trajectory generators and case-level splitters
- Clinical boundary enforcement helper
- Label constants and execution modes
"""

from backend.ml.training.models.common import enforce_trajectory_boundary
from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    DISTRESS_EMBEDDING_DIM,
    DISTRESS_LEVEL_DIM,
    DISTRESS_SCORE_DIM,
    FUSED_EMBEDDING_DIM,
    ID_TO_LABEL,
    LABEL_DISCLAIMER,
    LABEL_IMPROVING,
    LABEL_RAPIDLY_WORSENING,
    LABEL_STABLE,
    LABEL_TO_ID,
    LABEL_WORSENING,
    SMOKE_TEST_DISCLAIMER,
    TIMESTEP_INPUT_DIM,
    TRAJECTORY_DEFINITIONS,
    TRAJECTORY_EMBEDDING_DIM,
    TRAJECTORY_INTERNAL_SCORES,
    VALID_TRAJECTORY_LABELS,
    CaseTrajectory,
    TrajectoryDataset,
    TrajectoryInputRecord,
    TrajectoryLabel,
    build_synthetic_trajectories,
    determine_synthetic_trajectory_label,
    split_trajectories_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.trajectory.explainability import (
    STATE_IMPROVING,
    STATE_RAPIDLY_WORSENING,
    STATE_RECOVERING,
    STATE_SLOWLY_WORSENING,
    STATE_STABLE,
    TrajectoryEvidence,
    calculate_trajectory_metrics,
    determine_trajectory_state_and_confidence,
    generate_trajectory_evidence,
    generate_trajectory_reasons,
)
from backend.ml.training.models.trajectory.inference import (
    TrajectoryInferencePipeline,
)
from backend.ml.training.models.trajectory.model import (
    DEFAULT_MODEL_VERSION,
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    VALID_EXECUTION_MODES,
    LongitudinalTrajectoryModel,
)

__all__ = [
    "LongitudinalTrajectoryModel",
    "TrajectoryInferencePipeline",
    "TrajectoryInputRecord",
    "CaseTrajectory",
    "TrajectoryDataset",
    "TrajectoryLabel",
    "TrajectoryEvidence",
    "calculate_trajectory_metrics",
    "determine_trajectory_state_and_confidence",
    "generate_trajectory_evidence",
    "generate_trajectory_reasons",
    "STATE_IMPROVING",
    "STATE_STABLE",
    "STATE_SLOWLY_WORSENING",
    "STATE_RAPIDLY_WORSENING",
    "STATE_RECOVERING",
    "TRAJECTORY_INTERNAL_SCORES",
    "TRAJECTORY_DEFINITIONS",
    "build_synthetic_trajectories",
    "determine_synthetic_trajectory_label",
    "split_trajectories_by_case",
    "validate_no_case_leakage",
    "enforce_trajectory_boundary",
    "TIMESTEP_INPUT_DIM",
    "TRAJECTORY_EMBEDDING_DIM",
    "DEFAULT_HISTORY_WINDOW",
    "DEFAULT_MODEL_VERSION",
    "LABEL_STABLE",
    "LABEL_IMPROVING",
    "LABEL_WORSENING",
    "LABEL_RAPIDLY_WORSENING",
    "VALID_TRAJECTORY_LABELS",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
    "LABEL_DISCLAIMER",
    "SMOKE_TEST_DISCLAIMER",
    "EXECUTION_MODE_FALLBACK",
    "EXECUTION_MODE_PYTORCH_FROZEN",
    "EXECUTION_MODE_PYTORCH_FINETUNE",
    "VALID_EXECUTION_MODES",
]
