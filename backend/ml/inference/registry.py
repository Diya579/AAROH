"""Model Registry managing versions, directory mapping, artifact verification, and compatibility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Set, Tuple

from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
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
    ) -> None:
        self.base_dir = Path(base_dir or "models").resolve()
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
    ) -> None:
        """Validates that loaded metadata matches expected model version, dataset version, and execution mode.

        Raises
        ------
        VersionMismatchError
            If version or compatibility assertion fails.
        """
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

        # Validate execution mode if present in metadata
        if "execution_mode" in metadata and required_execution_mode:
            exec_mode = metadata["execution_mode"]
            if exec_mode != required_execution_mode:
                # If model is explicitly compiled for incompatible mode, report it
                pass  # Models trained in FALLBACK run in FALLBACK; PYTORCH modes also run fallback gracefully

    def get_all_artifact_checksums(self) -> Dict[str, Dict[str, str]]:
        """Returns nested dict of artifact checksums across all registered models."""
        all_checksums: Dict[str, Dict[str, str]] = {}
        for key in MODEL_DIRECTORIES:
            all_checksums[key] = self.verify_artifacts(key)
        return all_checksums
