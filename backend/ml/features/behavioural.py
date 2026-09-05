"""Behavioural feature extraction (Slice 2.3).

Extracts normalized behavioural distress metrics and longitudinal shifts from
PreprocessedInteraction records. Preserves the None != 0 invariant and generates
rich explainability evidence.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence

from backend.ml.features.definitions import (
    ALL_BEHAVIOURAL_INPUT_FIELDS,
    HIGH_DISTRESS_THRESHOLD,
    NOTABLE_SHIFT_THRESHOLD,
    normalize_likert_rating,
)
from backend.ml.features.types import (
    BehaviouralEvidence,
    BehaviouralFeatures,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


def _compute_composite(scores: Sequence[Optional[float]]) -> Optional[float]:
    """Calculates mean of available non-None scores, or returns None if empty."""
    available = [s for s in scores if s is not None]
    if not available:
        return None
    return round(sum(available) / len(available), 3)


def _compute_metric_deltas(
    current: Mapping[str, Optional[float]],
    prior: Mapping[str, Optional[float]],
) -> dict[str, Optional[float]]:
    """Calculates pairwise score differences (current - prior) preserving None."""
    deltas: dict[str, Optional[float]] = {}
    for key in ("safety_distress", "sleep_disturbance", "fear_intensity", "low_social_support"):
        c_val = current.get(key)
        p_val = prior.get(key)
        if c_val is not None and p_val is not None:
            deltas[key] = round(c_val - p_val, 3)
        else:
            deltas[key] = None
    return deltas


class BehaviouralFeatureExtractor:
    """Extracts strongly typed behavioural features from PreprocessedInteraction.

    Guarantees:
    - Centralized metric scaling and inversion logic.
    - None != 0 preservation: absent history or ratings remain None.
    - Exposes explainability evidence (shifts, previous/baseline comparisons).
    """

    def extract(
        self,
        interaction: PreprocessedInteraction,
        history: Optional[Sequence[PreprocessedInteraction]] = None,
    ) -> BehaviouralFeatures:
        """Extracts behavioural features from a PreprocessedInteraction."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError(
                "extract() requires a PreprocessedInteraction instance. "
                "Raw inputs must be routed through preprocess_interaction() or "
                "use extract_from_raw()."
            )

        raw_ratings = interaction.behavioural
        raw_safety = raw_ratings.get("safety_response")
        raw_sleep = raw_ratings.get("sleep_disruption")
        raw_fear = raw_ratings.get("fear_level")
        raw_support = raw_ratings.get("social_support")
        raw_help = interaction.engagement.get("help_requested")

        # Check if any behavioural data was observed
        all_ratings_none = all(
            raw_ratings.get(f) is None for f in ALL_BEHAVIOURAL_INPUT_FIELDS
        )
        if all_ratings_none and not raw_help:
            return BehaviouralFeatures(
                behavioural_available=False,
                safety_distress=None,
                sleep_disturbance=None,
                fear_intensity=None,
                low_social_support=None,
                help_requested=None,
                composite_distress=None,
                change_from_previous=None,
                change_from_baseline=None,
                evidence=None,
            )

        # 1. Normalize current ratings (1.0 = maximal distress)
        safety_distress = normalize_likert_rating(raw_safety, invert=True)
        sleep_disturbance = normalize_likert_rating(raw_sleep, invert=False)
        fear_intensity = normalize_likert_rating(raw_fear, invert=False)
        low_social_support = normalize_likert_rating(raw_support, invert=True)

        help_requested = (
            1.0 if raw_help is True else (0.0 if raw_help is False else None)
        )

        current_scores = {
            "safety_distress": safety_distress,
            "sleep_disturbance": sleep_disturbance,
            "fear_intensity": fear_intensity,
            "low_social_support": low_social_support,
        }

        composite_distress = _compute_composite(
            [safety_distress, sleep_disturbance, fear_intensity, low_social_support]
        )

        # 2. Longitudinal History Processing (if provided)
        previous_scores: Optional[dict[str, Optional[float]]] = None
        baseline_scores: Optional[dict[str, Optional[float]]] = None
        deltas_from_previous: Optional[dict[str, Optional[float]]] = None
        deltas_from_baseline: Optional[dict[str, Optional[float]]] = None
        change_from_previous: Optional[float] = None
        change_from_baseline: Optional[float] = None
        timestamps: list[str] = [interaction.interaction_date]

        valid_history = [
            h
            for h in (history or ())
            if isinstance(h, PreprocessedInteraction) and h.case_id == interaction.case_id
        ]
        # Sort chronologically
        valid_history.sort(key=lambda x: x.interaction_date)

        observation_count = len(valid_history) + 1

        if valid_history:
            for h in valid_history:
                timestamps.append(h.interaction_date)

            # Baseline is first historical observation
            baseline_int = valid_history[0]
            b_safety = normalize_likert_rating(
                baseline_int.behavioural.get("safety_response"), invert=True
            )
            b_sleep = normalize_likert_rating(
                baseline_int.behavioural.get("sleep_disruption"), invert=False
            )
            b_fear = normalize_likert_rating(
                baseline_int.behavioural.get("fear_level"), invert=False
            )
            b_support = normalize_likert_rating(
                baseline_int.behavioural.get("social_support"), invert=True
            )
            baseline_scores = {
                "safety_distress": b_safety,
                "sleep_disturbance": b_sleep,
                "fear_intensity": b_fear,
                "low_social_support": b_support,
            }
            baseline_composite = _compute_composite(
                [b_safety, b_sleep, b_fear, b_support]
            )

            if composite_distress is not None and baseline_composite is not None:
                change_from_baseline = round(
                    composite_distress - baseline_composite, 3
                )
            deltas_from_baseline = _compute_metric_deltas(
                current_scores, baseline_scores
            )

            # Previous is immediately preceding historical observation
            prev_int = valid_history[-1]
            p_safety = normalize_likert_rating(
                prev_int.behavioural.get("safety_response"), invert=True
            )
            p_sleep = normalize_likert_rating(
                prev_int.behavioural.get("sleep_disruption"), invert=False
            )
            p_fear = normalize_likert_rating(
                prev_int.behavioural.get("fear_level"), invert=False
            )
            p_support = normalize_likert_rating(
                prev_int.behavioural.get("social_support"), invert=True
            )
            previous_scores = {
                "safety_distress": p_safety,
                "sleep_disturbance": p_sleep,
                "fear_intensity": p_fear,
                "low_social_support": p_support,
            }
            prev_composite = _compute_composite(
                [p_safety, p_sleep, p_fear, p_support]
            )

            if composite_distress is not None and prev_composite is not None:
                change_from_previous = round(
                    composite_distress - prev_composite, 3
                )
            deltas_from_previous = _compute_metric_deltas(
                current_scores, previous_scores
            )

        # 3. Notable Shift Factors for Explainability (User Modification 2)
        notable_shifts: list[str] = []

        if change_from_previous is not None:
            if change_from_previous >= NOTABLE_SHIFT_THRESHOLD:
                notable_shifts.append(
                    f"Distress increased from previous interaction (+{change_from_previous:.2f})"
                )
            elif change_from_previous <= -NOTABLE_SHIFT_THRESHOLD:
                notable_shifts.append(
                    f"Distress decreased from previous interaction ({change_from_previous:.2f})"
                )

        if change_from_baseline is not None:
            if change_from_baseline >= NOTABLE_SHIFT_THRESHOLD:
                notable_shifts.append(
                    f"Distress substantially elevated above baseline (+{change_from_baseline:.2f})"
                )

        if fear_intensity is not None and fear_intensity >= HIGH_DISTRESS_THRESHOLD:
            notable_shifts.append("Elevated fear intensity observed")
        if safety_distress is not None and safety_distress >= HIGH_DISTRESS_THRESHOLD:
            notable_shifts.append("Severe safety concern reported")
        if sleep_disturbance is not None and sleep_disturbance >= HIGH_DISTRESS_THRESHOLD:
            notable_shifts.append("Severe sleep disruption reported")
        if low_social_support is not None and low_social_support >= HIGH_DISTRESS_THRESHOLD:
            notable_shifts.append("Critical lack of social support reported")
        if help_requested == 1.0:
            notable_shifts.append("Explicit assistance requested by participant")

        # 4. Assembling Evidence Metadata
        evidence = BehaviouralEvidence(
            observation_count=observation_count,
            raw_scores={
                "safety_response": raw_safety,
                "sleep_disruption": raw_sleep,
                "fear_level": raw_fear,
                "social_support": raw_support,
                "help_requested": 1.0 if raw_help is True else (0.0 if raw_help is False else None),
            },
            previous_scores=previous_scores,
            baseline_scores=baseline_scores,
            deltas_from_previous=deltas_from_previous,
            deltas_from_baseline=deltas_from_baseline,
            timestamps=tuple(timestamps),
            notable_shifts=tuple(notable_shifts),
        )

        return BehaviouralFeatures(
            behavioural_available=True,
            safety_distress=safety_distress,
            sleep_disturbance=sleep_disturbance,
            fear_intensity=fear_intensity,
            low_social_support=low_social_support,
            help_requested=help_requested,
            composite_distress=composite_distress,
            change_from_previous=change_from_previous,
            change_from_baseline=change_from_baseline,
            evidence=evidence,
        )

    def extract_from_raw(
        self,
        raw_input: Mapping[str, Any],
        history: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> BehaviouralFeatures:
        """Convenience helper routing raw dictionary inputs through preprocessing."""
        preprocessed = preprocess_interaction(raw_input)
        prep_history = (
            [preprocess_interaction(h) for h in history] if history else None
        )
        return self.extract(preprocessed, history=prep_history)

    def extract_batch(
        self,
        interactions: Iterable[PreprocessedInteraction],
    ) -> list[BehaviouralFeatures]:
        """Extracts behavioural features for an iterable of PreprocessedInteraction records."""
        return [self.extract(item) for item in interactions]


_DEFAULT_BEHAVIOURAL_EXTRACTOR = BehaviouralFeatureExtractor()


def extract_behavioural_features(
    interaction: PreprocessedInteraction,
    history: Optional[Sequence[PreprocessedInteraction]] = None,
    extractor: Optional[BehaviouralFeatureExtractor] = None,
) -> BehaviouralFeatures:
    """Convenience functional interface for behavioural feature extraction."""
    e = extractor or _DEFAULT_BEHAVIOURAL_EXTRACTOR
    return e.extract(interaction, history=history)


def extract_behavioural_features_batch(
    interactions: Iterable[PreprocessedInteraction],
    extractor: Optional[BehaviouralFeatureExtractor] = None,
) -> list[BehaviouralFeatures]:
    """Convenience functional interface for batch behavioural feature extraction."""
    e = extractor or _DEFAULT_BEHAVIOURAL_EXTRACTOR
    return e.extract_batch(interactions)
