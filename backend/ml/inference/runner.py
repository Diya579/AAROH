"""Stage timing, structured tracing, and strict stage interface validation utilities."""

from __future__ import annotations

import logging
import math
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

from backend.ml.inference.exceptions import PipelineExecutionError

logger = logging.getLogger("aaroh.ml.inference")


class StageTimer:
    """High-precision timer recording stage and total pipeline execution durations in milliseconds."""

    def __init__(self) -> None:
        self.text_time_ms: float = 0.0
        self.audio_time_ms: float = 0.0
        self.fusion_time_ms: float = 0.0
        self.distress_time_ms: float = 0.0
        self.trajectory_time_ms: float = 0.0
        self.escalation_time_ms: float = 0.0
        self.total_pipeline_time_ms: float = 0.0
        self._start_total: Optional[float] = None

    def start_pipeline(self) -> None:
        self._start_total = time.perf_counter()

    def stop_pipeline(self) -> None:
        if self._start_total is not None:
            self.total_pipeline_time_ms = round(
                (time.perf_counter() - self._start_total) * 1000.0, 3
            )

    @contextmanager
    def measure(self, stage_name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 3)
            attr = f"{stage_name}_time_ms"
            if hasattr(self, attr):
                setattr(self, attr, duration_ms)

    def to_dict(self) -> Dict[str, float]:
        return {
            "text_time_ms": self.text_time_ms,
            "audio_time_ms": self.audio_time_ms,
            "fusion_time_ms": self.fusion_time_ms,
            "distress_time_ms": self.distress_time_ms,
            "trajectory_time_ms": self.trajectory_time_ms,
            "escalation_time_ms": self.escalation_time_ms,
            "total_pipeline_time_ms": self.total_pipeline_time_ms,
        }


