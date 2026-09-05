from typing import Optional

from backend.voice.baseline import (
    MIN_VALID_SESSIONS,
    calculate_baseline_deviation,
    calculate_voice_baseline,
)


def make_session(
    speech_rate: Optional[float] = 4.0,
    pause_ratio: Optional[float] = 0.2,
    response_latency: Optional[float] = 1.0,
    pitch_variability: Optional[float] = 0.1,
    energy_variation: Optional[float] = 0.2,
) -> dict[str, Optional[float]]:
    return {
        "speech_rate": speech_rate,
        "pause_ratio": pause_ratio,
        "response_latency": response_latency,
        "pitch_variability": pitch_variability,
        "energy_variation": energy_variation,
    }


def test_baseline_requires_three_valid_sessions():
    sessions = [
        make_session(),
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)

    assert len(sessions) < MIN_VALID_SESSIONS
    assert baseline.valid_session_count == 2

    assert baseline.speech_rate is None
    assert baseline.pause_ratio is None
    assert baseline.response_latency is None
    assert baseline.pitch_variability is None
    assert baseline.energy_variation is None


def test_baseline_is_calculated_from_three_sessions():
    sessions = [
        make_session(speech_rate=4.0),
        make_session(speech_rate=5.0),
        make_session(speech_rate=6.0),
    ]

    baseline = calculate_voice_baseline(sessions)

    assert baseline.valid_session_count == 3
    assert baseline.speech_rate == 5.0


def test_missing_features_are_not_treated_as_zero():
    sessions = [
        make_session(pitch_variability=None),
        make_session(pitch_variability=None),
        make_session(pitch_variability=0.3),
    ]

    baseline = calculate_voice_baseline(sessions)

    assert baseline.pitch_variability == 0.3


def test_identical_current_features_have_zero_deviation():
    sessions = [
        make_session(),
        make_session(),
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)
    current = make_session()

    result = calculate_baseline_deviation(
        current,
        baseline,
    )

    assert result.baseline_deviation == 0.0
    assert result.usable_feature_count == 5
    assert result.reason is None


def test_deviation_is_non_negative():
    sessions = [
        make_session(),
        make_session(),
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)

    current = make_session(
        speech_rate=6.0,
        pause_ratio=0.4,
        response_latency=2.0,
        pitch_variability=0.2,
        energy_variation=0.4,
    )

    result = calculate_baseline_deviation(
        current,
        baseline,
    )

    assert result.baseline_deviation is not None
    assert result.baseline_deviation >= 0


def test_missing_current_feature_is_excluded():
    sessions = [
        make_session(),
        make_session(),
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)

    current = make_session(
        speech_rate=None,
    )

    result = calculate_baseline_deviation(
        current,
        baseline,
    )

    assert result.baseline_deviation is not None
    assert result.usable_feature_count == 4


def test_insufficient_sessions_return_null_deviation():
    sessions = [
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)
    current = make_session()

    result = calculate_baseline_deviation(
        current,
        baseline,
    )

    assert result.baseline_deviation is None
    assert result.usable_feature_count == 0
    assert result.reason == "INSUFFICIENT_VALID_SESSIONS"


def test_no_comparable_features_return_null():
    sessions = [
        make_session(),
        make_session(),
        make_session(),
    ]

    baseline = calculate_voice_baseline(sessions)

    current: dict[str, Optional[float]] = {
        "speech_rate": None,
        "pause_ratio": None,
        "response_latency": None,
        "pitch_variability": None,
        "energy_variation": None,
    }

    result = calculate_baseline_deviation(
        current,
        baseline,
    )

    assert result.baseline_deviation is None
    assert result.usable_feature_count == 0
    assert result.reason == "NO_COMPARABLE_FEATURES"