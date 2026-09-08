"""Versioned configuration for the AAROH End-to-End ML Inference Pipeline (Slice 3.9)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional, Set

from backend.ml.inference.exceptions import ExecutionModeError

# Canonical execution modes
EXECUTION_MODE_FALLBACK = "FALLBACK"
EXECUTION_MODE_NEURAL = "NEURAL"
EXECUTION_MODE_PYTORCH_FROZEN = "PYTORCH_FROZEN"
EXECUTION_MODE_PYTORCH_FINETUNE = "PYTORCH_FINETUNE"

VALID_EXECUTION_MODES: Set[str] = {
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_NEURAL,
    EXECUTION_MODE_PYTORCH_FROZEN,
    EXECUTION_MODE_PYTORCH_FINETUNE,
}

NEURAL_EXECUTION_MODES: Set[str] = {
    EXECUTION_MODE_NEURAL,
    EXECUTION_MODE_PYTORCH_FROZEN,
    EXECUTION_MODE_PYTORCH_FINETUNE,
}


def is_execution_mode_compatible(runtime_mode: str, artifact_mode: str) -> bool:
    """Evaluates whether runtime execution mode is compatible with artifact execution mode.

    Semantic Compatibility Invariants:
    1. Exact matches are always compatible:
       - FALLBACK + FALLBACK -> True
       - NEURAL + NEURAL -> True
       - PYTORCH_FROZEN + PYTORCH_FROZEN -> True
       - PYTORCH_FINETUNE + PYTORCH_FINETUNE -> True
    2. Deterministic FALLBACK and Neural family are strictly mutually exclusive:
       - FALLBACK + any Neural mode -> False
       - any Neural mode + FALLBACK -> False
    3. Neural family interoperability:
       - NEURAL runtime is the umbrella neural mode, compatible with NEURAL, PYTORCH_FROZEN,
         and PYTORCH_FINETUNE artifacts.
       - PYTORCH_FROZEN runtime is compatible with PYTORCH_FROZEN and generic NEURAL artifacts.
       - PYTORCH_FINETUNE runtime strictly requires PYTORCH_FINETUNE artifacts (cannot run against
         frozen or generic pretrained backbones).
       - PYTORCH_FROZEN runtime strictly rejects PYTORCH_FINETUNE artifacts.
    """
    if runtime_mode == artifact_mode:
        return True

    # FALLBACK is strictly isolated from all neural modes
    if runtime_mode == EXECUTION_MODE_FALLBACK or artifact_mode == EXECUTION_MODE_FALLBACK:
        return False

    # Umbrella NEURAL runtime accepts any neural artifact
    if runtime_mode == EXECUTION_MODE_NEURAL and artifact_mode in NEURAL_EXECUTION_MODES:
        return True

    # PYTORCH_FROZEN runtime accepts generic NEURAL (which uses frozen weights by default)
    if runtime_mode == EXECUTION_MODE_PYTORCH_FROZEN and artifact_mode == EXECUTION_MODE_NEURAL:
        return True

    # All other cross-mode combinations (e.g. FROZEN vs FINETUNE) are incompatible
    return False


_UNSET = "___UNSET___"


@dataclass
class PipelineConfig:
    """Centralized, versioned configuration controlling the ML inference pipeline."""

    pipeline_version: str = "aaroh-pipeline-v1"
    pipeline_build: str = "2026.09.06"
    default_execution_mode: str = "FALLBACK"
    execution_mode: Any = _UNSET
    seed: int = 42
    warmup_on_load: bool = True
    warmup_dummy_samples: int = 1
    enable_cache: bool = True
    max_history_window: int = 10
    default_target_horizon_days: int = 7
    strict_stage_validation: bool = True
    export_manifest: bool = True
    manifest_path: str = "models/pipeline_manifest.json"
    feature_schema_version: str = "1.0"
    contract_version: str = "1.0"

    def __post_init__(self) -> None:
        """Validates configuration parameters upon instantiation."""
        if self.execution_mode != _UNSET:
            if not self.execution_mode or self.execution_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Invalid execution mode '{self.execution_mode}'. "
                    f"Must be one of {sorted(VALID_EXECUTION_MODES)}"
                )
            self.default_execution_mode = self.execution_mode

        if not self.default_execution_mode or self.default_execution_mode not in VALID_EXECUTION_MODES:
            raise ExecutionModeError(
                f"Invalid execution mode '{self.default_execution_mode}'. "
                f"Must be one of {sorted(VALID_EXECUTION_MODES)}"
            )

    @property
    def target_horizon_days(self) -> int:
        """Alias for default_target_horizon_days."""
        return self.default_target_horizon_days

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to standard dictionary."""
        d = asdict(self)
        if d.get("execution_mode") == _UNSET:
            del d["execution_mode"]
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PipelineConfig:
        """Instantiate configuration from dictionary or mapping."""
        valid_keys = {
            "pipeline_version",
            "pipeline_build",
            "default_execution_mode",
            "seed",
            "warmup_on_load",
            "warmup_dummy_samples",
            "enable_cache",
            "max_history_window",
            "default_target_horizon_days",
            "strict_stage_validation",
            "export_manifest",
            "manifest_path",
            "feature_schema_version",
            "contract_version",
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
