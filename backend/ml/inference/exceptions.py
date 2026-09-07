"""Exception classes for the AAROH End-to-End ML Inference Pipeline (Slice 3.9)."""

from __future__ import annotations


class InferencePipelineError(Exception):
    """Base exception for all errors in the ML inference pipeline."""
    pass


class VersionMismatchError(InferencePipelineError):
    """Raised when an exported model or schema version does not match requirements."""
    pass


class ModelLoadError(InferencePipelineError):
    """Raised when an exported model fails to instantiate or load state."""
    pass


class ArtifactNotFoundError(InferencePipelineError):
    """Raised when required export files (weights, config, metadata, schemas) are missing."""
    pass


class InvalidInputError(InferencePipelineError):
    """Raised when the input record or history sequence fails structural validation."""
    pass


class PipelineExecutionError(InferencePipelineError):
    """Raised when pipeline stage execution or stage interface validation fails."""
    pass
