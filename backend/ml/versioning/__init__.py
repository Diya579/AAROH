"""Versioned model identity for inference outputs.

Every successful or low-confidence prediction must carry ``model_name`` and
``model_version``. Historical predictions must not be rewritten when a newer
artifact is introduced.
"""

from backend.ml.versioning.identity import ModelIdentity

__all__ = ["ModelIdentity"]
