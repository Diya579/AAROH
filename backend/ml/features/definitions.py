"""Centralized definitions and constants for behavioural features (Slice 2.3).

Single source of truth for:
- Likert scale boundaries (1–5) and normalization
- Metric names and directionality (higher = worse)
- Distress thresholds and significant shift criteria for explainability
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

MIN_LIKERT_RATING = 1
MAX_LIKERT_RATING = 5
LIKERT_SPAN = MAX_LIKERT_RATING - MIN_LIKERT_RATING  # 4

# Significant deviation threshold for generating explainability flags
NOTABLE_SHIFT_THRESHOLD = 0.25

# High distress threshold
HIGH_DISTRESS_THRESHOLD = 0.65


class BehaviouralMetric(str, Enum):
    SAFETY_DISTRESS = "safety_distress"
    SLEEP_DISTURBANCE = "sleep_disturbance"
    FEAR_INTENSITY = "fear_intensity"
    LOW_SOCIAL_SUPPORT = "low_social_support"
    HELP_REQUESTED = "help_requested"
    COMPOSITE_DISTRESS = "composite_distress"


# Metrics that require inversion so that 1.0 uniformly represents maximal distress:
# In raw responses:
#   safety_response: 5 = very safe (distress 0.0), 1 = very unsafe (distress 1.0)
#   social_support: 5 = strong support (distress 0.0), 1 = no support (distress 1.0)
INVERTED_METRICS = frozenset(
    {
        "safety_response",
        "social_support",
        BehaviouralMetric.SAFETY_DISTRESS.value,
        BehaviouralMetric.LOW_SOCIAL_SUPPORT.value,
    }
)

# Direct metrics where higher rating = higher distress:
#   sleep_disruption: 5 = severe disruption (distress 1.0)
#   fear_level: 5 = extreme fear (distress 1.0)
DIRECT_METRICS = frozenset(
    {
        "sleep_disruption",
        "fear_level",
        BehaviouralMetric.SLEEP_DISTURBANCE.value,
        BehaviouralMetric.FEAR_INTENSITY.value,
    }
)

ALL_BEHAVIOURAL_INPUT_FIELDS = (
    "safety_response",
    "sleep_disruption",
    "fear_level",
    "social_support",
)


def normalize_likert_rating(
    value: Optional[float | int], *, invert: bool = False
) -> Optional[float]:
    """Normalizes a 1-5 Likert score into [0.0, 1.0].

    Preserves None explicitly (None != 0).
    When invert is True: 1 -> 1.0, 5 -> 0.0.
    When invert is False: 1 -> 0.0, 5 -> 1.0.
    """
    if value is None:
        return None

    # Clamp value safely within valid scale bounds
    clamped = max(float(MIN_LIKERT_RATING), min(float(MAX_LIKERT_RATING), float(value)))
    normalized = (clamped - MIN_LIKERT_RATING) / float(LIKERT_SPAN)

    if invert:
        normalized = 1.0 - normalized

    return round(normalized, 3)
