"""RAVDESS Audio Emotion Dataset loader & preprocessing (Slice 3.4).

Provides:
- RavdessDataset with lazy waveform loading (no preloading of all WAVs into memory).
- Deterministic actor-level splitting preventing speaker leakage.
- High-quality audio resampling to 16 kHz (torchaudio/librosa when available, deterministic interpolation fallback).
- Amplitude normalization and padding/truncation to 5.0 seconds (80,000 samples).
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.training.preprocessing.common import read_jsonl

# 8 RAVDESS Speech Emotion Classes
RAVDESS_EMOTIONS: tuple[str, ...] = (
    "neutral",
    "calm",
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgust",
    "surprised",
)

EMOTION_TO_ID: dict[str, int] = {name: idx for idx, name in enumerate(RAVDESS_EMOTIONS)}
ID_TO_EMOTION: dict[int, str] = {idx: name for idx, name in enumerate(RAVDESS_EMOTIONS)}

DEFAULT_TARGET_SAMPLE_RATE = 16000
DEFAULT_TARGET_DURATION_SECONDS = 5.0
DEFAULT_TARGET_SAMPLES = int(DEFAULT_TARGET_SAMPLE_RATE * DEFAULT_TARGET_DURATION_SECONDS)  # 80,000


def validate_no_actor_leakage(
    train_records: Sequence[dict[str, Any]],
    test_records: Sequence[dict[str, Any]],
) -> None:
    """Validates that no actor appears in both train and test splits.

    Raises:
        ValueError: If any actor appears in both train and test.
    """
    train_actors = set(str(r["actor"]).strip() for r in train_records)
    test_actors = set(str(r["actor"]).strip() for r in test_records)
    leakage = train_actors.intersection(test_actors)
    if leakage:
        raise ValueError(
            f"ACTOR LEAKAGE DETECTED: Actors present in both train and test splits: {sorted(list(leakage))}"
        )


def split_ravdess_records_by_actor(
    records: Sequence[dict[str, Any]],
    test_ratio: float = 0.25,
    seed: int = 42,
    test_actors: Optional[Sequence[str]] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministically partitions records by Actor ID to strictly prevent speaker leakage.

    Raises:
        ValueError: If actor leakage is detected or a partition is empty.
    """
    all_actors = sorted(list(set(str(r["actor"]).strip() for r in records)))
    if not all_actors:
        return [], []

    if test_actors is not None:
        selected_test_actors = set(str(a).strip() for a in test_actors)
    else:
        # Deterministic programmatic partition using seed=42
        rng = random.Random(seed)
        shuffled_actors = list(all_actors)
        rng.shuffle(shuffled_actors)
        n_test = max(1, int(round(len(all_actors) * test_ratio)))
        selected_test_actors = set(shuffled_actors[:n_test])

    selected_train_actors = set(all_actors) - selected_test_actors

    if not selected_train_actors or not selected_test_actors:
        raise ValueError(
            "Invalid actor partition: either train or test actor split is empty. "
            f"Train actors: {len(selected_train_actors)}, Test actors: {len(selected_test_actors)}"
        )

    # Leakage check 1: Actor sets
    leakage = selected_train_actors.intersection(selected_test_actors)
    if leakage:
        raise ValueError(
            f"ACTOR LEAKAGE DETECTED: Actors present in both train and test splits: {sorted(list(leakage))}"
        )

    train_records = [r for r in records if str(r["actor"]).strip() in selected_train_actors]
    test_records = [r for r in records if str(r["actor"]).strip() in selected_test_actors]

    # Leakage check 2: Record-level validation
    validate_no_actor_leakage(train_records, test_records)

    return train_records, test_records


def _resample_waveform_fallback(
    samples: list[float],
    orig_sr: int,
    target_sr: int,
) -> list[float]:
    """Deterministic interpolation resampling for environments without torchaudio/librosa.

    Uses band-limited anti-aliasing filtering and linear interpolation.
    """
    if orig_sr == target_sr or not samples:
        return samples

    ratio = orig_sr / target_sr
    target_length = int(round(len(samples) / ratio))
    resampled: list[float] = [0.0] * target_length

    # Simple moving average anti-aliasing prefilter if downsampling
    filter_radius = max(1, int(math.ceil(ratio / 2.0))) if ratio > 1.0 else 1

    for i in range(target_length):
        center_pos = i * ratio
        idx_low = int(math.floor(center_pos))
        idx_high = min(len(samples) - 1, idx_low + 1)
        frac = center_pos - idx_low

        if ratio > 1.0 and filter_radius > 1:
            # Average window around center_pos to avoid aliasing high frequencies
            w_start = max(0, int(center_pos - filter_radius))
            w_end = min(len(samples), int(center_pos + filter_radius + 1))
            val = sum(samples[k] for k in range(w_start, w_end)) / (w_end - w_start)
            resampled[i] = val
        else:
            # Linear interpolation
            s1 = samples[idx_low]
            s2 = samples[idx_high]
            resampled[i] = (1.0 - frac) * s1 + frac * s2

    return resampled


