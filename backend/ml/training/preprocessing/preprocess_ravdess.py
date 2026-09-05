"""RAVDESS dataset ingestion and preprocessing (Slice 3.2).

Automatically discovers Actor directories, parses filenames according to the official
RAVDESS naming specification (7-part hyphen-separated code), and creates normalized JSONL records.
Does NOT compute MFCCs or extract acoustic embeddings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.training.preprocessing.common import (
    compute_dataset_stats,
    deterministic_sort,
    write_jsonl,
)

# Official RAVDESS filename specification mappings
RAVDESS_MODALITIES: dict[str, str] = {
    "01": "full-AV",
    "02": "video-only",
    "03": "audio-only",
}

RAVDESS_VOCAL_CHANNELS: dict[str, str] = {
    "01": "speech",
    "02": "song",
}

RAVDESS_EMOTIONS: dict[str, str] = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}

RAVDESS_INTENSITIES: dict[str, str] = {
    "01": "normal",
    "02": "strong",
}

RAVDESS_STATEMENTS: dict[str, str] = {
    "01": "Kids are talking by the door",
    "02": "Dogs are sitting by the door",
}

RAVDESS_REPETITIONS: dict[str, str] = {
    "01": "1st repetition",
    "02": "2nd repetition",
}


def parse_ravdess_filename(file_name: str) -> dict[str, str]:
    """Parses a standard RAVDESS filename (e.g., '03-01-01-01-01-01-01.wav').

    Fails with a descriptive ValueError if the format is invalid.
    """
    stem = Path(file_name).stem
    parts = stem.split("-")
    if len(parts) != 7:
        raise ValueError(
            f"Invalid RAVDESS filename format '{file_name}': expected 7 hyphen-separated "
            f"components (MM-VC-EE-II-SS-RR-AA), got {len(parts)} parts"
        )

    modality_code, channel_code, emotion_code, intensity_code, statement_code, repetition_code, actor_code = parts

    emotion = RAVDESS_EMOTIONS.get(emotion_code)
    if not emotion:
        raise ValueError(f"Unknown RAVDESS emotion code '{emotion_code}' in '{file_name}'")

    intensity = RAVDESS_INTENSITIES.get(intensity_code, "normal")
    statement = RAVDESS_STATEMENTS.get(statement_code, f"Statement {statement_code}")
    repetition = RAVDESS_REPETITIONS.get(repetition_code, f"Repetition {repetition_code}")
    vocal_channel = RAVDESS_VOCAL_CHANNELS.get(channel_code, "speech")

    return {
        "modality": vocal_channel,
        "emotion": emotion,
        "intensity": intensity,
        "statement": statement,
        "repetition": repetition,
        "actor": actor_code,
    }


def discover_ravdess_files(data_dir: Path | str) -> list[Path]:
    """Automatically discovers all RAVDESS .wav files across Actor directories."""
    path = Path(data_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"RAVDESS directory does not exist: {path}")

    # Search for all .wav files in subdirectories (e.g. Actor_01, Audio_Speech_Actors_01-24, etc.)
    wav_files = sorted(path.rglob("*.wav"))
    if not wav_files:
        raise FileNotFoundError(f"No .wav audio files found in RAVDESS directory: {path}")

    return wav_files


def preprocess_ravdess_directory(data_dir: Path | str) -> list[dict[str, Any]]:
    """Walks RAVDESS directory and parses audio filenames into structured records."""
    wav_files = discover_ravdess_files(data_dir)
    records: list[dict[str, Any]] = []

    for wav_path in wav_files:
        parsed = parse_ravdess_filename(wav_path.name)
        # Use relative path from repository root if possible
        try:
            rel_path = str(wav_path.relative_to(Path.cwd()))
        except ValueError:
            rel_path = str(wav_path)

        record = {
            "dataset": "ravdess",
            "audio_path": rel_path,
            "actor": parsed["actor"],
            "emotion": parsed["emotion"],
            "intensity": parsed["intensity"],
            "statement": parsed["statement"],
            "repetition": parsed["repetition"],
            "modality": parsed["modality"],
        }
        records.append(record)

    # Sort deterministically by actor, then audio_path
    return deterministic_sort(records, key_fields=["actor", "audio_path"])


def process_ravdess(
    data_dir: Path | str,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Processes all detected RAVDESS audio files and writes ravdess.jsonl."""
    records = preprocess_ravdess_directory(data_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "ravdess.jsonl"
    count = write_jsonl(records, out_file)

    stats = compute_dataset_stats(
        dataset_name="ravdess",
        records=records,
        label_field="emotion",
        language="en",
    )
    # Collect actor counts
    actors = set(r["actor"] for r in records)
    stats["total_samples"] = count
    stats["actor_count"] = len(actors)
    stats["actors"] = sorted(list(actors))

    return stats
