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
    SafetyIndicators,
    TextFeatures,
    TextQualityMetadata,
)

__all__ = [
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
