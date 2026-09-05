import wave

import numpy as np

from backend.voice.energy_variation import calculate_energy_variation
from backend.voice.vad import SpeechSegment, VADResult


def create_wav(path, amplitude=0.25, duration=2.0):
    sample_rate = 16000

    samples = np.arange(
        int(sample_rate * duration)
    )

    audio = (
        amplitude
        * np.sin(
            2 * np.pi * 200.0 * samples / sample_rate
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


def test_constant_energy_has_low_variability(tmp_path):
    audio_path = tmp_path / "constant_energy.wav"

    create_wav(
        audio_path,
        amplitude=0.25,
        duration=2.0,
    )

    result = calculate_energy_variation(
        audio_path,
        make_vad(),
    )

    assert result.energy_variation is not None
    assert result.energy_variation >= 0
    assert result.energy_variation < 0.05

    assert result.mean_rms_energy is not None
    assert result.mean_rms_energy > 0

    assert result.valid_frame_count > 0
    assert result.reason is None


def test_missing_audio_returns_null(tmp_path):
    audio_path = tmp_path / "missing.wav"

    result = calculate_energy_variation(
        audio_path,
        make_vad(),
    )

    assert result.energy_variation is None
    assert result.mean_rms_energy is None
    assert result.std_rms_energy is None
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

    result = calculate_energy_variation(
        audio_path,
        vad_result,
    )

    assert result.energy_variation is None
    assert result.reason == "VAD_UNUSABLE"


def test_silence_has_no_valid_energy(tmp_path):
    audio_path = tmp_path / "silence.wav"

    create_wav(
        audio_path,
        amplitude=0.0,
        duration=2.0,
    )

    result = calculate_energy_variation(
        audio_path,
        make_vad(),
    )

    assert result.energy_variation is None
    assert result.valid_frame_count == 0
    assert result.reason == "NO_VALID_ENERGY"


def test_energy_variation_is_non_negative(tmp_path):
    audio_path = tmp_path / "energy.wav"

    create_wav(
        audio_path,
        amplitude=0.20,
        duration=2.0,
    )

    result = calculate_energy_variation(
        audio_path,
        make_vad(),
    )

    assert result.energy_variation is not None
    assert result.energy_variation >= 0