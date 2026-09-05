"""Versioned configuration for the AAROH End-to-End ML Inference Pipeline (Slice 3.9)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


@dataclass
class PipelineConfig:
    """Centralized, versioned configuration controlling the ML inference pipeline."""

    pipeline_version: str = "aaroh-pipeline-v1"
    pipeline_build: str = "2026.09.06"
    default_execution_mode: str = "FALLBACK"
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

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to standard dictionary."""
        return asdict(self)

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
