from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


TARGET_SAMPLE_RATE = 16_000
TARGET_CHANNELS = 1
TARGET_SAMPLE_FORMAT = "s16"

MIN_DURATION_SECONDS = 1.0
MAX_DURATION_SECONDS = 120.0


@dataclass
class AudioPreprocessingResult:
    success: bool
    reason: str | None
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    output_path: str | None


def _get_audio_duration(input_path: Path) -> float | None:
    """
    Get audio duration using ffprobe.

    Returns:
        Duration in seconds, or None if the media cannot be inspected.
    """

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    try:
        duration = float(result.stdout.strip())
    except (TypeError, ValueError):
        return None

    if duration < 0:
        return None

    return duration


def preprocess_audio(
    audio_bytes: bytes,
    input_extension: str = ".webm",
) -> AudioPreprocessingResult:
    """
    Decode and normalize captured audio for the AAROH voice pipeline.

    Output:
        16 kHz, mono, signed 16-bit PCM WAV.

    The original audio bytes are never modified.
    """

    if not audio_bytes:
        return AudioPreprocessingResult(
            success=False,
            reason="EMPTY_AUDIO",
            duration_seconds=None,
            sample_rate=None,
            channels=None,
            output_path=None,
        )

    suffix = input_extension.lower()

    if not suffix.startswith("."):
        suffix = f".{suffix}"

    temporary_input: Path | None = None
    temporary_output: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as input_file:
            input_file.write(audio_bytes)
            temporary_input = Path(input_file.name)

        duration = _get_audio_duration(temporary_input)

        if duration is None:
            return AudioPreprocessingResult(
                success=False,
                reason="INVALID_OR_UNREADABLE_AUDIO",
                duration_seconds=None,
                sample_rate=None,
                channels=None,
                output_path=None,
            )

        if duration < MIN_DURATION_SECONDS:
            return AudioPreprocessingResult(
                success=False,
                reason="AUDIO_TOO_SHORT",
                duration_seconds=duration,
                sample_rate=None,
                channels=None,
                output_path=None,
            )

        if duration > MAX_DURATION_SECONDS:
            return AudioPreprocessingResult(
                success=False,
                reason="AUDIO_TOO_LONG",
                duration_seconds=duration,
                sample_rate=None,
                channels=None,
                output_path=None,
            )

        output_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        )
        output_file.close()

        temporary_output = Path(output_file.name)

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(temporary_input),
            "-ac",
            str(TARGET_CHANNELS),
            "-ar",
            str(TARGET_SAMPLE_RATE),
            "-sample_fmt",
            TARGET_SAMPLE_FORMAT,
            "-c:a",
            "pcm_s16le",
            str(temporary_output),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return AudioPreprocessingResult(
                success=False,
                reason="AUDIO_CONVERSION_FAILED",
                duration_seconds=duration,
                sample_rate=None,
                channels=None,
                output_path=None,
            )

        if not temporary_output.exists() or temporary_output.stat().st_size == 0:
            return AudioPreprocessingResult(
                success=False,
                reason="EMPTY_PROCESSED_AUDIO",
                duration_seconds=duration,
                sample_rate=None,
                channels=None,
                output_path=None,
            )

        return AudioPreprocessingResult(
            success=True,
            reason=None,
            duration_seconds=duration,
            sample_rate=TARGET_SAMPLE_RATE,
            channels=TARGET_CHANNELS,
            output_path=str(temporary_output),
        )

    finally:
        if temporary_input is not None:
            try:
                temporary_input.unlink(missing_ok=True)
            except OSError:
                pass