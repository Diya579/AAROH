from backend.voice.speech_rate import calculate_speech_rate
from backend.voice.vad import SpeechSegment, VADResult


def make_vad(segments, usable=True):
    speech_duration = sum(
        segment.duration_seconds for segment in segments
    )

    return VADResult(
        usable=usable,
        speech_segments=segments,
        speech_duration_seconds=speech_duration,
        speech_ratio=None,
        silence_ratio=None,
        reason=None if usable else "VAD_UNUSABLE",
    )


def test_speech_rate_is_calculated():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
            SpeechSegment(2.5, 4.5),
        ]
    )

    result = calculate_speech_rate(
        vad_result,
        "hello world",
    )

    assert result.speech_duration_seconds == 4.0
    assert result.estimated_syllables == 3
    assert result.speech_rate == 0.75
    assert result.reason is None


def test_unusable_vad_returns_null():
    vad_result = make_vad([], usable=False)

    result = calculate_speech_rate(
        vad_result,
        "hello world",
    )

    assert result.speech_rate is None
    assert result.estimated_syllables is None
    assert result.reason == "VAD_UNUSABLE"


def test_missing_transcription_returns_null_rate():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
        ]
    )

    result = calculate_speech_rate(
        vad_result,
        None,
    )

    assert result.speech_rate is None
    assert result.estimated_syllables is None
    assert result.reason == "TRANSCRIPTION_UNAVAILABLE"


def test_no_speech_returns_null():
    vad_result = make_vad([])

    result = calculate_speech_rate(
        vad_result,
        "hello world",
    )

    assert result.speech_rate is None
    assert result.reason == "NO_SPEECH_DETECTED"


def test_indic_transcription_is_supported():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
        ]
    )

    result = calculate_speech_rate(
        vad_result,
        "आज मौसम बहुत अच्छा है",
    )

    assert result.estimated_syllables is not None
    assert result.estimated_syllables > 0

    assert result.speech_rate is not None
    assert result.speech_rate >= 0