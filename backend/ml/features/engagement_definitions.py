"""Centralized definitions and configurable settings for engagement features (Slice 2.4).

Single source of truth for:
- Enums (EngagementTrend, EngagementMetric)
- Default thresholds and configurable EngagementConfig (User Modification 1)
- Engagement score definitions (User Modification 2: measures interaction adherence, NOT distress)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Default thresholds (exposed as configurable constants)
DEFAULT_LONG_RESPONSE_DELAY_DAYS = 5.0
DEFAULT_MISSED_CHECKIN_ALERT_STREAK = 2
DEFAULT_LOW_CONSISTENCY_THRESHOLD = 0.50
DEFAULT_NOTABLE_ENGAGEMENT_DROP = 0.25
DEFAULT_RECENT_ACTIVITY_WINDOW_DAYS = 14
DEFAULT_TREND_SHIFT_THRESHOLD = 0.20


class EngagementTrend(str, Enum):
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    IMPROVING = "IMPROVING"


class EngagementMetric(str, Enum):
    COMPLETED_CHECKIN = "completed_checkin"
    MISSED_CHECKIN = "missed_checkin"
    MISSED_CHECKIN_STREAK = "missed_checkin_streak"
    CHECKIN_CONSISTENCY = "checkin_consistency"
    RESPONSE_DELAY = "response_delay"
    AVERAGE_RESPONSE_DELAY = "average_response_delay"
    RESPONSE_FREQUENCY = "response_frequency"
    ENGAGEMENT_DROP = "engagement_drop"
    INTERACTION_COUNT = "interaction_count"
    RECENT_ACTIVITY_COUNT = "recent_activity_count"
    INACTIVITY_DURATION = "inactivity_duration"
    ENGAGEMENT_SCORE = "engagement_score"


@dataclass(frozen=True)
class EngagementConfig:
    """Configurable parameters for engagement feature extraction (User Modification 1).

    Allows future model calibration to adjust operational cutoffs without modifying
    the extractor code.
    """

    long_response_delay_days: float = DEFAULT_LONG_RESPONSE_DELAY_DAYS
    missed_checkin_alert_streak: int = DEFAULT_MISSED_CHECKIN_ALERT_STREAK
    low_consistency_threshold: float = DEFAULT_LOW_CONSISTENCY_THRESHOLD
    notable_engagement_drop: float = DEFAULT_NOTABLE_ENGAGEMENT_DROP
    recent_activity_window_days: int = DEFAULT_RECENT_ACTIVITY_WINDOW_DAYS
    trend_shift_threshold: float = DEFAULT_TREND_SHIFT_THRESHOLD

    def __post_init__(self) -> None:
        if self.long_response_delay_days <= 0:
            raise ValueError("long_response_delay_days must be positive")
        if self.missed_checkin_alert_streak < 1:
            raise ValueError("missed_checkin_alert_streak must be >= 1")
        if not 0.0 <= self.low_consistency_threshold <= 1.0:
            raise ValueError("low_consistency_threshold must be in [0.0, 1.0]")
        if not 0.0 <= self.notable_engagement_drop <= 1.0:
            raise ValueError("notable_engagement_drop must be in [0.0, 1.0]")
        if self.recent_activity_window_days < 1:
            raise ValueError("recent_activity_window_days must be >= 1")
        if not 0.0 <= self.trend_shift_threshold <= 1.0:
            raise ValueError("trend_shift_threshold must be in [0.0, 1.0]")
