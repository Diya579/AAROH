from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from backend.voice.vad import VADResult


FRAME_DURATION_SECONDS = 0.030
FRAME_STEP_SECONDS = 0.010

MIN_RMS_ENERGY = 0.005


@dataclass
class EnergyVariationResult:
    energy_variation: Optional[float]
    mean_rms_energy: Optional[float]
    std_rms_energy: Optional[float]
    valid_frame_count: int
    reason: Optional[str] = None


def _load_wav(audio_path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(audio_path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()

        if channels != 1:
            raise ValueError("Audio must be mono.")

        if sample_width != 2:
            raise ValueError("Audio must be 16-bit PCM.")

        if sample_rate != 16000:
            raise ValueError("Audio must have a 16 kHz sample rate.")

        if frame_count <= 0:
            raise ValueError("Audio contains no samples.")

        frames = wav_file.readframes(frame_count)

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    audio /= 32768.0

    return audio, sample_rate


def _calculate_rms(frame: np.ndarray) -> float:
    if frame.size == 0:
        return 0.0

    return float(np.sqrt(np.mean(frame * frame)))


def calculate_energy_variation(
    audio_path: str | Path,
    vad_result: VADResult,
) -> EnergyVariationResult:
    """
    Calculate variation in RMS energy across voiced frames.

    energy_variation = standard deviation of RMS / mean RMS

    Silence and frames below the minimum RMS threshold are excluded.
    """

    if not vad_result.usable:
        return EnergyVariationResult(
            energy_variation=None,
            mean_rms_energy=None,
            std_rms_energy=None,
            valid_frame_count=0,
            reason="VAD_UNUSABLE",
        )

    path = Path(audio_path)

    if not path.exists() or not path.is_file():
        return EnergyVariationResult(
            energy_variation=None,
            mean_rms_energy=None,
            std_rms_energy=None,
            valid_frame_count=0,
            reason="AUDIO_FILE_NOT_FOUND",
        )

    try:
        audio, sample_rate = _load_wav(path)
    except (wave.Error, ValueError, OSError):
        return EnergyVariationResult(
            energy_variation=None,
            mean_rms_energy=None,
            std_rms_energy=None,
            valid_frame_count=0,
            reason="INVALID_AUDIO",
        )

    frame_length = int(sample_rate * FRAME_DURATION_SECONDS)
    frame_step = int(sample_rate * FRAME_STEP_SECONDS)

    rms_values: list[float] = []

    for segment in vad_result.speech_segments:
        start_sample = max(
            0,
            int(segment.start_seconds * sample_rate),
        )

        end_sample = min(
            len(audio),
            int(segment.end_seconds * sample_rate),
        )

        if end_sample - start_sample < frame_length:
            continue

        position = start_sample

        while position + frame_length <= end_sample:
            frame = audio[position : position + frame_length]

            rms = _calculate_rms(frame)

            if rms >= MIN_RMS_ENERGY:
                rms_values.append(rms)

            position += frame_step

    if not rms_values:
        return EnergyVariationResult(
            energy_variation=None,
            mean_rms_energy=None,
            std_rms_energy=None,
            valid_frame_count=0,
            reason="NO_VALID_ENERGY",
        )

    rms_array = np.asarray(rms_values, dtype=np.float64)

    mean_rms = float(np.mean(rms_array))
    std_rms = float(np.std(rms_array))

    if mean_rms <= 0:
        return EnergyVariationResult(
            energy_variation=None,
            mean_rms_energy=None,
            std_rms_energy=None,
            valid_frame_count=len(rms_values),
            reason="INVALID_MEAN_ENERGY",
        )

    energy_variation = std_rms / mean_rms

    return EnergyVariationResult(
        energy_variation=max(0.0, float(energy_variation)),
        mean_rms_energy=mean_rms,
        std_rms_energy=std_rms,
        valid_frame_count=len(rms_values),
        reason=None,
    )