import wave

import numpy as np

from backend.voice.pitch_variability import calculate_pitch_variability
from backend.voice.vad import SpeechSegment, VADResult


def create_wav(path, frequency=200.0, duration=2.0):
    sample_rate = 16000

    samples = np.arange(
        int(sample_rate * duration)
    )

    audio = (
        0.25
        * np.sin(
            2 * np.pi * frequency * samples / sample_rate
        )
    )

    audio = np.int16(audio * 32767)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())


def make_vad(duration=2.0):
    segment = SpeechSegment(
        start_seconds=0.0,
        end_seconds=duration,
    )

    return VADResult(
        usable=True,
        speech_segments=[segment],
        speech_duration_seconds=duration,
        speech_ratio=1.0,
        silence_ratio=0.0,
        reason=None,
    )


def test_constant_pitch_has_low_variability(tmp_path):
    audio_path = tmp_path / "constant_pitch.wav"

    create_wav(
        audio_path,
        frequency=200.0,
        duration=2.0,
    )

    result = calculate_pitch_variability(
        audio_path,
        make_vad(),
    )

    assert result.pitch_variability is not None
    assert result.pitch_variability >= 0
    assert result.pitch_variability < 0.05

    assert result.mean_f0_hz is not None
    assert 190 <= result.mean_f0_hz <= 210

    assert result.valid_frame_count > 0
    assert result.reason is None


def test_missing_audio_returns_null(tmp_path):
    audio_path = tmp_path / "missing.wav"

    result = calculate_pitch_variability(
        audio_path,
        make_vad(),
    )

    assert result.pitch_variability is None
    assert result.mean_f0_hz is None
    assert result.std_f0_hz is None
    assert result.reason == "AUDIO_FILE_NOT_FOUND"


def test_unusable_vad_returns_null(tmp_path):
    audio_path = tmp_path / "audio.wav"

    create_wav(audio_path)

    vad_result = VADResult(
        usable=False,
        speech_segments=[],
        speech_duration_seconds=0.0,
        speech_ratio=0.0,
        silence_ratio=1.0,
        reason="NO_SPEECH_DETECTED",
    )

    result = calculate_pitch_variability(
        audio_path,
        vad_result,
    )

    assert result.pitch_variability is None
    assert result.reason == "VAD_UNUSABLE"


def test_silence_has_no_valid_pitch(tmp_path):
    audio_path = tmp_path / "silence.wav"

    create_wav(
        audio_path,
        frequency=0.0,
        duration=2.0,
    )

    result = calculate_pitch_variability(
        audio_path,
        make_vad(),
    )

    assert result.pitch_variability is None
    assert result.valid_frame_count == 0
    assert result.reason == "NO_VALID_PITCH"


def test_pitch_variability_is_non_negative(tmp_path):
    audio_path = tmp_path / "pitch.wav"

    create_wav(
        audio_path,
        frequency=180.0,
        duration=2.0,
    )

    result = calculate_pitch_variability(
        audio_path,
        make_vad(),
    )

    assert result.pitch_variability is not None
    assert result.pitch_variability >= 0