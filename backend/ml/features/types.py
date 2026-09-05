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
