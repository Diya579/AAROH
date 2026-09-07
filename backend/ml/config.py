"""Configurable ML inference settings.

Horizon, confidence floors, and abstention cutoffs live here so they are
not hard-coded throughout training or inference code.
"""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_TARGET_HORIZON_DAYS = 7


@dataclass(frozen=True)
class InferenceConfig:
    """Runtime configuration for ML inference.

    ``target_horizon_days`` is the escalation window associated with
    ``prediction.escalation_probability``. The AAROH baseline uses 7 days.
    """

    target_horizon_days: int = DEFAULT_TARGET_HORIZON_DAYS

    # Overall prediction confidence at or above this value may be SUCCESS.
    min_success_confidence: float = 0.50

    # Below this overall confidence the model abstains (no fabricated prediction).
    abstain_below_confidence: float = 0.30

    # Distress confidence at or above this value is treated as usable.
    min_distress_confidence: float = 0.50

    # Minimum longitudinal observations before baseline_deviation is required.
    min_observations_for_baseline: int = 2

    def __post_init__(self) -> None:
        if self.target_horizon_days <= 0:
            raise ValueError("target_horizon_days must be greater than 0")

        for name in (
            "min_success_confidence",
            "abstain_below_confidence",
            "min_distress_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0]")

        if self.abstain_below_confidence > self.min_success_confidence:
            raise ValueError(
                "abstain_below_confidence must be <= min_success_confidence"
            )

        if self.min_observations_for_baseline < 1:
            raise ValueError("min_observations_for_baseline must be >= 1")
