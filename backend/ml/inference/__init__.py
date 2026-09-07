"""Inference interface consumed by the application layer.

``infer`` returns a nested dict (Slice 1 backward compatibility).
``MLInferencePipeline`` provides the end-to-end orchestration pipeline (Slice 3.9).
"""

from __future__ import annotations

from backend.ml.inference.cache import InferenceCache
from backend.ml.inference.config import PipelineConfig
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    InferencePipelineError,
    InvalidInputError,
    ModelLoadError,
    PipelineExecutionError,
    VersionMismatchError,
)
from backend.ml.inference.pipeline import MLInferencePipeline
from backend.ml.inference.registry import ModelRegistry
from backend.ml.inference.service import infer

__all__ = [
    "infer",
    "MLInferencePipeline",
    "PipelineConfig",
    "ModelRegistry",
    "InferenceCache",
    "InferencePipelineError",
    "VersionMismatchError",
    "ModelLoadError",
    "ArtifactNotFoundError",
    "InvalidInputError",
    "PipelineExecutionError",
]
