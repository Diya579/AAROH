"""ML Feature Extraction layer (Slice 2.2).

Provides deterministic, multilingual text feature extraction consuming
Slice 2.1 ``PreprocessedInteraction`` records.
"""

from backend.ml.features.distress import extract_distress_indicators
from backend.ml.features.extractor import (
    TextFeatureExtractor,
    extract_text_features,
    extract_text_features_batch,
)
from backend.ml.features.help_seeking import extract_help_seeking_indicators
from backend.ml.features.lexical import extract_lexical_metrics
from backend.ml.features.lexicons import (
    DISTRESS_LEXICONS,
    HELP_SEEKING_LEXICONS,
    SAFETY_LEXICONS,
    find_matched_terms,
)
from backend.ml.features.safety import extract_safety_indicators
from backend.ml.features.types import (
    DistressIndicators,
    ExplanationEvidence,
    HelpSeekingIndicators,
    LexicalMetrics,
    SafetyIndicators,
    TextFeatures,
    TextQualityMetadata,
)

__all__ = [
    # Top-level feature container & orchestrator
    "TextFeatures",
    "TextFeatureExtractor",
    "extract_text_features",
    "extract_text_features_batch",
    # Dataclasses
    "DistressIndicators",
    "ExplanationEvidence",
    "HelpSeekingIndicators",
    "LexicalMetrics",
    "SafetyIndicators",
    "TextQualityMetadata",
    # Modular feature extraction routines
    "extract_distress_indicators",
    "extract_help_seeking_indicators",
    "extract_lexical_metrics",
    "extract_safety_indicators",
    # Centralized lexicons
    "DISTRESS_LEXICONS",
    "HELP_SEEKING_LEXICONS",
    "SAFETY_LEXICONS",
    "find_matched_terms",
]
