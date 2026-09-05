"""Engagement feature extraction (Slice 2.4).

Extracts check-in behaviour, response delays, interaction frequency, and longitudinal
engagement signals from PreprocessedInteraction records.
Preserves the None != 0 invariant and provides explainability evidence.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Mapping, Optional, Sequence

from backend.ml.features.engagement_definitions import (
    EngagementConfig,
    EngagementTrend,
)
from backend.ml.features.types import (
    EngagementEvidence,
    EngagementFeatures,
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
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _compute_score_for_prefix(
    interactions: Sequence[PreprocessedInteraction],
    config: EngagementConfig,
) -> Optional[float]:
    """Computes engagement adherence score consistently for a sequence prefix."""
    if not interactions:
        return None
    completed = sum(
        1 for item in interactions if item.engagement.get("response_completed") is True
    )
    total = sum(
        1 for item in interactions if item.engagement.get("response_completed") is not None
    )
    if total == 0:
        return None
    consistency = completed / total

    # Check most recent delay in this prefix
    delay: Optional[float] = None
    if len(interactions) > 1:
        d1 = _parse_date(interactions[-2].interaction_date)
        d2 = _parse_date(interactions[-1].interaction_date)
        if d1 is not None and d2 is not None:
            delay = float(max(0, (d2 - d1).days))

    if delay is not None and delay > config.long_response_delay_days:
        delay_factor = max(
            0.0,
            1.0
            - min(
                1.0,
                (delay - config.long_response_delay_days)
                / (2.0 * config.long_response_delay_days),
            ),
        )
        return round(0.7 * consistency + 0.3 * delay_factor, 3)
    return round(consistency, 3)


class EngagementFeatureExtractor:
    """Extracts strongly typed engagement features from PreprocessedInteraction.

    Guarantees:
    - None != 0 invariant: missing delay or missing history strictly remains None.
    - Configurable thresholds via EngagementConfig (User Modification 1).
    - Engagement score summarizes interaction adherence, NOT distress (User Modification 2).
    - Collects structured evidence metadata for explainability.
    """

    def __init__(self, config: Optional[EngagementConfig] = None) -> None:
        self.config = config or EngagementConfig()

    def extract(
        self,
        interaction: PreprocessedInteraction,
        history: Optional[Sequence[PreprocessedInteraction]] = None,
    ) -> EngagementFeatures:
        """Extracts engagement features from a PreprocessedInteraction."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError(
                "extract() requires a PreprocessedInteraction instance. "
                "Raw inputs must be routed through preprocess_interaction() or "
                "use extract_from_raw()."
            )

        # 1. Basic Check-in Metrics
        raw_comp = interaction.engagement.get("response_completed")
        if raw_comp is None:
            completed_checkin: Optional[float] = None
            missed_checkin: Optional[float] = None
        elif raw_comp is True:
            completed_checkin = 1.0
            missed_checkin = 0.0
        else:
            completed_checkin = 0.0
            missed_checkin = 1.0

        # Check if engagement data is available at all
        if completed_checkin is None and not interaction.engagement.get("channel"):
            return EngagementFeatures(
                engagement_available=False,
                completed_checkin=None,
                missed_checkin=None,
                missed_checkin_streak=None,
                checkin_consistency=None,
                response_delay=None,
                average_response_delay=None,
                response_frequency=None,
                engagement_drop=None,
                interaction_count=0,
                evidence=None,
            )

        # 2. History & Sequence Alignment
        valid_history = [
            h
            for h in (history or ())
            if isinstance(h, PreprocessedInteraction) and h.case_id == interaction.case_id
        ]
        valid_history.sort(key=lambda x: x.interaction_date)

        all_interactions = valid_history + [interaction]
        observation_count = len(all_interactions)

        # 3. Check-in Streak & Consistency
        completed_count = 0
        missed_count = 0
        for item in all_interactions:
            comp = item.engagement.get("response_completed")
            if comp is True:
                completed_count += 1
            elif comp is False:
                missed_count += 1

        total_known = completed_count + missed_count
        checkin_consistency = (
            round(completed_count / total_known, 3) if total_known > 0 else None
        )

        # Streak calculation: consecutive missed check-ins leading up to and including current
        missed_streak = 0
        for item in reversed(all_interactions):
            comp = item.engagement.get("response_completed")
            if comp is False:
                missed_streak += 1
            elif comp is True:
                break

        # 4. Response Delays & Dates
        curr_date = _parse_date(interaction.interaction_date)
        delays: list[float] = []

        # Check if response_delay is passed directly in metadata
        direct_delay = interaction.metadata.get("response_delay")
        if direct_delay is not None:
            try:
                response_delay: Optional[float] = float(direct_delay)
            except (ValueError, TypeError):
                response_delay = None
        elif len(valid_history) > 0 and curr_date is not None:
            prev_date = _parse_date(valid_history[-1].interaction_date)
            if prev_date is not None:
                response_delay = float(max(0, (curr_date - prev_date).days))
            else:
                response_delay = None
        else:
            # First observation or no history: delay is unknown/None (None != 0)
            response_delay = None

        # Collect historical delays between consecutive interactions
        for i in range(1, len(all_interactions)):
            d1 = _parse_date(all_interactions[i - 1].interaction_date)
            d2 = _parse_date(all_interactions[i].interaction_date)
            if d1 is not None and d2 is not None:
                delays.append(float(max(0, (d2 - d1).days)))

        average_response_delay = (
            round(sum(delays) / len(delays), 2) if delays else response_delay
        )

        # Inactivity duration is the response delay from last observed interaction
        inactivity_duration = response_delay

        # Response frequency (interactions per 7 days across observed span)
        if len(all_interactions) > 1:
            first_d = _parse_date(all_interactions[0].interaction_date)
            last_d = _parse_date(all_interactions[-1].interaction_date)
            if first_d is not None and last_d is not None:
                total_span_days = max(1, (last_d - first_d).days)
                response_frequency = round(
                    (observation_count / total_span_days) * 7.0, 3
                )
            else:
                response_frequency = None
        else:
            response_frequency = None

        # Recent activity count (within configured window)
        recent_activity_count = 0
        if curr_date is not None:
            for item in all_interactions:
                d = _parse_date(item.interaction_date)
                if d is not None:
                    if 0 <= (curr_date - d).days <= self.config.recent_activity_window_days:
                        recent_activity_count += 1
        else:
            recent_activity_count = 1

        # 5. Engagement Score (Interaction Adherence/Reliability)
        # Note: Measures engagement behaviour, NOT psychological distress (User Modification 2)
        engagement_score = _compute_score_for_prefix(all_interactions, self.config)

        # 6. Longitudinal Engagement Shifts & Trend
        previous_engagement_score: Optional[float] = None
        baseline_engagement_score: Optional[float] = None
        change_from_previous: Optional[float] = None
        change_from_baseline: Optional[float] = None
        engagement_drop: Optional[float] = None

        if len(valid_history) > 0:
            # Baseline engagement score from first interaction
            baseline_engagement_score = _compute_score_for_prefix(
                valid_history[:1], self.config
            )

            # Previous engagement score from preceding interactions
            previous_engagement_score = _compute_score_for_prefix(
                valid_history, self.config
            )

            if engagement_score is not None and previous_engagement_score is not None:
                change_from_previous = round(
                    engagement_score - previous_engagement_score, 3
                )

            if engagement_score is not None and baseline_engagement_score is not None:
                change_from_baseline = round(
                    engagement_score - baseline_engagement_score, 3
                )
                if baseline_engagement_score > engagement_score:
                    engagement_drop = round(
                        baseline_engagement_score - engagement_score, 3
                    )
                else:
                    engagement_drop = 0.0

            # Trend determination
            if (
                (change_from_previous is not None and change_from_previous <= -self.config.trend_shift_threshold)
                or missed_streak >= self.config.missed_checkin_alert_streak
            ):
                engagement_trend = EngagementTrend.DECLINING.value
            elif change_from_previous is not None and change_from_previous >= self.config.trend_shift_threshold:
                engagement_trend = EngagementTrend.IMPROVING.value
            else:
                engagement_trend = EngagementTrend.STABLE.value
        else:
            engagement_trend = (
                EngagementTrend.DECLINING.value
                if completed_checkin == 0.0
                else EngagementTrend.STABLE.value
            )

        # 7. Explainability Evidence & Notable Shifts
        notable_shifts: list[str] = []
        if missed_streak >= self.config.missed_checkin_alert_streak:
            notable_shifts.append(
                f"Missed {missed_streak} consecutive scheduled check-ins"
            )
        elif missed_checkin == 1.0:
            notable_shifts.append("Check-in was missed for this interaction")

        if (
            response_delay is not None
            and response_delay >= self.config.long_response_delay_days
        ):
            notable_shifts.append(
                f"Extended response delay of {response_delay:.1f} days"
            )

        if (
            checkin_consistency is not None
            and checkin_consistency < self.config.low_consistency_threshold
        ):
            notable_shifts.append(
                f"Low check-in completion consistency ({checkin_consistency:.0%})"
            )

        if (
            engagement_drop is not None
            and engagement_drop >= self.config.notable_engagement_drop
        ):
            notable_shifts.append(
                f"Engagement dropped substantially compared to baseline (-{engagement_drop:.2f})"
            )

        if (
            change_from_previous is not None
            and change_from_previous <= -self.config.trend_shift_threshold
        ):
            notable_shifts.append(
                f"Engagement declined noticeably from previous interaction ({change_from_previous:.2f})"
            )

        evidence = EngagementEvidence(
            observation_count=observation_count,
            timestamps=tuple(item.interaction_date for item in all_interactions),
            completed_count=completed_count,
            missed_count=missed_count,
            current_streak=missed_streak,
            delays=tuple(delays),
            previous_engagement_score=previous_engagement_score,
            baseline_engagement_score=baseline_engagement_score,
            notable_shifts=tuple(notable_shifts),
        )

        return EngagementFeatures(
            engagement_available=True,
            completed_checkin=completed_checkin,
            missed_checkin=missed_checkin,
            missed_checkin_streak=missed_streak,
            checkin_consistency=checkin_consistency,
            response_delay=response_delay,
            average_response_delay=average_response_delay,
            response_frequency=response_frequency,
            engagement_drop=engagement_drop,
            interaction_count=observation_count,
            recent_activity_count=recent_activity_count,
            inactivity_duration=inactivity_duration,
            engagement_score=engagement_score,
            change_from_previous=change_from_previous,
            change_from_baseline=change_from_baseline,
            engagement_trend=engagement_trend,
            evidence=evidence,
        )

    def extract_from_raw(
        self,
        raw_input: Mapping[str, Any],
        history: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> EngagementFeatures:
        """Convenience helper routing raw dictionary inputs through preprocessing."""
        preprocessed = preprocess_interaction(raw_input)
        prep_history = (
            [preprocess_interaction(h) for h in history] if history else None
        )
        return self.extract(preprocessed, history=prep_history)

    def extract_batch(
        self,
        interactions: Iterable[PreprocessedInteraction],
    ) -> list[EngagementFeatures]:
        """Extracts engagement features for an iterable of PreprocessedInteraction records."""
        return [self.extract(item) for item in interactions]


_DEFAULT_ENGAGEMENT_EXTRACTOR = EngagementFeatureExtractor()


def extract_engagement_features(
    interaction: PreprocessedInteraction,
    history: Optional[Sequence[PreprocessedInteraction]] = None,
    config: Optional[EngagementConfig] = None,
    extractor: Optional[EngagementFeatureExtractor] = None,
) -> EngagementFeatures:
    """Convenience functional interface for engagement feature extraction."""
    if extractor is not None:
        return extractor.extract(interaction, history=history)
    if config is not None:
        return EngagementFeatureExtractor(config=config).extract(
            interaction, history=history
        )
    return _DEFAULT_ENGAGEMENT_EXTRACTOR.extract(interaction, history=history)


def extract_engagement_features_batch(
    interactions: Iterable[PreprocessedInteraction],
    config: Optional[EngagementConfig] = None,
    extractor: Optional[EngagementFeatureExtractor] = None,
) -> list[EngagementFeatures]:
    """Convenience functional interface for batch engagement feature extraction."""
    e = extractor or (
        EngagementFeatureExtractor(config=config)
        if config is not None
        else _DEFAULT_ENGAGEMENT_EXTRACTOR
    )
    return e.extract_batch(interactions)
