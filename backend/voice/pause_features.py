from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.voice.vad import VADResult


MIN_PAUSE_SECONDS = 0.250


@dataclass
class PauseFeatureResult:
    pause_ratio: Optional[float]
    total_pause_seconds: Optional[float]
    pause_count: int
    reason: Optional[str] = None


def calculate_pause_features(
    vad_result: VADResult,
    recording_duration_seconds: float,
) -> PauseFeatureResult:
    """
    Calculate meaningful pause features from VAD speech segments.

    A pause is counted only when it occurs between two detected speech
    segments and is at least MIN_PAUSE_SECONDS long.

    pause_ratio = total meaningful pause duration /
                  usable recording duration
    """

    if recording_duration_seconds <= 0:
        return PauseFeatureResult(
            pause_ratio=None,
            total_pause_seconds=None,
            pause_count=0,
            reason="INVALID_RECORDING_DURATION",
        )

    if not vad_result.usable:
        return PauseFeatureResult(
            pause_ratio=None,
            total_pause_seconds=None,
            pause_count=0,
            reason="VAD_UNUSABLE",
        )

    segments = vad_result.speech_segments

    if len(segments) < 2:
        return PauseFeatureResult(
            pause_ratio=0.0,
            total_pause_seconds=0.0,
            pause_count=0,
            reason=None,
        )

    total_pause = 0.0
    pause_count = 0

    for previous, current in zip(segments, segments[1:]):
        gap = current.start_seconds - previous.end_seconds

        if gap >= MIN_PAUSE_SECONDS:
            total_pause += gap
            pause_count += 1

    pause_ratio = total_pause / recording_duration_seconds

    # Defensive numerical bound.
    pause_ratio = max(0.0, min(1.0, pause_ratio))

    return PauseFeatureResult(
        pause_ratio=pause_ratio,
        total_pause_seconds=total_pause,
        pause_count=pause_count,
        reason=None,
    )