class PipelineLogger:
    """Structured pipeline execution logger recording stages tagged by unique pipeline_run_id."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.trace: List[str] = []

    def log_stage(self, stage_msg: str) -> None:
        formatted = f"[{self.run_id}] {stage_msg}"
        self.trace.append(formatted)
        logger.info(formatted)


# =====================================================================
# Strict Stage Interface Validation
# =====================================================================

def validate_text_stage(output: Any) -> None:
    """Strictly validates text representation model outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'text_emotion': expected dict, got {type(output).__name__}"
        )
    if "emotion_embeddings" not in output or not isinstance(output["emotion_embeddings"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'text_emotion': missing or invalid 'emotion_embeddings'"
        )
    if not output["emotion_embeddings"]:
        raise PipelineExecutionError(
            "Stage validation failed for 'text_emotion': 'emotion_embeddings' is empty"
        )
    dim = len(output["emotion_embeddings"][0])
    if dim != 768:
        raise PipelineExecutionError(
            f"Stage validation failed for 'text_emotion': embedding dimension must be 768, got {dim}"
        )
    if "emotion_probabilities" not in output or not isinstance(output["emotion_probabilities"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'text_emotion': missing or invalid 'emotion_probabilities'"
        )


def validate_audio_stage(output: Any) -> None:
    """Strictly validates audio emotion model outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'audio_emotion': expected dict, got {type(output).__name__}"
        )
    if "audio_embeddings" not in output or not isinstance(output["audio_embeddings"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'audio_emotion': missing or invalid 'audio_embeddings'"
        )
    if not output["audio_embeddings"]:
        raise PipelineExecutionError(
            "Stage validation failed for 'audio_emotion': 'audio_embeddings' is empty"
        )
    dim = len(output["audio_embeddings"][0])
    if dim != 768:
        raise PipelineExecutionError(
            f"Stage validation failed for 'audio_emotion': embedding dimension must be 768, got {dim}"
        )
    if "audio_emotion_probabilities" not in output or not isinstance(output["audio_emotion_probabilities"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'audio_emotion': missing or invalid 'audio_emotion_probabilities'"
        )


def validate_fusion_stage(output: Any) -> None:
    """Strictly validates multimodal fusion outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'multimodal_fusion': expected dict, got {type(output).__name__}"
        )
    if "fused_embedding" not in output or not isinstance(output["fused_embedding"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'multimodal_fusion': missing or invalid 'fused_embedding'"
        )
    dim = len(output["fused_embedding"])
    if dim != 256:
        raise PipelineExecutionError(
            f"Stage validation failed for 'multimodal_fusion': fused_embedding dimension must be 256, got {dim}"
        )
    if "modality_weights" not in output or not isinstance(output["modality_weights"], dict):
        raise PipelineExecutionError(
            "Stage validation failed for 'multimodal_fusion': missing or invalid 'modality_weights'"
        )
    for mod in ("tabular", "text", "audio"):
        if mod not in output["modality_weights"]:
            raise PipelineExecutionError(
                f"Stage validation failed for 'multimodal_fusion': modality weight '{mod}' missing"
            )


def validate_distress_stage(output: Any) -> None:
    """Strictly validates dynamic distress model outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'distress': expected dict, got {type(output).__name__}"
        )
    if "distress_score" not in output or not isinstance(output["distress_score"], (int, float)):
        raise PipelineExecutionError(
            "Stage validation failed for 'distress': missing or non-numeric 'distress_score'"
        )
    score = float(output["distress_score"])
    if not (0.0 <= score <= 1.0):
        raise PipelineExecutionError(
            f"Stage validation failed for 'distress': distress_score must be in [0.0, 1.0], got {score}"
        )
    if "distress_level" not in output or output["distress_level"] not in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        raise PipelineExecutionError(
            f"Stage validation failed for 'distress': invalid distress_level '{output.get('distress_level')}'"
        )
    if "distress_embedding" not in output or not isinstance(output["distress_embedding"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'distress': missing or invalid 'distress_embedding'"
        )
    dim = len(output["distress_embedding"])
    if dim != 128:
        raise PipelineExecutionError(
            f"Stage validation failed for 'distress': distress_embedding dimension must be 128, got {dim}"
        )


def validate_trajectory_stage(output: Any) -> None:
    """Strictly validates longitudinal trajectory model outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'trajectory': expected dict, got {type(output).__name__}"
        )
    if "trajectory_score" not in output or not isinstance(output["trajectory_score"], (int, float)):
        raise PipelineExecutionError(
            "Stage validation failed for 'trajectory': missing or non-numeric 'trajectory_score'"
        )
    score = float(output["trajectory_score"])
    if not (-1.0 <= score <= 1.0):
        raise PipelineExecutionError(
            f"Stage validation failed for 'trajectory': trajectory_score must be in [-1.0, 1.0], got {score}"
        )
    valid_labels = {"STABLE", "IMPROVING", "WORSENING", "RAPIDLY_WORSENING"}
    if "trajectory_label" not in output or output["trajectory_label"] not in valid_labels:
        raise PipelineExecutionError(
            f"Stage validation failed for 'trajectory': invalid trajectory_label '{output.get('trajectory_label')}'"
        )
    if "trajectory_embedding" not in output or not isinstance(output["trajectory_embedding"], (list, tuple)):
        raise PipelineExecutionError(
            "Stage validation failed for 'trajectory': missing or invalid 'trajectory_embedding'"
        )
    dim = len(output["trajectory_embedding"])
    if dim != 128:
        raise PipelineExecutionError(
            f"Stage validation failed for 'trajectory': trajectory_embedding dimension must be 128, got {dim}"
        )


def validate_escalation_stage(output: Any) -> None:
    """Strictly validates escalation assessment model outputs."""
    if not isinstance(output, dict):
        raise PipelineExecutionError(
            f"Stage validation failed for 'escalation': expected dict, got {type(output).__name__}"
        )
    status = output.get("status")
    if hasattr(status, "value"):
        status = status.value

    # If abstained or insufficient data, escalation_probability and risk_level are None
    if status in ("INSUFFICIENT_DATA", "ABSTAINED"):
        if output.get("escalation_probability") is not None:
            raise PipelineExecutionError(
                f"Stage validation failed for 'escalation': status {status} must have null escalation_probability"
            )
        return

    if "escalation_probability" not in output or not isinstance(output["escalation_probability"], (int, float)):
        raise PipelineExecutionError(
            "Stage validation failed for 'escalation': missing or non-numeric 'escalation_probability'"
        )
    prob = float(output["escalation_probability"])
    if not (0.0 <= prob <= 1.0):
        raise PipelineExecutionError(
            f"Stage validation failed for 'escalation': escalation_probability must be in [0.0, 1.0], got {prob}"
        )
    risk_level = output.get("risk_level")
    if hasattr(risk_level, "value"):
        risk_level = risk_level.value
    if risk_level not in ("LOW", "MODERATE", "HIGH"):
        raise PipelineExecutionError(
            f"Stage validation failed for 'escalation': invalid risk_level '{risk_level}'"
        )
    if "confidence" not in output or not isinstance(output["confidence"], (int, float)):
        raise PipelineExecutionError(
            "Stage validation failed for 'escalation': missing or non-numeric 'confidence'"
        )
    if "explanation" not in output or not isinstance(output["explanation"], dict):
        raise PipelineExecutionError(
            "Stage validation failed for 'escalation': missing or invalid 'explanation'"
        )
    if "factors" not in output["explanation"] or "trend" not in output["explanation"]:
        raise PipelineExecutionError(
            "Stage validation failed for 'escalation': explanation missing 'factors' or 'trend'"
        )