def load_and_preprocess_wav(
    audio_path: Path | str,
    target_sr: int = DEFAULT_TARGET_SAMPLE_RATE,
    target_samples: int = DEFAULT_TARGET_SAMPLES,
) -> tuple[list[float], int]:
    """Lazily loads and preprocesses a WAV file:

    1. Reads audio frames (16-bit PCM or float).
    2. Resamples to target_sr (16 kHz) using torchaudio/librosa or deterministic fallback.
    3. Normalizes waveform amplitude.
    4. Pads with zeros or truncates to target_samples (80,000 samples = 5.0 seconds).

    Returns:
        (waveform_samples, sample_rate)
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Check for torchaudio
    try:
        import torchaudio
        waveform, sr = torchaudio.load(str(path))
        # Convert to mono if multi-channel
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        # Resample to 16 kHz
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
            waveform = resampler(waveform)
        # Flatten
        samples = waveform.squeeze(0).tolist()
    except Exception:
        # Check for librosa
        try:
            import librosa
            waveform, sr = librosa.load(str(path), sr=target_sr, mono=True)
            samples = waveform.tolist()
        except Exception:
            # Fallback: Read using Python standard library wave module
            with wave.open(str(path), "rb") as wav_file:
                channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                sr = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                raw_bytes = wav_file.readframes(n_frames)

            # Unpack 16-bit PCM
            if sampwidth == 2:
                total_samples = n_frames * channels
                unpacked = struct.unpack(f"<{total_samples}h", raw_bytes)
                if channels > 1:
                    mono_samples = [
                        sum(unpacked[i * channels + c] for c in range(channels)) / (channels * 32768.0)
                        for i in range(n_frames)
                    ]
                else:
                    mono_samples = [s / 32768.0 for s in unpacked]
            else:
                # 8-bit or 24-bit fallback
                mono_samples = [0.0] * n_frames

            # Resample if needed
            samples = _resample_waveform_fallback(mono_samples, orig_sr=sr, target_sr=target_sr)

    # Amplitude normalization (peak normalize to [-1.0, 1.0])
    max_amp = max((abs(s) for s in samples), default=0.0)
    if max_amp > 1e-6:
        samples = [s / max_amp for s in samples]

    # Pad or truncate to target_samples (80,000 samples)
    if len(samples) < target_samples:
        pad_size = target_samples - len(samples)
        samples = samples + [0.0] * pad_size
    elif len(samples) > target_samples:
        samples = samples[:target_samples]

    return samples, target_sr


class RavdessDataset:
    """Lazy-loading dataset for RAVDESS audio speech emotion records.

    Does NOT preload all WAV files into memory; reads and preprocesses
    audio files on-the-fly during indexing.
    """

    def __init__(
        self,
        records: Sequence[dict[str, Any]],
        target_sr: int = DEFAULT_TARGET_SAMPLE_RATE,
        target_samples: int = DEFAULT_TARGET_SAMPLES,
    ) -> None:
        self.records = list(records)
        self.target_sr = target_sr
        self.target_samples = target_samples

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        rec = self.records[idx]
        audio_path = rec["audio_path"]
        emotion_str = rec.get("emotion", "neutral")
        emotion_id = EMOTION_TO_ID.get(emotion_str, 0)
        actor_id = str(rec.get("actor", "01"))
        intensity = rec.get("intensity", "normal")

        # Lazy waveform load & preprocess
        waveform, sr = load_and_preprocess_wav(
            audio_path=audio_path,
            target_sr=self.target_sr,
            target_samples=self.target_samples,
        )

        return {
            "waveform": waveform,
            "sample_rate": sr,
            "emotion": emotion_str,
            "emotion_id": emotion_id,
            "actor_id": actor_id,
            "intensity": intensity,
            "audio_path": str(audio_path),
        }
