from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.voice.vad import VADResult


@dataclass
class ResponseLatencyResult:
    response_latency: Optional[float]
    reason: Optional[str] = None


def calculate_response_latency(
    vad_result: VADResult,
    prompt_end_seconds: Optional[float],
) -> ResponseLatencyResult:
    """
    Calculate response latency from prompt end to first valid speech.

    response_latency = first_speech_start - prompt_end

    Returns None when:
    - prompt-end timing is unavailable
    - VAD is unusable
    - no speech segment is available
    - calculated latency would be negative
    """

    if prompt_end_seconds is None:
        return ResponseLatencyResult(
            response_latency=None,
            reason="PROMPT_END_UNAVAILABLE",
        )

    if prompt_end_seconds < 0:
        return ResponseLatencyResult(
            response_latency=None,
            reason="INVALID_PROMPT_END",
        )

    if not vad_result.usable:
        return ResponseLatencyResult(
            response_latency=None,
            reason="VAD_UNUSABLE",
        )

    if not vad_result.speech_segments:
        return ResponseLatencyResult(
            response_latency=None,
            reason="NO_SPEECH_SEGMENTS",
        )

    first_speech_start = vad_result.speech_segments[0].start_seconds
    latency = first_speech_start - prompt_end_seconds

    if latency < 0:
        return ResponseLatencyResult(
            response_latency=None,
            reason="INVALID_NEGATIVE_LATENCY",
        )

    return ResponseLatencyResult(
        response_latency=latency,
        reason=None,
    )