"""Centralized definitions and configurable settings for longitudinal features (Slice 2.5).

Single source of truth for:
- Enums (LongitudinalTrend, LongitudinalMetric)
- Default thresholds and configurable LongitudinalConfig (User Modification 1)
- Centralized trend classification logic (User Modification 1)
- Contract trajectory mapping
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Default thresholds (exposed as configurable constants)
DEFAULT_MIN_OBSERVATIONS_FOR_TREND = 2
DEFAULT_RAPID_SHIFT_THRESHOLD = 0.35
DEFAULT_NOTABLE_SHIFT_THRESHOLD = 0.20
DEFAULT_HIGH_DISTRESS_THRESHOLD = 0.65
DEFAULT_RAPID_VELOCITY_THRESHOLD = 0.05  # daily rate of change
DEFAULT_MODERATE_VELOCITY_THRESHOLD = 0.02  # daily rate of change
DEFAULT_VOLATILITY_ALERT_THRESHOLD = 0.20


class LongitudinalTrend(str, Enum):
    UNKNOWN = "UNKNOWN"
    STABLE = "STABLE"
    IMPROVING = "IMPROVING"
    WORSENING = "WORSENING"
    RAPIDLY_IMPROVING = "RAPIDLY_IMPROVING"
    RAPIDLY_WORSENING = "RAPIDLY_WORSENING"


class LongitudinalMetric(str, Enum):
    OBSERVATION_COUNT = "observation_count"
    HISTORY_SPAN_DAYS = "history_span_days"
    CURRENT_DISTRESS = "current_distress"
    BASELINE_DISTRESS = "baseline_distress"
    PREVIOUS_DISTRESS = "previous_distress"
    DELTA_FROM_BASELINE = "delta_from_baseline"
    DELTA_FROM_PREVIOUS = "delta_from_previous"
    DISTRESS_VELOCITY = "distress_velocity"
    DISTRESS_ACCELERATION = "distress_acceleration"
    DISTRESS_VOLATILITY = "distress_volatility"
    PEAK_DISTRESS = "peak_distress"
    TROUGH_DISTRESS = "trough_distress"
    SUSTAINED_DISTRESS_COUNT = "sustained_distress_count"
    LONGITUDINAL_TREND = "longitudinal_trend"


@dataclass(frozen=True)
class LongitudinalConfig:
    """Configurable parameters for longitudinal feature extraction (User Modification 1).

    Allows future model calibration and escalation policies to adjust operational
    cutoffs without duplicating or modifying extractor code.
    """

    min_observations_for_trend: int = DEFAULT_MIN_OBSERVATIONS_FOR_TREND
    rapid_shift_threshold: float = DEFAULT_RAPID_SHIFT_THRESHOLD
    notable_shift_threshold: float = DEFAULT_NOTABLE_SHIFT_THRESHOLD
    high_distress_threshold: float = DEFAULT_HIGH_DISTRESS_THRESHOLD
    rapid_velocity_threshold: float = DEFAULT_RAPID_VELOCITY_THRESHOLD
    moderate_velocity_threshold: float = DEFAULT_MODERATE_VELOCITY_THRESHOLD
    volatility_alert_threshold: float = DEFAULT_VOLATILITY_ALERT_THRESHOLD

    def __post_init__(self) -> None:
        if self.min_observations_for_trend < 1:
            raise ValueError("min_observations_for_trend must be >= 1")
        if not 0.0 <= self.rapid_shift_threshold <= 1.0:
            raise ValueError("rapid_shift_threshold must be in [0.0, 1.0]")
        if not 0.0 <= self.notable_shift_threshold <= 1.0:
            raise ValueError("notable_shift_threshold must be in [0.0, 1.0]")
        if self.notable_shift_threshold > self.rapid_shift_threshold:
            raise ValueError("notable_shift_threshold cannot exceed rapid_shift_threshold")
        if not 0.0 <= self.high_distress_threshold <= 1.0:
            raise ValueError("high_distress_threshold must be in [0.0, 1.0]")
        if self.rapid_velocity_threshold <= 0:
            raise ValueError("rapid_velocity_threshold must be positive")
        if self.moderate_velocity_threshold <= 0:
            raise ValueError("moderate_velocity_threshold must be positive")
        if self.moderate_velocity_threshold > self.rapid_velocity_threshold:
            raise ValueError("moderate_velocity_threshold cannot exceed rapid_velocity_threshold")
        if not 0.0 <= self.volatility_alert_threshold <= 1.0:
            raise ValueError("volatility_alert_threshold must be in [0.0, 1.0]")


def classify_longitudinal_trend(
    delta_previous: Optional[float],
    delta_baseline: Optional[float],
    velocity: Optional[float],
    config: Optional[LongitudinalConfig] = None,
    observation_count: int = 1,
) -> LongitudinalTrend:
    """Classifies longitudinal trajectory trend using centralized thresholds (User Modification 1).

    Returns LongitudinalTrend.UNKNOWN if observations are fewer than min_observations_for_trend
    or if all comparative signals are missing (User Modification 3).
    """
    cfg = config or LongitudinalConfig()

    if observation_count < cfg.min_observations_for_trend:
        return LongitudinalTrend.UNKNOWN

    if delta_previous is None and delta_baseline is None and velocity is None:
        return LongitudinalTrend.UNKNOWN

    # 1. Rapid worsening
    if (delta_previous is not None and delta_previous >= cfg.rapid_shift_threshold) or (
        velocity is not None and velocity >= cfg.rapid_velocity_threshold
    ):
        return LongitudinalTrend.RAPIDLY_WORSENING

    # 2. Rapid improving
    if (delta_previous is not None and delta_previous <= -cfg.rapid_shift_threshold) or (
        velocity is not None and velocity <= -cfg.rapid_velocity_threshold
    ):
        return LongitudinalTrend.RAPIDLY_IMPROVING

    # 3. Moderate worsening
    if (
        (delta_previous is not None and delta_previous >= cfg.notable_shift_threshold)
        or (delta_baseline is not None and delta_baseline >= cfg.notable_shift_threshold)
        or (velocity is not None and velocity >= cfg.moderate_velocity_threshold)
    ):
        return LongitudinalTrend.WORSENING

    # 4. Moderate improving
    if (
        (delta_previous is not None and delta_previous <= -cfg.notable_shift_threshold)
        or (delta_baseline is not None and delta_baseline <= -cfg.notable_shift_threshold)
        or (velocity is not None and velocity <= -cfg.moderate_velocity_threshold)
    ):
        return LongitudinalTrend.IMPROVING

    # 5. Stable
    return LongitudinalTrend.STABLE
