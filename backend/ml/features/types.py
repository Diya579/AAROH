"""Data types and schemas for the ML Text Feature Extraction layer (Slice 2.2).

Follows the immutable frozen dataclass pattern established in ``backend/ml/contract.py``.
Provides strong typing, explicit serialization, and strict preservation of missing values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class LexicalMetrics:
    """Basic lexical statistics computed from text."""

    word_count: int
    character_count: int
    sentence_count: int
    average_word_length: float
    uppercase_ratio: float
    punctuation_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "word_count": self.word_count,
            "character_count": self.character_count,
            "sentence_count": self.sentence_count,
            "average_word_length": self.average_word_length,
            "uppercase_ratio": self.uppercase_ratio,
            "punctuation_ratio": self.punctuation_ratio,
        }


@dataclass(frozen=True)
class DistressIndicators:
    """Observable distress indicators in [0.0, 1.0]. Not clinical diagnoses."""

    fear: float
    hopelessness: float
    isolation: float
    helplessness: float
    intimidation: float
    sadness: float
    anxiety: float

    def to_dict(self) -> dict[str, float]:
        return {
            "fear": self.fear,
            "hopelessness": self.hopelessness,
            "isolation": self.isolation,
            "helplessness": self.helplessness,
            "intimidation": self.intimidation,
            "sadness": self.sadness,
            "anxiety": self.anxiety,
        }


@dataclass(frozen=True)
class HelpSeekingIndicators:
    """Observable help-seeking indicators in [0.0, 1.0]."""

    asking_for_help: float
    requesting_support: float
    emergency_language: float

    def to_dict(self) -> dict[str, float]:
        return {
            "asking_for_help": self.asking_for_help,
            "requesting_support": self.requesting_support,
            "emergency_language": self.emergency_language,
        }


@dataclass(frozen=True)
class SafetyIndicators:
    """Observable safety and urgency indicators in [0.0, 1.0]."""

    urgency: float
    danger_related_wording: float

    def to_dict(self) -> dict[str, float]:
        return {
            "urgency": self.urgency,
            "danger_related_wording": self.danger_related_wording,
        }


@dataclass(frozen=True)
class TextQualityMetadata:
    """Reused linguistic quality metadata from Slice 2.1 preprocessing."""

    language: str
    detected_scripts: tuple[str, ...]
    has_multilingual_chars: bool
    is_empty: bool
    is_very_short: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "detected_scripts": list(self.detected_scripts),
            "has_multilingual_chars": self.has_multilingual_chars,
            "is_empty": self.is_empty,
            "is_very_short": self.is_very_short,
        }


@dataclass(frozen=True)
class ExplanationEvidence:
    """Matched keywords and phrases for explainability (User Modification 1).

    Preserves exact terms that triggered feature indicators. Does not alter numeric
    scores; stored as evidence metadata for downstream explainability.
    """

    matched_terms_by_category: Mapping[str, tuple[str, ...]]
    all_matched_terms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched_terms_by_category": {
                k: list(v) for k, v in self.matched_terms_by_category.items()
            },
            "all_matched_terms": list(self.all_matched_terms),
        }


@dataclass(frozen=True)
class TextFeatures:
    """Strongly typed, immutable container for all text-derived ML features.

    Preserves the Slice 2.1 invariant: None != 0.
    When text is absent, text_available is False and indicator blocks are None.
    """

    text_available: bool
    lexical: Optional[LexicalMetrics]
    distress: Optional[DistressIndicators]
    help_seeking: Optional[HelpSeekingIndicators]
    safety: Optional[SafetyIndicators]
    quality: Optional[TextQualityMetadata]
    evidence: Optional[ExplanationEvidence] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_available": self.text_available,
            "lexical": None if self.lexical is None else self.lexical.to_dict(),
            "distress": None if self.distress is None else self.distress.to_dict(),
            "help_seeking": (
                None if self.help_seeking is None else self.help_seeking.to_dict()
            ),
            "safety": None if self.safety is None else self.safety.to_dict(),
            "quality": None if self.quality is None else self.quality.to_dict(),
            "evidence": None if self.evidence is None else self.evidence.to_dict(),
        }

    def to_feature_dict(self) -> dict[str, Any]:
        """Flattens numerical and categorical features for downstream model consumption.

        Preserves None for absent feature blocks (never converts absent blocks to 0).
        """
        features: dict[str, Any] = {
            "text_available": int(self.text_available),
        }

        if self.lexical is not None:
            for k, v in self.lexical.to_dict().items():
                features[f"lexical_{k}"] = v

        if self.distress is not None:
            for k, v in self.distress.to_dict().items():
                features[f"distress_{k}"] = v

        if self.help_seeking is not None:
            for k, v in self.help_seeking.to_dict().items():
                features[f"help_seeking_{k}"] = v

        if self.safety is not None:
            for k, v in self.safety.to_dict().items():
                features[f"safety_{k}"] = v

        if self.quality is not None:
            features["quality_is_very_short"] = int(self.quality.is_very_short)
            features["quality_has_multilingual"] = int(
                self.quality.has_multilingual_chars
            )

        return features


@dataclass(frozen=True)
class BehaviouralEvidence:
    """Metadata and evidence supporting explainability for behavioural features.

    Stores observation counts, raw Likert inputs, previous values, baseline values,
    deltas, timestamps, and notable shift factors.
    Does not affect numeric feature values.
    """

    observation_count: int
    raw_scores: Mapping[str, Optional[float]]
    previous_scores: Optional[Mapping[str, Optional[float]]] = None
    baseline_scores: Optional[Mapping[str, Optional[float]]] = None
    deltas_from_previous: Optional[Mapping[str, Optional[float]]] = None
    deltas_from_baseline: Optional[Mapping[str, Optional[float]]] = None
    timestamps: tuple[str, ...] = ()
    notable_shifts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "raw_scores": dict(self.raw_scores),
            "previous_scores": (
                None if self.previous_scores is None else dict(self.previous_scores)
            ),
            "baseline_scores": (
                None if self.baseline_scores is None else dict(self.baseline_scores)
            ),
            "deltas_from_previous": (
                None
                if self.deltas_from_previous is None
                else dict(self.deltas_from_previous)
            ),
            "deltas_from_baseline": (
                None
                if self.deltas_from_baseline is None
                else dict(self.deltas_from_baseline)
            ),
            "timestamps": list(self.timestamps),
            "notable_shifts": list(self.notable_shifts),
        }


@dataclass(frozen=True)
class BehaviouralFeatures:
    """Strongly typed, immutable container for behavioural features (Slice 2.3).

    Preserves None != 0 invariant: missing ratings or missing history remain None.
    Normalized to [0.0, 1.0] where 1.0 uniformly represents maximal distress.
    """

    behavioural_available: bool
    safety_distress: Optional[float]
    sleep_disturbance: Optional[float]
    fear_intensity: Optional[float]
    low_social_support: Optional[float]
    help_requested: Optional[float]
    composite_distress: Optional[float]
    change_from_previous: Optional[float] = None
    change_from_baseline: Optional[float] = None
    evidence: Optional[BehaviouralEvidence] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "behavioural_available": self.behavioural_available,
            "safety_distress": self.safety_distress,
            "sleep_disturbance": self.sleep_disturbance,
            "fear_intensity": self.fear_intensity,
            "low_social_support": self.low_social_support,
            "help_requested": self.help_requested,
            "composite_distress": self.composite_distress,
            "change_from_previous": self.change_from_previous,
            "change_from_baseline": self.change_from_baseline,
            "evidence": None if self.evidence is None else self.evidence.to_dict(),
        }

    def to_feature_dict(self) -> dict[str, Any]:
        """Flattens features for downstream model consumption without converting None to 0."""
        features: dict[str, Any] = {
            "behavioural_available": int(self.behavioural_available),
        }
        if self.behavioural_available:
            for metric in (
                "safety_distress",
                "sleep_disturbance",
                "fear_intensity",
                "low_social_support",
                "help_requested",
                "composite_distress",
                "change_from_previous",
                "change_from_baseline",
            ):
                val = getattr(self, metric)
                if val is not None:
                    features[f"behavioural_{metric}"] = val

        return features


@dataclass(frozen=True)
class EngagementEvidence:
    """Metadata and evidence supporting explainability for engagement features.

    Stores observation counts, completion counts, streaks, delay statistics,
    and notable shift descriptions. Does not alter numeric feature values.
    """

    observation_count: int
    timestamps: tuple[str, ...]
    completed_count: int
    missed_count: int
    current_streak: int
    delays: tuple[float, ...] = ()
    previous_engagement_score: Optional[float] = None
    baseline_engagement_score: Optional[float] = None
    notable_shifts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "timestamps": list(self.timestamps),
            "completed_count": self.completed_count,
            "missed_count": self.missed_count,
            "current_streak": self.current_streak,
            "delays": list(self.delays),
            "previous_engagement_score": self.previous_engagement_score,
            "baseline_engagement_score": self.baseline_engagement_score,
            "notable_shifts": list(self.notable_shifts),
        }


@dataclass(frozen=True)
class EngagementFeatures:
    """Strongly typed, immutable container for engagement features (Slice 2.4).

    Preserves the None != 0 invariant: missing delay or absent history remain None.
    Measures interaction adherence/behaviour, NOT clinical distress (User Modification 2).
    """

    engagement_available: bool
    completed_checkin: Optional[float]
    missed_checkin: Optional[float]
    missed_checkin_streak: Optional[int]
    checkin_consistency: Optional[float]
    response_delay: Optional[float]
    average_response_delay: Optional[float]
    response_frequency: Optional[float]
    engagement_drop: Optional[float]
    interaction_count: int
    recent_activity_count: Optional[int] = None
    inactivity_duration: Optional[float] = None
    engagement_score: Optional[float] = None
    change_from_previous: Optional[float] = None
    change_from_baseline: Optional[float] = None
    engagement_trend: Optional[str] = None
    evidence: Optional[EngagementEvidence] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "engagement_available": self.engagement_available,
            "completed_checkin": self.completed_checkin,
            "missed_checkin": self.missed_checkin,
            "missed_checkin_streak": self.missed_checkin_streak,
            "checkin_consistency": self.checkin_consistency,
            "response_delay": self.response_delay,
            "average_response_delay": self.average_response_delay,
            "response_frequency": self.response_frequency,
            "engagement_drop": self.engagement_drop,
            "interaction_count": self.interaction_count,
            "recent_activity_count": self.recent_activity_count,
            "inactivity_duration": self.inactivity_duration,
            "engagement_score": self.engagement_score,
            "change_from_previous": self.change_from_previous,
            "change_from_baseline": self.change_from_baseline,
            "engagement_trend": self.engagement_trend,
            "evidence": None if self.evidence is None else self.evidence.to_dict(),
        }

    def to_feature_dict(self) -> dict[str, Any]:
        """Flattens features for downstream model consumption without converting None to 0."""
        features: dict[str, Any] = {
            "engagement_available": int(self.engagement_available),
            "engagement_interaction_count": self.interaction_count,
        }
        if self.engagement_available:
            for metric in (
                "completed_checkin",
                "missed_checkin",
                "missed_checkin_streak",
                "checkin_consistency",
                "response_delay",
                "average_response_delay",
                "response_frequency",
                "engagement_drop",
                "recent_activity_count",
                "inactivity_duration",
                "engagement_score",
                "change_from_previous",
                "change_from_baseline",
            ):
                val = getattr(self, metric)
                if val is not None:
                    features[f"engagement_{metric}"] = val

            if self.engagement_trend is not None:
                features["engagement_trend"] = self.engagement_trend

        return features


@dataclass(frozen=True)
class LongitudinalEvidence:
    """Structured evidence for longitudinal features (User Modification 2).

    Retains baseline values, historical observations, computed deltas, trend calculations,
    observation counts, timestamps, and contributing factors for downstream explainability.
    Does not affect numeric feature values directly.
    """

    observation_count: int
    timestamps: tuple[str, ...]
    distress_scores: tuple[Optional[float], ...]
    baseline_distress: Optional[float]
    previous_distress: Optional[float]
    current_distress: Optional[float]
    delta_from_baseline: Optional[float]
    delta_from_previous: Optional[float]
    distress_velocity: Optional[float]
    distress_acceleration: Optional[float]
    distress_volatility: Optional[float]
    trend: str
    contributing_factors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "timestamps": list(self.timestamps),
            "distress_scores": list(self.distress_scores),
            "baseline_distress": self.baseline_distress,
            "previous_distress": self.previous_distress,
            "current_distress": self.current_distress,
            "delta_from_baseline": self.delta_from_baseline,
            "delta_from_previous": self.delta_from_previous,
            "distress_velocity": self.distress_velocity,
            "distress_acceleration": self.distress_acceleration,
            "distress_volatility": self.distress_volatility,
            "trend": self.trend,
            "contributing_factors": list(self.contributing_factors),
        }


@dataclass(frozen=True)
class LongitudinalFeatures:
    """Strongly typed, immutable container for longitudinal features (Slice 2.5).

    Preserves the None != 0 invariant: missing historical observations, missing
    baselines, or insufficient history remain None rather than being fabricated as 0.
    """

    longitudinal_available: bool
    observation_count: int
    history_span_days: Optional[int]
    current_distress: Optional[float]
    baseline_distress: Optional[float]
    previous_distress: Optional[float]
    delta_from_baseline: Optional[float]
    delta_from_previous: Optional[float]
    distress_velocity: Optional[float]
    distress_acceleration: Optional[float]
    distress_volatility: Optional[float]
    peak_distress: Optional[float]
    trough_distress: Optional[float]
    sustained_distress_count: Optional[int]
    longitudinal_trend: str
    evidence: Optional[LongitudinalEvidence] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "longitudinal_available": self.longitudinal_available,
            "observation_count": self.observation_count,
            "history_span_days": self.history_span_days,
            "current_distress": self.current_distress,
            "baseline_distress": self.baseline_distress,
            "previous_distress": self.previous_distress,
            "delta_from_baseline": self.delta_from_baseline,
            "delta_from_previous": self.delta_from_previous,
            "distress_velocity": self.distress_velocity,
            "distress_acceleration": self.distress_acceleration,
            "distress_volatility": self.distress_volatility,
            "peak_distress": self.peak_distress,
            "trough_distress": self.trough_distress,
            "sustained_distress_count": self.sustained_distress_count,
            "longitudinal_trend": self.longitudinal_trend,
            "evidence": None if self.evidence is None else self.evidence.to_dict(),
        }

    def to_feature_dict(self) -> dict[str, Any]:
        """Flattens longitudinal features for downstream model consumption without converting None to 0."""
        features: dict[str, Any] = {
            "longitudinal_available": int(self.longitudinal_available),
            "longitudinal_observation_count": self.observation_count,
        }
        if self.longitudinal_available:
            for metric in (
                "history_span_days",
                "current_distress",
                "baseline_distress",
                "previous_distress",
                "delta_from_baseline",
                "delta_from_previous",
                "distress_velocity",
                "distress_acceleration",
                "distress_volatility",
                "peak_distress",
                "trough_distress",
                "sustained_distress_count",
            ):
                val = getattr(self, metric)
                if val is not None:
                    features[f"longitudinal_{metric}"] = val

            if self.longitudinal_trend is not None:
                features["longitudinal_trend"] = self.longitudinal_trend

        return features


from backend.ml.features.voice import VoiceFeatures


