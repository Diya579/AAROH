from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional


MIN_VALID_SESSIONS = 3

VOICE_FEATURE_NAMES = (
    "speech_rate",
    "pause_ratio",
    "response_latency",
    "pitch_variability",
    "energy_variation",
)


@dataclass
class VoiceBaseline:
    speech_rate: Optional[float]
    pause_ratio: Optional[float]
    response_latency: Optional[float]
    pitch_variability: Optional[float]
    energy_variation: Optional[float]
    valid_session_count: int


@dataclass
class BaselineDeviationResult:
    baseline_deviation: Optional[float]
    valid_session_count: int
    usable_feature_count: int
    reason: Optional[str] = None


def _mean_available(values: Sequence[Optional[float]]) -> Optional[float]:
    valid_values = [
        value
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return sum(valid_values) / len(valid_values)


def calculate_voice_baseline(
    sessions: Sequence[Mapping[str, Optional[float]]],
) -> VoiceBaseline:
    """
    Calculate a historical voice baseline.

    Only sessions represented in `sessions` should be supplied by the caller
    after filtering for GOOD audio quality.

    Missing feature values remain missing and are never converted to zero.
    """

    valid_session_count = len(sessions)

    if valid_session_count < MIN_VALID_SESSIONS:
        return VoiceBaseline(
            speech_rate=None,
            pause_ratio=None,
            response_latency=None,
            pitch_variability=None,
            energy_variation=None,
            valid_session_count=valid_session_count,
        )

    return VoiceBaseline(
        speech_rate=_mean_available(
            [session.get("speech_rate") for session in sessions]
        ),
        pause_ratio=_mean_available(
            [session.get("pause_ratio") for session in sessions]
        ),
        response_latency=_mean_available(
            [session.get("response_latency") for session in sessions]
        ),
        pitch_variability=_mean_available(
            [session.get("pitch_variability") for session in sessions]
        ),
        energy_variation=_mean_available(
            [session.get("energy_variation") for session in sessions]
        ),
        valid_session_count=valid_session_count,
    )


def _relative_deviation(
    current: Optional[float],
    baseline: Optional[float],
) -> Optional[float]:
    """
    Calculate absolute relative deviation from baseline.

    Returns None when either value is unavailable or the baseline is zero.
    """

    if current is None or baseline is None:
        return None

    if baseline == 0:
        return None

    return abs(current - baseline) / abs(baseline)


def calculate_baseline_deviation(
    current_features: Mapping[str, Optional[float]],
    baseline: VoiceBaseline,
) -> BaselineDeviationResult:
    """
    Calculate normalized deviation of the current voice features from baseline.

    The result is the mean of available feature-level relative deviations.

    Missing features are excluded rather than treated as zero.
    """

    if baseline.valid_session_count < MIN_VALID_SESSIONS:
        return BaselineDeviationResult(
            baseline_deviation=None,
            valid_session_count=baseline.valid_session_count,
            usable_feature_count=0,
            reason="INSUFFICIENT_VALID_SESSIONS",
        )

    baseline_values: dict[str, Optional[float]] = {
        "speech_rate": baseline.speech_rate,
        "pause_ratio": baseline.pause_ratio,
        "response_latency": baseline.response_latency,
        "pitch_variability": baseline.pitch_variability,
        "energy_variation": baseline.energy_variation,
    }

    deviations: list[float] = []

    for feature_name in VOICE_FEATURE_NAMES:
        deviation = _relative_deviation(
            current_features.get(feature_name),
            baseline_values[feature_name],
        )

        if deviation is not None:
            deviations.append(deviation)

    if not deviations:
        return BaselineDeviationResult(
            baseline_deviation=None,
            valid_session_count=baseline.valid_session_count,
            usable_feature_count=0,
            reason="NO_COMPARABLE_FEATURES",
        )

    baseline_deviation = sum(deviations) / len(deviations)

    # Avoid floating-point noise such as:
    # 8.326672684688672e-17 instead of exactly 0.0
    if abs(baseline_deviation) < 1e-12:
        baseline_deviation = 0.0

    return BaselineDeviationResult(
        baseline_deviation=max(0.0, baseline_deviation),
        valid_session_count=baseline.valid_session_count,
        usable_feature_count=len(deviations),
        reason=None,
    )