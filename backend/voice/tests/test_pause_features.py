from backend.voice.pause_features import calculate_pause_features
from backend.voice.vad import SpeechSegment, VADResult


def make_vad(segments, usable=True):
    return VADResult(
        usable=usable,
        speech_segments=segments,
        speech_duration_seconds=sum(
            segment.duration_seconds for segment in segments
        ),
        speech_ratio=None,
        silence_ratio=None,
        reason=None if usable else "VAD_UNUSABLE",
    )


def test_pause_between_speech_segments_is_detected():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
            SpeechSegment(2.5, 4.5),
        ]
    )

    result = calculate_pause_features(vad_result, 5.0)

    assert result.pause_count == 1
    assert result.total_pause_seconds == 0.5
    assert result.pause_ratio == 0.1
    assert result.reason is None


def test_pause_shorter_than_threshold_is_ignored():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
            SpeechSegment(2.2, 4.5),
        ]
    )

    result = calculate_pause_features(vad_result, 5.0)

    assert result.pause_count == 0
    assert result.total_pause_seconds == 0.0
    assert result.pause_ratio == 0.0


def test_single_speech_segment_has_no_pause():
    vad_result = make_vad(
        [
            SpeechSegment(0.5, 4.5),
        ]
    )

    result = calculate_pause_features(vad_result, 5.0)

    assert result.pause_count == 0
    assert result.total_pause_seconds == 0.0
    assert result.pause_ratio == 0.0


def test_unusable_vad_returns_null_pause_ratio():
    vad_result = make_vad([], usable=False)

    result = calculate_pause_features(vad_result, 5.0)

    assert result.pause_ratio is None
    assert result.total_pause_seconds is None
    assert result.pause_count == 0
    assert result.reason == "VAD_UNUSABLE"


def test_invalid_duration_returns_null_pause_ratio():
    vad_result = make_vad(
        [
            SpeechSegment(0.0, 2.0),
            SpeechSegment(2.5, 4.5),
        ]
    )

    result = calculate_pause_features(vad_result, 0.0)

    assert result.pause_ratio is None
    assert result.total_pause_seconds is None
    assert result.reason == "INVALID_RECORDING_DURATION"