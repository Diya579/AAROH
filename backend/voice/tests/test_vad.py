from pathlib import Path
import wave

import numpy as np

from backend.voice.vad import VADService


def create_wav(
    path: Path,
    duration_seconds: float,
    frequency: float = 440.0,
    amplitude: float = 0.2,
):
    sample_rate = 16000
    sample_count = int(sample_rate * duration_seconds)

    t = np.arange(sample_count) / sample_rate
    audio = amplitude * np.sin(2 * np.pi * frequency * t)

    pcm = np.int16(audio * 32767)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def create_silence(path: Path, duration_seconds: float):
    sample_rate = 16000
    sample_count = int(sample_rate * duration_seconds)

    pcm = np.zeros(sample_count, dtype=np.int16)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def test_missing_file():
    result = VADService().detect("does_not_exist.wav")

    assert result.usable is False
    assert result.reason == "AUDIO_FILE_NOT_FOUND"


def test_empty_audio(tmp_path):
    path = tmp_path / "empty.wav"
    path.write_bytes(b"")

    result = VADService().detect(path)

    assert result.usable is False


def test_silence(tmp_path):
    path = tmp_path / "silence.wav"
    create_silence(path, 2.0)

    result = VADService().detect(path)

    assert result.usable is False
    assert result.reason == "NO_SPEECH_DETECTED"


def test_audio_with_signal(tmp_path):
    path = tmp_path / "signal.wav"
    create_wav(path, 2.0)

    result = VADService().detect(path)

    assert result.speech_duration_seconds >= 0
    assert result.speech_ratio is not None
    assert result.silence_ratio is not None

    assert 0.0 <= result.speech_ratio <= 1.0
    assert 0.0 <= result.silence_ratio <= 1.0