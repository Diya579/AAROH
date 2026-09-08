"""Model Registry managing versions, directory mapping, artifact verification, and compatibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Set, Tuple

from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_NEURAL,
    NEURAL_EXECUTION_MODES,
    VALID_EXECUTION_MODES,
    is_execution_mode_compatible,
)
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    ExecutionModeError,
    VersionMismatchError,
)

# Canonical expected versions
DEFAULT_MODEL_VERSIONS: Dict[str, str] = {
    "text": "aaroh-text-v1",
    "audio": "aaroh-audio-v1",
    "fusion": "aaroh-fusion-v1",
    "distress": "aaroh-distress-v1",
    "trajectory": "aaroh-trajectory-v1",
    "escalation": "aaroh-escalation-v1",
}

# Directory naming under models/
MODEL_DIRECTORIES: Dict[str, str] = {
    "text": "text_emotion",
    "audio": "audio_emotion",
    "fusion": "multimodal_fusion",
    "distress": "distress",
    "trajectory": "trajectory",
    "escalation": "escalation",
}

# Semantic version compatibility aliases (v1 canonical name to exported semantic versions)
VERSION_ALIASES: Dict[str, Set[str]] = {
    "aaroh-text-v1": {"aaroh-text-v1", "1.0.0"},
    "aaroh-audio-v1": {"aaroh-audio-v1", "1.0.0"},
    "aaroh-fusion-v1": {"aaroh-fusion-v1", "1.0.0"},
    "aaroh-distress-v1": {"aaroh-distress-v1"},
    "aaroh-trajectory-v1": {"aaroh-trajectory-v1"},
    "aaroh-escalation-v1": {"aaroh-escalation-v1"},
}

# Required artifact files per model key
REQUIRED_FILES: Dict[str, Tuple[str, ...]] = {
    "text": ("config.json", "metadata.json", "pytorch_model.bin", "label_mapping.json"),
    "audio": ("config.json", "metadata.json", "pytorch_model.bin", "label_mapping.json"),
    "fusion": ("config.json", "metadata.json", "weights", "modality_schema.json"),
    "distress": ("config.json", "metadata.json", "weights", "label_mapping.json"),
    "trajectory": ("config.json", "metadata.json", "weights", "label_mapping.json"),
    "escalation": ("config.json", "metadata.json", "weights", "label_mapping.json"),
}


def compute_file_sha256(path: Path) -> str:
    """Computes SHA-256 checksum of an exported artifact file."""
    if not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelRegistry:
    """Central registry defining expected model versions, paths, and compatibility rules."""

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        expected_versions: Optional[Mapping[str, str]] = None,
        models_dir: Optional[Path | str] = None,
    ) -> None:
        self.base_dir = Path(models_dir or base_dir or "models").resolve()
        self.expected_versions = dict(expected_versions or DEFAULT_MODEL_VERSIONS)

    def get_model_path(self, model_key: str) -> Path:
        """Returns filesystem directory path for a model key."""
        if model_key not in MODEL_DIRECTORIES:
            raise KeyError(f"Unknown model key: '{model_key}'. Allowed: {list(MODEL_DIRECTORIES.keys())}")
        return self.base_dir / MODEL_DIRECTORIES[model_key]

    def verify_artifacts(self, model_key: str) -> Dict[str, str]:
        """Verifies that all required artifact files exist and returns file checksums.

        Raises
        ------
        ArtifactNotFoundError
            If any required artifact file is missing.
        """
        model_dir = self.get_model_path(model_key)
        if not model_dir.is_dir():
            raise ArtifactNotFoundError(
                f"Model directory does not exist for '{model_key}': {model_dir}"
            )

        required = REQUIRED_FILES.get(model_key, ("config.json", "metadata.json"))
        checksums: Dict[str, str] = {}

        for filename in required:
            filepath = model_dir / filename
            if not filepath.exists():
                raise ArtifactNotFoundError(
                    f"Required artifact '{filename}' missing for model '{model_key}' in {model_dir}"
                )
            checksums[filename] = compute_file_sha256(filepath)

        return checksums

    def validate_metadata(
        self,
        model_key: str,
        metadata: Dict[str, Any],
        required_execution_mode: Optional[str] = "FALLBACK",
        execution_mode: Optional[str] = None,
    ) -> None:
        """Validates that loaded metadata matches expected model version, dataset version, and execution mode.

        Raises
        ------
        VersionMismatchError
            If version or compatibility assertion fails.
        """
        if execution_mode is not None:
            required_execution_mode = execution_mode
        if not isinstance(metadata, dict):
            raise VersionMismatchError(
                f"Corrupt metadata for '{model_key}': expected JSON dict, got {type(metadata).__name__}"
            )

        model_version = metadata.get("model_version")
        if not model_version:
            raise VersionMismatchError(
                f"Model '{model_key}' metadata missing 'model_version' field"
            )

        expected_version = self.expected_versions.get(model_key)
        if expected_version:
            allowed_aliases = VERSION_ALIASES.get(expected_version, {expected_version})
            if model_version not in allowed_aliases and model_version != expected_version:
                raise VersionMismatchError(
                    f"Version mismatch for model '{model_key}': expected '{expected_version}' "
                    f"(or aliases {allowed_aliases}), got '{model_version}'"
                )

        # Validate required execution mode
        if required_execution_mode is not None:
            if required_execution_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Invalid required_execution_mode '{required_execution_mode}'. "
                    f"Must be one of {sorted(VALID_EXECUTION_MODES)}"
                )

        # Validate execution mode if present in metadata
        if "execution_mode" in metadata:
            artifact_mode = metadata["execution_mode"]
            if artifact_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Model '{model_key}' artifact specifies invalid execution_mode '{artifact_mode}'. "
                    f"Must be one of {sorted(VALID_EXECUTION_MODES)}"
                )
            if required_execution_mode:
                if not is_execution_mode_compatible(required_execution_mode, artifact_mode):
                    raise ExecutionModeError(
                        f"Execution mode mismatch for model '{model_key}': runtime is configured for "
                        f"'{required_execution_mode}', but artifact was built for '{artifact_mode}'. "
                        f"Incompatible execution modes cannot proceed."
                    )

        # Validate representation consistency where specified in metadata
        rep_type = metadata.get("training_representation") or metadata.get("upstream_representation") or metadata.get("representation")
        if rep_type is not None and required_execution_mode:
            is_req_fallback = (required_execution_mode == EXECUTION_MODE_FALLBACK)
            rep_lower = str(rep_type).lower()
            is_rep_fallback = ("fallback" in rep_lower or "deterministic" in rep_lower or "hash" in rep_lower or "heuristic" in rep_lower)
            is_rep_neural = ("neural" in rep_lower or "transformer" in rep_lower) and not is_rep_fallback
            if is_req_fallback and is_rep_neural:
                raise ExecutionModeError(
                    f"Representation mismatch for model '{model_key}': runtime is in FALLBACK mode, "
                    f"but artifact was trained with neural representation '{rep_type}'."
                )
            if not is_req_fallback and is_rep_fallback:
                raise ExecutionModeError(
                    f"Representation mismatch for model '{model_key}': runtime is in '{required_execution_mode}' "
                    f"neural mode, but artifact was trained with deterministic fallback representation '{rep_type}'."
                )

    def get_all_artifact_checksums(self) -> Dict[str, Dict[str, str]]:
        """Returns nested dict of artifact checksums across all registered models."""
        all_checksums: Dict[str, Dict[str, str]] = {}
        for key in MODEL_DIRECTORIES:
            all_checksums[key] = self.verify_artifacts(key)
        return all_checksums
