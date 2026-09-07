"""ML Feature Extraction layer (Slice 2.2, Slice 2.3 & Slice 2.4).

Provides deterministic text, behavioural, and engagement feature extraction consuming
Slice 2.1 ``PreprocessedInteraction`` records.
"""

from backend.ml.features.behavioural import (
    BehaviouralFeatureExtractor,
    extract_behavioural_features,
    extract_behavioural_features_batch,
)
from backend.ml.features.definitions import (
    ALL_BEHAVIOURAL_INPUT_FIELDS,
    HIGH_DISTRESS_THRESHOLD,
    MAX_LIKERT_RATING,
    MIN_LIKERT_RATING,
    NOTABLE_SHIFT_THRESHOLD,
    BehaviouralMetric,
    normalize_likert_rating,
)
from backend.ml.features.distress import extract_distress_indicators
from backend.ml.features.engagement import (
    EngagementFeatureExtractor,
    extract_engagement_features,
    extract_engagement_features_batch,
)
from backend.ml.features.engagement_definitions import (
    DEFAULT_LONG_RESPONSE_DELAY_DAYS,
    DEFAULT_LOW_CONSISTENCY_THRESHOLD,
    DEFAULT_MISSED_CHECKIN_ALERT_STREAK,
    DEFAULT_NOTABLE_ENGAGEMENT_DROP,
    DEFAULT_RECENT_ACTIVITY_WINDOW_DAYS,
    DEFAULT_TREND_SHIFT_THRESHOLD,
    EngagementConfig,
    EngagementMetric,
    EngagementTrend,
)
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
from backend.ml.features.longitudinal import (
    LongitudinalFeatureExtractor,
    compute_interaction_distress,
    extract_longitudinal_features,
    extract_longitudinal_features_batch,
)
from backend.ml.features.longitudinal_definitions import (
    DEFAULT_HIGH_DISTRESS_THRESHOLD as DEFAULT_LONGITUDINAL_HIGH_DISTRESS_THRESHOLD,
    DEFAULT_MIN_OBSERVATIONS_FOR_TREND,
    DEFAULT_MODERATE_VELOCITY_THRESHOLD,
    DEFAULT_NOTABLE_SHIFT_THRESHOLD as DEFAULT_LONGITUDINAL_NOTABLE_SHIFT_THRESHOLD,
    DEFAULT_RAPID_SHIFT_THRESHOLD,
    DEFAULT_RAPID_VELOCITY_THRESHOLD,
    DEFAULT_VOLATILITY_ALERT_THRESHOLD,
    LongitudinalConfig,
    LongitudinalMetric,
    LongitudinalTrend,
    classify_longitudinal_trend,
)
from backend.ml.features.assembly import (
    MLInput,
    MLInputAssembler,
    assemble_ml_input,
    assemble_ml_input_batch,
)
from backend.ml.features.registry import (
    FEATURE_INDEX_TO_NAME,
    FEATURE_NAME_TO_INDEX,
    FEATURE_NAMES,
    FEATURE_REGISTRY,
    FEATURE_SOURCE_MAP,
    FEATURE_SOURCES,
    ML_INPUT_SCHEMA_VERSION,
    TOTAL_FEATURES_COUNT,
    FeatureDefinition,
    get_feature_definition,
    validate_feature_value,
)
from backend.ml.features.safety import extract_safety_indicators
from backend.ml.features.types import (
    BehaviouralEvidence,
    BehaviouralFeatures,
    DistressIndicators,
    EngagementEvidence,
    EngagementFeatures,
    ExplanationEvidence,
    HelpSeekingIndicators,
    LexicalMetrics,
    LongitudinalEvidence,
    LongitudinalFeatures,
    SafetyIndicators,
    TextFeatures,
    TextQualityMetadata,
)
from backend.ml.features.voice import VoiceFeatures

__all__ = [
    # ML Input Assembly (Slice 3.1)
    "MLInput",
    "MLInputAssembler",
    "assemble_ml_input",
    "assemble_ml_input_batch",
    "VoiceFeatures",
    "FeatureDefinition",
    "FEATURE_REGISTRY",
    "FEATURE_NAMES",
    "FEATURE_SOURCES",
    "FEATURE_NAME_TO_INDEX",
    "FEATURE_INDEX_TO_NAME",
    "FEATURE_SOURCE_MAP",
    "ML_INPUT_SCHEMA_VERSION",
    "TOTAL_FEATURES_COUNT",
    "get_feature_definition",
    "validate_feature_value",
    # Top-level feature containers & orchestrators
    "TextFeatures",
    "TextFeatureExtractor",
    "extract_text_features",
    "extract_text_features_batch",
    "BehaviouralFeatures",
    "BehaviouralEvidence",
    "BehaviouralFeatureExtractor",
    "extract_behavioural_features",
    "extract_behavioural_features_batch",
    "EngagementFeatures",
    "EngagementEvidence",
    "EngagementFeatureExtractor",
    "extract_engagement_features",
    "extract_engagement_features_batch",
    # Longitudinal feature containers & extractors (Slice 2.5)
    "LongitudinalFeatures",
    "LongitudinalEvidence",
    "LongitudinalFeatureExtractor",
    "compute_interaction_distress",
    "extract_longitudinal_features",
    "extract_longitudinal_features_batch",
    # Longitudinal definitions & configuration
    "LongitudinalTrend",
    "LongitudinalMetric",
    "LongitudinalConfig",
    "classify_longitudinal_trend",
    "DEFAULT_MIN_OBSERVATIONS_FOR_TREND",
    "DEFAULT_RAPID_SHIFT_THRESHOLD",
    "DEFAULT_LONGITUDINAL_NOTABLE_SHIFT_THRESHOLD",
    "DEFAULT_LONGITUDINAL_HIGH_DISTRESS_THRESHOLD",
    "DEFAULT_RAPID_VELOCITY_THRESHOLD",
    "DEFAULT_MODERATE_VELOCITY_THRESHOLD",
    "DEFAULT_VOLATILITY_ALERT_THRESHOLD",
    # Engagement definitions & configuration
    "EngagementTrend",
    "EngagementMetric",
    "EngagementConfig",
    "DEFAULT_LONG_RESPONSE_DELAY_DAYS",
    "DEFAULT_MISSED_CHECKIN_ALERT_STREAK",
    "DEFAULT_LOW_CONSISTENCY_THRESHOLD",
    "DEFAULT_NOTABLE_ENGAGEMENT_DROP",
    "DEFAULT_RECENT_ACTIVITY_WINDOW_DAYS",
    "DEFAULT_TREND_SHIFT_THRESHOLD",
    # Behavioural definitions & constants
    "BehaviouralMetric",
    "MIN_LIKERT_RATING",
    "MAX_LIKERT_RATING",
    "NOTABLE_SHIFT_THRESHOLD",
    "HIGH_DISTRESS_THRESHOLD",
    "ALL_BEHAVIOURAL_INPUT_FIELDS",
    "normalize_likert_rating",
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
