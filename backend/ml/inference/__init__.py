"""Inference interface consumed by the application layer.

``infer`` returns a nested dict and must not persist to PostgreSQL.
"""

from backend.ml.inference.service import infer

__all__ = ["infer"]
