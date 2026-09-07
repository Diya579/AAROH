"""ML Preprocessing Package (Slice 2.1).

Provides clean, deterministic input validation, multilingual Unicode text
normalization, and safe missing-value handling for ML pipelines.

Existing extractors remain in ``backend/features/``. This package prepares
clean, structured inputs that subsequent ML feature extraction and models consume.
"""

from backend.ml.preprocessing.missingness import (
    assess_missingness,
    filter_available_features,
    is_missing,
)
from backend.ml.preprocessing.pipeline import (
    InteractionPreprocessingPipeline,
    preprocess_interaction,
    preprocess_interaction_batch,
)
from backend.ml.preprocessing.text import (
    clean_invisible_characters,
    detect_scripts,
    evaluate_text_quality,
    normalize_casing,
    normalize_unicode,
    normalize_whitespace,
    preprocess_text,
)
from backend.ml.preprocessing.types import (
    MissingnessReport,
    NormalizedText,
    PreprocessedInteraction,
    TextQualityMetrics,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from backend.ml.preprocessing.validation import (
    KNOWN_INTERACTION_FIELDS,
    KNOWN_LANGUAGES,
    validate_boolean_field,
    validate_case_id,
    validate_date,
    validate_interaction_payload,
    validate_language,
    validate_numeric_metric,
    validate_scale_rating,
    validate_text_field,
)

__all__ = [
    # Pipeline & Record
    "InteractionPreprocessingPipeline",
    "PreprocessedInteraction",
    "preprocess_interaction",
    "preprocess_interaction_batch",
    # Types
    "MissingnessReport",
    "NormalizedText",
    "TextQualityMetrics",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    # Text Utilities
    "clean_invisible_characters",
    "detect_scripts",
    "evaluate_text_quality",
    "normalize_casing",
    "normalize_unicode",
    "normalize_whitespace",
    "preprocess_text",
    # Validation Utilities
    "KNOWN_INTERACTION_FIELDS",
    "KNOWN_LANGUAGES",
    "validate_boolean_field",
    "validate_case_id",
    "validate_date",
    "validate_interaction_payload",
    "validate_language",
    "validate_numeric_metric",
    "validate_scale_rating",
    "validate_text_field",
    # Missingness Utilities
    "assess_missingness",
    "filter_available_features",
    "is_missing",
]
