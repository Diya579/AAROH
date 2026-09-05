"""Centralized Feature Registry and Schema Versioning (Slice 3.1).

Single source of truth for:
- Permanent feature indices, names, sources, and ordering (User Modification)
- Schema version (ML_INPUT_SCHEMA_VERSION)
- Explainability mapping: index → name → source
- Feature range validation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

# Schema version: any breaking change to feature ordering requires an increment
ML_INPUT_SCHEMA_VERSION = "3.1.0"


@dataclass(frozen=True)
class FeatureDefinition:
    """Immutable specification of a single feature in the ML input representation."""

    index: int
    name: str
    source: str
    description: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_optional: bool = False

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError(f"Feature index must be non-negative, got {self.index}")
        if not self.name or not self.name.strip():
            raise ValueError("Feature name cannot be empty")
        if not self.source or not self.source.strip():
            raise ValueError("Feature source cannot be empty")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"Feature '{self.name}' min_value ({self.min_value}) cannot exceed "
                f"max_value ({self.max_value})"
            )


# Permanent, frozen registry of all numerical features across all modalities.
# Indices are strictly contiguous from 0 to N-1.
FEATURE_REGISTRY: tuple[FeatureDefinition, ...] = (
    # --- Modality 1: Text Features (Slice 2.2) ---
    FeatureDefinition(0, "text_word_count", "text", "Total word count in text response", min_value=0.0),
    FeatureDefinition(1, "text_character_count", "text", "Total character count in text response", min_value=0.0),
    FeatureDefinition(2, "text_sentence_count", "text", "Total sentence count in text response", min_value=0.0),
    FeatureDefinition(3, "text_average_word_length", "text", "Average word length in characters", min_value=0.0),
    FeatureDefinition(4, "text_uppercase_ratio", "text", "Ratio of uppercase letters to total alphabetic characters", min_value=0.0, max_value=1.0),
    FeatureDefinition(5, "text_punctuation_ratio", "text", "Ratio of punctuation marks to total characters", min_value=0.0, max_value=1.0),
    FeatureDefinition(6, "text_fear", "text", "Lexicon-derived fear indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(7, "text_hopelessness", "text", "Lexicon-derived hopelessness indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(8, "text_isolation", "text", "Lexicon-derived isolation indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(9, "text_helplessness", "text", "Lexicon-derived helplessness indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(10, "text_intimidation", "text", "Lexicon-derived intimidation indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(11, "text_sadness", "text", "Lexicon-derived sadness indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(12, "text_anxiety", "text", "Lexicon-derived anxiety indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(13, "text_asking_for_help", "text", "Lexicon-derived asking for help indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(14, "text_requesting_support", "text", "Lexicon-derived requesting support indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(15, "text_emergency_language", "text", "Lexicon-derived emergency language indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(16, "text_urgency", "text", "Lexicon-derived urgency indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(17, "text_danger_related_wording", "text", "Lexicon-derived danger wording indicator", min_value=0.0, max_value=1.0),

    # --- Modality 2: Behavioural Features (Slice 2.3) ---
    FeatureDefinition(18, "behavioural_safety_distress", "behavioural", "Normalized inverted safety response (1.0 = unsafe)", min_value=0.0, max_value=1.0),
    FeatureDefinition(19, "behavioural_sleep_disturbance", "behavioural", "Normalized direct sleep disruption (1.0 = severe)", min_value=0.0, max_value=1.0),
    FeatureDefinition(20, "behavioural_fear_intensity", "behavioural", "Normalized direct fear level (1.0 = extreme fear)", min_value=0.0, max_value=1.0),
    FeatureDefinition(21, "behavioural_low_social_support", "behavioural", "Normalized inverted social support (1.0 = no support)", min_value=0.0, max_value=1.0),
    FeatureDefinition(22, "behavioural_help_requested", "behavioural", "Binary flag indicating help explicitly requested", min_value=0.0, max_value=1.0),
    FeatureDefinition(23, "behavioural_composite_distress", "behavioural", "Composite behavioural distress score", min_value=0.0, max_value=1.0),
    FeatureDefinition(24, "behavioural_change_from_previous", "behavioural", "Distress change from immediately preceding interaction", min_value=-1.0, max_value=1.0),
    FeatureDefinition(25, "behavioural_change_from_baseline", "behavioural", "Distress change from baseline interaction", min_value=-1.0, max_value=1.0),

    # --- Modality 3: Engagement Features (Slice 2.4) ---
    FeatureDefinition(26, "engagement_completed_checkin", "engagement", "Check-in completed indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(27, "engagement_missed_checkin", "engagement", "Check-in missed indicator", min_value=0.0, max_value=1.0),
    FeatureDefinition(28, "engagement_missed_checkin_streak", "engagement", "Consecutive missed check-ins streak count", min_value=0.0),
    FeatureDefinition(29, "engagement_checkin_consistency", "engagement", "Check-in consistency ratio across interaction history", min_value=0.0, max_value=1.0),
    FeatureDefinition(30, "engagement_response_delay", "engagement", "Response delay in days/hours for current interaction", min_value=0.0),
    FeatureDefinition(31, "engagement_average_response_delay", "engagement", "Average response delay across interaction history", min_value=0.0),
    FeatureDefinition(32, "engagement_response_frequency", "engagement", "Mean interval between interactions in days", min_value=0.0),
    FeatureDefinition(33, "engagement_engagement_drop", "engagement", "Drop in adherence relative to prior window", min_value=0.0, max_value=1.0),
    FeatureDefinition(34, "engagement_recent_activity_count", "engagement", "Number of interactions within recent activity window", min_value=0.0),
    FeatureDefinition(35, "engagement_inactivity_duration", "engagement", "Days elapsed since last recorded interaction", min_value=0.0),
    FeatureDefinition(36, "engagement_score", "engagement", "Interaction adherence/reliability score", min_value=0.0, max_value=1.0),
    FeatureDefinition(37, "engagement_change_from_previous", "engagement", "Engagement adherence change from previous interaction", min_value=-1.0, max_value=1.0),
    FeatureDefinition(38, "engagement_change_from_baseline", "engagement", "Engagement adherence change from baseline interaction", min_value=-1.0, max_value=1.0),

    # --- Modality 4: Longitudinal Features (Slice 2.5) ---
    FeatureDefinition(39, "longitudinal_observation_count", "longitudinal", "Total interactions observed in longitudinal timeline", min_value=1.0),
    FeatureDefinition(40, "longitudinal_history_span_days", "longitudinal", "Total days spanned from first observation to current", min_value=0.0),
    FeatureDefinition(41, "longitudinal_current_distress", "longitudinal", "Current composite distress score", min_value=0.0, max_value=1.0),
    FeatureDefinition(42, "longitudinal_baseline_distress", "longitudinal", "Baseline composite distress score", min_value=0.0, max_value=1.0),
    FeatureDefinition(43, "longitudinal_previous_distress", "longitudinal", "Immediately preceding composite distress score", min_value=0.0, max_value=1.0),
    FeatureDefinition(44, "longitudinal_delta_from_baseline", "longitudinal", "Distress delta relative to baseline observation", min_value=-1.0, max_value=1.0),
    FeatureDefinition(45, "longitudinal_delta_from_previous", "longitudinal", "Distress delta relative to immediately preceding observation", min_value=-1.0, max_value=1.0),
    FeatureDefinition(46, "longitudinal_distress_velocity", "longitudinal", "Daily rate of change (slope) of composite distress"),
    FeatureDefinition(47, "longitudinal_distress_acceleration", "longitudinal", "Second derivative of composite distress rate"),
    FeatureDefinition(48, "longitudinal_distress_volatility", "longitudinal", "Sample standard deviation of observed distress scores", min_value=0.0),
    FeatureDefinition(49, "longitudinal_peak_distress", "longitudinal", "Highest observed distress score in timeline", min_value=0.0, max_value=1.0),
    FeatureDefinition(50, "longitudinal_trough_distress", "longitudinal", "Lowest observed distress score in timeline", min_value=0.0, max_value=1.0),
    FeatureDefinition(51, "longitudinal_sustained_distress_count", "longitudinal", "Consecutive interactions with distress >= high threshold", min_value=0.0),

    # --- Modality 5: Voice Features (Locked Voice contract, Optional) ---
    FeatureDefinition(52, "voice_speech_rate", "voice", "Speaking rate in syllables/words per second", min_value=0.0, is_optional=True),
    FeatureDefinition(53, "voice_pause_ratio", "voice", "Ratio of silent pause duration to total speech duration", min_value=0.0, max_value=1.0, is_optional=True),
    FeatureDefinition(54, "voice_response_latency", "voice", "Acoustic latency between prompt and verbal response", min_value=0.0, is_optional=True),
    FeatureDefinition(55, "voice_pitch_variability", "voice", "Fundamental frequency variability (pitch variation)", min_value=0.0, is_optional=True),
    FeatureDefinition(56, "voice_energy_variation", "voice", "Acoustic energy / intensity variability", min_value=0.0, is_optional=True),
    FeatureDefinition(57, "voice_audio_quality", "voice", "Signal quality score for the captured audio", min_value=0.0, max_value=1.0, is_optional=True),
    FeatureDefinition(58, "voice_asr_confidence", "voice", "Confidence score of the speech transcription", min_value=0.0, max_value=1.0, is_optional=True),
    FeatureDefinition(59, "voice_baseline_deviation", "voice", "Deviation of acoustic features from speaker baseline", min_value=0.0, is_optional=True),
)

# Registry Lookups (O(1))
FEATURE_NAME_TO_INDEX: Mapping[str, int] = {f.name: f.index for f in FEATURE_REGISTRY}
FEATURE_INDEX_TO_NAME: Mapping[int, str] = {f.index: f.name for f in FEATURE_REGISTRY}
FEATURE_SOURCE_MAP: Mapping[str, str] = {f.name: f.source for f in FEATURE_REGISTRY}
FEATURE_NAMES: tuple[str, ...] = tuple(f.name for f in FEATURE_REGISTRY)
FEATURE_SOURCES: tuple[str, ...] = tuple(f.source for f in FEATURE_REGISTRY)
TOTAL_FEATURES_COUNT: int = len(FEATURE_REGISTRY)

# Validation: ensure registry invariants are permanently held
assert len(FEATURE_NAME_TO_INDEX) == len(FEATURE_REGISTRY), "Duplicate feature names in registry"
assert all(FEATURE_REGISTRY[i].index == i for i in range(len(FEATURE_REGISTRY))), (
    "Feature registry indices must be contiguous from 0 to N-1"
)


def get_feature_definition(name_or_index: str | int) -> FeatureDefinition:
    """Retrieves feature definition by either its unique name or index."""
    if isinstance(name_or_index, int):
        if not 0 <= name_or_index < len(FEATURE_REGISTRY):
            raise IndexError(
                f"Feature index {name_or_index} out of range [0, {len(FEATURE_REGISTRY) - 1}]"
            )
        return FEATURE_REGISTRY[name_or_index]
    elif isinstance(name_or_index, str):
        idx = FEATURE_NAME_TO_INDEX.get(name_or_index)
        if idx is None:
            raise KeyError(f"Feature name '{name_or_index}' not found in feature registry")
        return FEATURE_REGISTRY[idx]
    else:
        raise TypeError(f"Expected str or int, got {type(name_or_index).__name__}")


def validate_feature_value(name: str, value: Optional[float]) -> None:
    """Validates that a feature value conforms to the declared ranges in the registry.

    Preserves None != 0 (None values are not rejected).
    Raises ValueError on out-of-range values.
    """
    if value is None:
        return

    defn = get_feature_definition(name)
    if defn.min_value is not None and value < defn.min_value:
        raise ValueError(
            f"Feature '{name}' value {value} is below minimum allowed {defn.min_value}"
        )
    if defn.max_value is not None and value > defn.max_value:
        raise ValueError(
            f"Feature '{name}' value {value} exceeds maximum allowed {defn.max_value}"
        )
