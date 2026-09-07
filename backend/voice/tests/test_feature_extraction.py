from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Optional

from backend.voice.baseline import calculate_voice_baseline
from backend.voice.feature_extraction import VoiceFeatureExtractor
from backend.voice.vad import SpeechSegment, VADResult


class FakeVADService:
    def __init__(self, result: VADResult) -> None:
        self.result = result

    def detect(self, audio_path: str | Path) -> VADResult:
        return self.result


def make_vad_result() -> VADResult:
    return VADResult(
        usable=True,
        speech_segments=[
            SpeechSegment(
                start_seconds=0.5,
                end_seconds=2.0,
            ),
            SpeechSegment(
                start_seconds=2.5,
                end_seconds=4.5,
            ),
        ],
        speech_duration_seconds=3.5,
        speech_ratio=0.7,
        silence_ratio=0.3,
        reason=None,
    )


def make_session(
    speech_rate: Optional[float] = 4.0,
    pause_ratio: Optional[float] = 0.2,
    response_latency: Optional[float] = 0.5,
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


def create_test_wav(
    path: Path,
    duration_seconds: float = 5.0,
) -> None:
    sample_rate = 16000
    total_samples = int(sample_rate * duration_seconds)

    samples = [
        int(
            0.15
            * 32767
            * math.sin(2 * math.pi * 180 * index / sample_rate)
        )
        for index in range(total_samples)
    ]

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(
            b"".join(
                struct.pack("<h", sample)
                for sample in samples
            )
        )


def test_feature_extraction_returns_all_features(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "test.wav"
    create_test_wav(audio_path)

    extractor = VoiceFeatureExtractor(
        vad_service=FakeVADService(make_vad_result())
    )

    result = extractor.extract(
        audio_path=audio_path,
        transcription="आज मौसम बहुत अच्छा है",
        prompt_end_seconds=0.2,
    )

    assert result.usable is True

    assert result.speech_rate is not None
    assert result.pause_ratio is not None
    assert result.response_latency is not None
    assert result.pitch_variability is not None
    assert result.energy_variation is not None

    assert result.audio_quality is not None
    assert result.quality_level is not None

    assert result.baseline_deviation is None


def test_missing_transcription_preserves_missing_speech_rate(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "test.wav"
    create_test_wav(audio_path)

    extractor = VoiceFeatureExtractor(
        vad_service=FakeVADService(make_vad_result())
    )

    result = extractor.extract(
        audio_path=audio_path,
        transcription=None,
        prompt_end_seconds=0.2,
    )

    assert result.usable is True
    assert result.speech_rate is None
    assert "speech_rate:TRANSCRIPTION_UNAVAILABLE" in result.reasons


def test_missing_prompt_end_preserves_missing_latency(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "test.wav"
    create_test_wav(audio_path)

    extractor = VoiceFeatureExtractor(
        vad_service=FakeVADService(make_vad_result())
    )

    result = extractor.extract(
        audio_path=audio_path,
        transcription="आज मौसम बहुत अच्छा है",
        prompt_end_seconds=None,
    )

    assert result.usable is True
    assert result.response_latency is None
    assert "response_latency:PROMPT_END_UNAVAILABLE" in result.reasons


def test_insufficient_baseline_history_returns_null_deviation(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "test.wav"
    create_test_wav(audio_path)

    baseline = calculate_voice_baseline(
        [
            make_session(),
            make_session(),
        ]
    )

    extractor = VoiceFeatureExtractor(
        vad_service=FakeVADService(make_vad_result())
    )

    result = extractor.extract(
        audio_path=audio_path,
        transcription="आज मौसम बहुत अच्छा है",
        prompt_end_seconds=0.2,
        baseline=baseline,
    )

    assert result.usable is True
    assert result.baseline_deviation is None
    assert "INSUFFICIENT_VALID_SESSIONS" in result.reasons


def test_baseline_deviation_is_calculated_with_valid_history(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "test.wav"
    create_test_wav(audio_path)

    baseline = calculate_voice_baseline(
        [
            make_session(),
            make_session(),
            make_session(),
        ]
    )

    extractor = VoiceFeatureExtractor(
        vad_service=FakeVADService(make_vad_result())
    )

    result = extractor.extract(
        audio_path=audio_path,
        transcription="आज मौसम बहुत अच्छा है",
        prompt_end_seconds=0.2,
        baseline=baseline,
    )

    assert result.usable is True
    assert result.baseline_deviation is not None
    assert result.baseline_deviation >= 0.0