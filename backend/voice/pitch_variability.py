from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from backend.voice.vad import VADResult


MIN_F0_HZ = 70.0
MAX_F0_HZ = 350.0

FRAME_DURATION_SECONDS = 0.030
FRAME_STEP_SECONDS = 0.010


@dataclass
class PitchVariabilityResult:
    pitch_variability: Optional[float]
    mean_f0_hz: Optional[float]
    std_f0_hz: Optional[float]
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


def _estimate_f0(
    frame: np.ndarray,
    sample_rate: int,
) -> Optional[float]:
    """
    Estimate fundamental frequency using normalized autocorrelation.

    Returns None when the frame does not contain a reliable periodic signal.
    """

    frame = frame - np.mean(frame)

    energy = np.sqrt(np.mean(frame * frame))

    if energy < 0.005:
        return None

    min_lag = int(sample_rate / MAX_F0_HZ)
    max_lag = int(sample_rate / MIN_F0_HZ)

    if max_lag >= len(frame):
        return None

    autocorrelation = np.correlate(frame, frame, mode="full")
    autocorrelation = autocorrelation[len(frame) - 1 :]

    zero_lag = autocorrelation[0]

    if zero_lag <= 0:
        return None

    autocorrelation /= zero_lag

    search_region = autocorrelation[min_lag : max_lag + 1]

    if len(search_region) == 0:
        return None

    peak_index = int(np.argmax(search_region))
    peak_value = float(search_region[peak_index])

    # Reject weak periodicity.
    if peak_value < 0.30:
        return None

    lag = min_lag + peak_index

    if lag <= 0:
        return None

    f0 = sample_rate / lag

    if f0 < MIN_F0_HZ or f0 > MAX_F0_HZ:
        return None

    return float(f0)


def calculate_pitch_variability(
    audio_path: str | Path,
    vad_result: VADResult,
) -> PitchVariabilityResult:
    """
    Estimate pitch variability from valid voiced frames.

    Pitch variability is calculated as:

        standard deviation of F0 / mean F0

    Only frames falling inside VAD speech segments are considered.
    """

    if not vad_result.usable:
        return PitchVariabilityResult(
            pitch_variability=None,
            mean_f0_hz=None,
            std_f0_hz=None,
            valid_frame_count=0,
            reason="VAD_UNUSABLE",
        )

    path = Path(audio_path)

    if not path.exists() or not path.is_file():
        return PitchVariabilityResult(
            pitch_variability=None,
            mean_f0_hz=None,
            std_f0_hz=None,
            valid_frame_count=0,
            reason="AUDIO_FILE_NOT_FOUND",
        )

    try:
        audio, sample_rate = _load_wav(path)
    except (wave.Error, ValueError, OSError):
        return PitchVariabilityResult(
            pitch_variability=None,
            mean_f0_hz=None,
            std_f0_hz=None,
            valid_frame_count=0,
            reason="INVALID_AUDIO",
        )

    frame_length = int(sample_rate * FRAME_DURATION_SECONDS)
    frame_step = int(sample_rate * FRAME_STEP_SECONDS)

    f0_values: list[float] = []

    for segment in vad_result.speech_segments:
        start_sample = max(0, int(segment.start_seconds * sample_rate))
        end_sample = min(
            len(audio),
            int(segment.end_seconds * sample_rate),
        )

        if end_sample - start_sample < frame_length:
            continue

        position = start_sample

        while position + frame_length <= end_sample:
            frame = audio[position : position + frame_length]

            f0 = _estimate_f0(frame, sample_rate)

            if f0 is not None:
                f0_values.append(f0)

            position += frame_step

    if not f0_values:
        return PitchVariabilityResult(
            pitch_variability=None,
            mean_f0_hz=None,
            std_f0_hz=None,
            valid_frame_count=0,
            reason="NO_VALID_PITCH",
        )

    f0_array = np.asarray(f0_values, dtype=np.float64)

    mean_f0 = float(np.mean(f0_array))
    std_f0 = float(np.std(f0_array))

    if mean_f0 <= 0:
        return PitchVariabilityResult(
            pitch_variability=None,
            mean_f0_hz=None,
            std_f0_hz=None,
            valid_frame_count=len(f0_values),
            reason="INVALID_MEAN_F0",
        )

    pitch_variability = std_f0 / mean_f0

    return PitchVariabilityResult(
        pitch_variability=max(0.0, float(pitch_variability)),
        mean_f0_hz=mean_f0,
        std_f0_hz=std_f0,
        valid_frame_count=len(f0_values),
        reason=None,
    )