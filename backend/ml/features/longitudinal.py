"""Longitudinal feature extraction (Slice 2.5).

Extracts longitudinal trajectory metrics, rate of change, volatility, and historical
shifts from PreprocessedInteraction sequences. Preserves the None != 0 invariant,
enforces centralized trend definitions, and generates structured explainability evidence.
"""

from __future__ import annotations

from datetime import date
import math
from typing import Any, Iterable, Mapping, Optional, Sequence

from backend.ml.features.definitions import normalize_likert_rating
from backend.ml.features.longitudinal_definitions import (
    LongitudinalConfig,
    LongitudinalTrend,
    classify_longitudinal_trend,
)
from backend.ml.features.extractor import extract_text_features
from backend.ml.features.types import (
    LongitudinalEvidence,
    LongitudinalFeatures,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


def _parse_date(date_str: str) -> Optional[date]:
    """Parses ISO date string (YYYY-MM-DD) safely."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(str(date_str)[:10])
    except (ValueError, TypeError):
        return None


def compute_interaction_distress(
    interaction: PreprocessedInteraction,
) -> Optional[float]:
    """Computes composite distress in [0.0, 1.0] for a single interaction.

    Combines available behavioural distress indicators and text distress indicators.
    Preserves None != 0 if no distress data is present.
    """
    if "distress_score" in interaction.metadata:
        try:
            return round(float(interaction.metadata["distress_score"]), 3)
        except (ValueError, TypeError):
            pass

    components: list[float] = []

    # 1. Behavioural composite
    raw_b = interaction.behavioural
    b_scores = [
        normalize_likert_rating(raw_b.get("safety_response"), invert=True),
        normalize_likert_rating(raw_b.get("sleep_disruption"), invert=False),
        normalize_likert_rating(raw_b.get("fear_level"), invert=False),
        normalize_likert_rating(raw_b.get("social_support"), invert=True),
    ]
    available_b = [s for s in b_scores if s is not None]
    if available_b:
        components.append(sum(available_b) / len(available_b))

    # 2. Text distress indicators
    if interaction.text and not interaction.text.quality.is_empty and interaction.text.clean.strip():
        text_feats = extract_text_features(interaction)
        if text_feats.text_available and text_feats.distress is not None:
            td = text_feats.distress
            vals = [
                td.fear,
                td.hopelessness,
                td.isolation,
                td.helplessness,
                td.intimidation,
                td.sadness,
                td.anxiety,
            ]
            if any(v > 0.0 for v in vals):
                components.append(sum(vals) / len(vals))

    if not components:
        return None
    return round(sum(components) / len(components), 3)


class LongitudinalFeatureExtractor:
    """Extracts strongly typed longitudinal features across an interaction timeline.

    Guarantees:
    - Centralized trend and threshold definitions (User Modification 1).
    - Rich explainability evidence metadata (User Modification 2).
    - Strict None != 0 preservation: insufficient history yields None/UNKNOWN (User Modification 3).
    """

    def extract(
        self,
        interaction: PreprocessedInteraction,
        history: Optional[Sequence[PreprocessedInteraction]] = None,
        config: Optional[LongitudinalConfig] = None,
    ) -> LongitudinalFeatures:
        """Extracts longitudinal features for the current interaction given its history."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError(
                "extract() requires a PreprocessedInteraction instance. "
                "Raw inputs must be routed through preprocess_interaction() or "
                "use extract_from_raw()."
            )

        cfg = config or LongitudinalConfig()

        # Build chronological timeline
        valid_history = [
            h
            for h in (history or ())
            if isinstance(h, PreprocessedInteraction) and h.case_id == interaction.case_id
        ]
        all_interactions = list(valid_history) + [interaction]
        all_interactions.sort(key=lambda x: x.interaction_date)

        observation_count = len(all_interactions)
        timestamps = tuple(item.interaction_date for item in all_interactions)

        # Compute distress score for each interaction
        scores_list = [compute_interaction_distress(item) for item in all_interactions]
        dates_list = [_parse_date(item.interaction_date) for item in all_interactions]

        # Filter valid observation points with both valid date and valid distress score
        valid_points = [
            (d, s)
            for d, s in zip(dates_list, scores_list)
            if d is not None and s is not None
        ]

        # Current distress is computed for the focal interaction
        current_distress = compute_interaction_distress(interaction)

        if not valid_points:
            # Completely missing longitudinal distress data
            return LongitudinalFeatures(
                longitudinal_available=False,
                observation_count=observation_count,
                history_span_days=None,
                current_distress=None,
                baseline_distress=None,
                previous_distress=None,
                delta_from_baseline=None,
                delta_from_previous=None,
                distress_velocity=None,
                distress_acceleration=None,
                distress_volatility=None,
                peak_distress=None,
                trough_distress=None,
                sustained_distress_count=None,
                longitudinal_trend=LongitudinalTrend.UNKNOWN.value,
                evidence=None,
            )

        # Total history span in days
        history_span_days: Optional[int] = None
        if len(valid_points) >= 2:
            history_span_days = max(0, (valid_points[-1][0] - valid_points[0][0]).days)
        elif len(valid_points) == 1:
            history_span_days = 0

        # Baseline and previous distress (User Modification 3: None != 0)
        # Baseline requires at least 2 observations (prior reference point)
        baseline_distress: Optional[float] = None
        previous_distress: Optional[float] = None
        delta_from_baseline: Optional[float] = None
        delta_from_previous: Optional[float] = None

        if len(valid_points) >= 2:
            baseline_distress = valid_points[0][1]
            previous_distress = valid_points[-2][1]
            if current_distress is not None and baseline_distress is not None:
                delta_from_baseline = round(current_distress - baseline_distress, 3)
            if current_distress is not None and previous_distress is not None:
                delta_from_previous = round(current_distress - previous_distress, 3)

        # Distress Velocity (rate of change per day)
        distress_velocity: Optional[float] = None
        if len(valid_points) >= 2:
            d0 = valid_points[0][0]
            days_from_start = [(pt[0] - d0).days for pt in valid_points]
            scores = [pt[1] for pt in valid_points]
            total_days = days_from_start[-1]

            if total_days > 0:
                mean_x = sum(days_from_start) / len(days_from_start)
                mean_y = sum(scores) / len(scores)
                denom = sum((x - mean_x) ** 2 for x in days_from_start)
                if denom > 0:
                    numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(days_from_start, scores))
                    distress_velocity = round(numer / denom, 4)
                else:
                    distress_velocity = round((scores[-1] - scores[0]) / float(total_days), 4)
            else:
                distress_velocity = round(scores[-1] - scores[0], 4)

        # Distress Acceleration (second derivative: rate of change of velocity)
        distress_acceleration: Optional[float] = None
        if len(valid_points) >= 3:
            p0, p1, p2 = valid_points[-3], valid_points[-2], valid_points[-1]
            dt1 = max(1.0, float((p1[0] - p0[0]).days))
            dt2 = max(1.0, float((p2[0] - p1[0]).days))
            v1 = (p1[1] - p0[1]) / dt1
            v2 = (p2[1] - p1[1]) / dt2
            mid_dt = max(1.0, (dt1 + dt2) / 2.0)
            distress_acceleration = round((v2 - v1) / mid_dt, 4)

        # Distress Volatility (standard deviation of observed distress scores)
        distress_volatility: Optional[float] = None
        if len(valid_points) >= 2:
            s_vals = [pt[1] for pt in valid_points]
            mean_s = sum(s_vals) / len(s_vals)
            variance = sum((s - mean_s) ** 2 for s in s_vals) / (len(s_vals) - 1)
            distress_volatility = round(math.sqrt(variance), 3)

        # Extremes
        valid_scores = [pt[1] for pt in valid_points]
        peak_distress = round(max(valid_scores), 3)
        trough_distress = round(min(valid_scores), 3)

        # Sustained high distress count (consecutive interactions >= high_distress_threshold)
        sustained_distress_count = 0
        for _, s in reversed(valid_points):
            if s >= cfg.high_distress_threshold:
                sustained_distress_count += 1
            else:
                break

        # Centralized Trend Classification (User Modification 1 & 3)
        trend_enum = classify_longitudinal_trend(
            delta_previous=delta_from_previous,
            delta_baseline=delta_from_baseline,
            velocity=distress_velocity,
            config=cfg,
            observation_count=len(valid_points),
        )
        longitudinal_trend = trend_enum.value

        # Structured Explainability Evidence (User Modification 2)
        contributing_factors: list[str] = []
        if delta_from_baseline is not None:
            if delta_from_baseline >= cfg.notable_shift_threshold:
                contributing_factors.append(
                    f"Distress substantially elevated above baseline (+{delta_from_baseline:.2f})"
                )
            elif delta_from_baseline <= -cfg.notable_shift_threshold:
                contributing_factors.append(
                    f"Distress decreased significantly compared to baseline ({delta_from_baseline:.2f})"
                )

        if delta_from_previous is not None:
            if delta_from_previous >= cfg.notable_shift_threshold:
                contributing_factors.append(
                    f"Distress increased from previous interaction (+{delta_from_previous:.2f})"
                )
            elif delta_from_previous <= -cfg.notable_shift_threshold:
                contributing_factors.append(
                    f"Distress decreased from previous interaction ({delta_from_previous:.2f})"
                )

        if trend_enum == LongitudinalTrend.RAPIDLY_WORSENING:
            contributing_factors.append("Rapidly worsening distress trajectory detected")
        elif trend_enum == LongitudinalTrend.RAPIDLY_IMPROVING:
            contributing_factors.append("Rapidly improving distress trajectory detected")

        if sustained_distress_count >= 2:
            contributing_factors.append(
                f"Sustained high distress across {sustained_distress_count} consecutive interactions"
            )

        if (
            distress_volatility is not None
            and distress_volatility >= cfg.volatility_alert_threshold
        ):
            contributing_factors.append(
                f"High distress volatility observed ({distress_volatility:.2f})"
            )

        evidence = LongitudinalEvidence(
            observation_count=observation_count,
            timestamps=timestamps,
            distress_scores=tuple(scores_list),
            baseline_distress=baseline_distress,
            previous_distress=previous_distress,
            current_distress=current_distress,
            delta_from_baseline=delta_from_baseline,
            delta_from_previous=delta_from_previous,
            distress_velocity=distress_velocity,
            distress_acceleration=distress_acceleration,
            distress_volatility=distress_volatility,
            trend=longitudinal_trend,
            contributing_factors=tuple(contributing_factors),
        )

        return LongitudinalFeatures(
            longitudinal_available=True,
            observation_count=observation_count,
            history_span_days=history_span_days,
            current_distress=current_distress,
            baseline_distress=baseline_distress,
            previous_distress=previous_distress,
            delta_from_baseline=delta_from_baseline,
            delta_from_previous=delta_from_previous,
            distress_velocity=distress_velocity,
            distress_acceleration=distress_acceleration,
            distress_volatility=distress_volatility,
            peak_distress=peak_distress,
            trough_distress=trough_distress,
            sustained_distress_count=sustained_distress_count,
            longitudinal_trend=longitudinal_trend,
            evidence=evidence,
        )

    def extract_from_raw(
        self,
        current_raw: Mapping[str, Any],
        history_raw: Optional[Sequence[Mapping[str, Any]]] = None,
        config: Optional[LongitudinalConfig] = None,
    ) -> LongitudinalFeatures:
        """Convenience method that preprocesses raw payloads before extraction."""
        current_prep = preprocess_interaction(current_raw)
        history_prep = [preprocess_interaction(h) for h in (history_raw or ())]
        return self.extract(current_prep, history=history_prep, config=config)

    def extract_batch(
        self,
        items: Iterable[tuple[PreprocessedInteraction, Optional[Sequence[PreprocessedInteraction]]]],
        config: Optional[LongitudinalConfig] = None,
    ) -> list[LongitudinalFeatures]:
        """Extracts longitudinal features for multiple interactions in batch."""
        return [self.extract(cur, hist, config) for cur, hist in items]


# Functional convenience entry points
_DEFAULT_EXTRACTOR = LongitudinalFeatureExtractor()


def extract_longitudinal_features(
    interaction: PreprocessedInteraction,
    history: Optional[Sequence[PreprocessedInteraction]] = None,
    config: Optional[LongitudinalConfig] = None,
) -> LongitudinalFeatures:
    """Convenience function to extract longitudinal features using the default extractor."""
    return _DEFAULT_EXTRACTOR.extract(interaction, history=history, config=config)


def extract_longitudinal_features_batch(
    items: Iterable[tuple[PreprocessedInteraction, Optional[Sequence[PreprocessedInteraction]]]],
    config: Optional[LongitudinalConfig] = None,
) -> list[LongitudinalFeatures]:
    """Convenience function to extract longitudinal features in batch."""
    return _DEFAULT_EXTRACTOR.extract_batch(items, config=config)
