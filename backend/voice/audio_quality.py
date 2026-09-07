from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path


QUALITY_GOOD = "GOOD"
QUALITY_POOR_BUT_USABLE = "POOR_BUT_USABLE"
QUALITY_UNUSABLE = "UNUSABLE"

MIN_AUDIO_QUALITY = 0.0
MAX_AUDIO_QUALITY = 1.0

MIN_SPEECH_RMS = 0.005
CLIPPING_THRESHOLD = 0.99
SILENCE_THRESHOLD = 0.01


@dataclass
class AudioQualityResult:
    usable: bool
    quality_level: str
    audio_quality: float
    duration_seconds: float | None
    silence_ratio: float | None
    clipping_ratio: float | None
    rms_energy: float | None
    reason: str | None


def _read_pcm_samples(audio_path: Path) -> tuple[list[int], int, int]:
    """
    Read a PCM WAV file.

    Returns:
        samples, sample_rate, sample_width
    """
    with wave.open(str(audio_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        frame_count = wav.getnframes()
        raw_audio = wav.readframes(frame_count)

    if channels != 1:
        raise ValueError("EXPECTED_MONO_AUDIO")

    if sample_width != 2:
        raise ValueError("EXPECTED_16_BIT_AUDIO")

    samples = [
        int.from_bytes(
            raw_audio[index:index + 2],
            byteorder="little",
            signed=True,
        )
        for index in range(0, len(raw_audio), 2)
    ]

    return samples, sample_rate, sample_width


def _calculate_rms_energy(samples: list[int]) -> float:
    if not samples:
        return 0.0

    mean_square = sum(sample * sample for sample in samples) / len(samples)
    rms = math.sqrt(mean_square)

    # Normalize signed 16-bit PCM to 0-1.
    return rms / 32768.0


def _calculate_silence_ratio(
    samples: list[int],
    silence_threshold: float = SILENCE_THRESHOLD,
) -> float:
    if not samples:
        return 1.0

    normalized = [
        abs(sample) / 32768.0
        for sample in samples
    ]

    silent_samples = sum(
        amplitude < silence_threshold
        for amplitude in normalized
    )

    return silent_samples / len(normalized)


def _calculate_clipping_ratio(
    samples: list[int],
    clipping_threshold: float = CLIPPING_THRESHOLD,
) -> float:
    if not samples:
        return 0.0

    normalized = [
        abs(sample) / 32768.0
        for sample in samples
    ]

    clipped_samples = sum(
        amplitude >= clipping_threshold
        for amplitude in normalized
    )

    return clipped_samples / len(normalized)


def _calculate_quality_score(
    rms_energy: float,
    silence_ratio: float,
    clipping_ratio: float,
) -> float:
    """
    Calculate an operational audio-quality score.

    This score measures recording suitability only.
    It is NOT a distress, emotion, or mental-health score.
    """

    score = 1.0

    # Very weak signal.
    if rms_energy < MIN_SPEECH_RMS:
        score -= 0.60
    elif rms_energy < 0.02:
        score -= 0.15

    # Excessive silence.
    if silence_ratio > 0.90:
        score -= 0.30
    elif silence_ratio > 0.70:
        score -= 0.15

    # Clipping.
    if clipping_ratio > 0.05:
        score -= 0.30
    elif clipping_ratio > 0.01:
        score -= 0.10

    return max(
        MIN_AUDIO_QUALITY,
        min(MAX_AUDIO_QUALITY, score),
    )


def assess_audio_quality(
    audio_path: str | Path,
) -> AudioQualityResult:
    """
    Assess the quality of a preprocessed mono 16-bit PCM WAV file.

    Quality levels:
        GOOD
        POOR_BUT_USABLE
        UNUSABLE
    """

    path = Path(audio_path)

    if not path.exists():
        return AudioQualityResult(
            usable=False,
            quality_level=QUALITY_UNUSABLE,
            audio_quality=0.0,
            duration_seconds=None,
            silence_ratio=None,
            clipping_ratio=None,
            rms_energy=None,
            reason="AUDIO_FILE_NOT_FOUND",
        )

    try:
        samples, sample_rate, sample_width = _read_pcm_samples(path)
    except (OSError, ValueError):
        return AudioQualityResult(
            usable=False,
            quality_level=QUALITY_UNUSABLE,
            audio_quality=0.0,
            duration_seconds=None,
            silence_ratio=None,
            clipping_ratio=None,
            rms_energy=None,
            reason="INVALID_AUDIO_FORMAT",
        )

    if not samples:
        return AudioQualityResult(
            usable=False,
            quality_level=QUALITY_UNUSABLE,
            audio_quality=0.0,
            duration_seconds=0.0,
            silence_ratio=1.0,
            clipping_ratio=0.0,
            rms_energy=0.0,
            reason="NO_AUDIO_SAMPLES",
        )

    duration_seconds = len(samples) / sample_rate

    rms_energy = _calculate_rms_energy(samples)
    silence_ratio = _calculate_silence_ratio(samples)
    clipping_ratio = _calculate_clipping_ratio(samples)

    quality_score = _calculate_quality_score(
        rms_energy=rms_energy,
        silence_ratio=silence_ratio,
        clipping_ratio=clipping_ratio,
    )

    if (
        rms_energy < MIN_SPEECH_RMS
        or silence_ratio > 0.95
    ):
        quality_level = QUALITY_UNUSABLE
        usable = False
        reason = "INSUFFICIENT_USABLE_AUDIO"
    elif quality_score >= 0.70:
        quality_level = QUALITY_GOOD
        usable = True
        reason = None
    else:
        quality_level = QUALITY_POOR_BUT_USABLE
        usable = True
        reason = "AUDIO_QUALITY_DEGRADED"

    return AudioQualityResult(
        usable=usable,
        quality_level=quality_level,
        audio_quality=quality_score,
        duration_seconds=duration_seconds,
        silence_ratio=silence_ratio,
        clipping_ratio=clipping_ratio,
        rms_energy=rms_energy,
        reason=reason,
    )