from backend.voice.response_latency import calculate_response_latency
from backend.voice.vad import SpeechSegment, VADResult


def make_vad_result(
    start_seconds: float = 2.0,
    usable: bool = True,
) -> VADResult:
    segments = (
        [SpeechSegment(start_seconds=start_seconds, end_seconds=4.0)]
        if usable
        else []
    )

    return VADResult(
        usable=usable,
        speech_segments=segments,
        speech_duration_seconds=2.0 if usable else 0.0,
        speech_ratio=0.5 if usable else 0.0,
        silence_ratio=0.5 if usable else 1.0,
        reason=None if usable else "NO_SPEECH_DETECTED",
    )


def test_response_latency_is_calculated_from_prompt_end_to_first_speech():
    vad_result = make_vad_result(start_seconds=2.0)

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=1.2,
    )

    assert result.response_latency == 0.8
    assert result.reason is None


def test_response_latency_can_be_zero():
    vad_result = make_vad_result(start_seconds=2.0)

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=2.0,
    )

    assert result.response_latency == 0.0


def test_missing_prompt_end_returns_none():
    vad_result = make_vad_result()

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=None,
    )

    assert result.response_latency is None
    assert result.reason == "PROMPT_END_UNAVAILABLE"


def test_unusable_vad_returns_none():
    vad_result = make_vad_result(usable=False)

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=1.0,
    )

    assert result.response_latency is None
    assert result.reason == "VAD_UNUSABLE"


def test_no_speech_segments_returns_none():
    vad_result = VADResult(
        usable=True,
        speech_segments=[],
        speech_duration_seconds=0.0,
        speech_ratio=0.0,
        silence_ratio=1.0,
        reason=None,
    )

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=1.0,
    )

    assert result.response_latency is None
    assert result.reason == "NO_SPEECH_SEGMENTS"


def test_negative_prompt_end_is_rejected():
    vad_result = make_vad_result()

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=-1.0,
    )

    assert result.response_latency is None
    assert result.reason == "INVALID_PROMPT_END"


def test_negative_latency_is_rejected():
    vad_result = make_vad_result(start_seconds=1.0)

    result = calculate_response_latency(
        vad_result,
        prompt_end_seconds=2.0,
    )

    assert result.response_latency is None
    assert result.reason == "INVALID_NEGATIVE_LATENCY"