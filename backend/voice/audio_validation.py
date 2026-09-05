from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Maximum accepted audio size: 10 MB
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024

# Minimum and maximum recording duration for AAROH voice check-ins.
MIN_DURATION_SECONDS = 1.0
MAX_DURATION_SECONDS = 120.0

# Browser/device formats we may receive from microphone capture.
SUPPORTED_MIME_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/ogg",
    "audio/ogg;codecs=opus",
    "audio/mp4",
    "audio/mpeg",
}


@dataclass
class AudioValidationResult:
    valid: bool
    reason: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


def validate_audio_input(
    audio_bytes: bytes,
    mime_type: str,
    filename: Optional[str] = None,
) -> AudioValidationResult:
    """
    Validate microphone-captured audio before preprocessing.

    This function performs basic input validation only.
    It does NOT:
    - perform ASR
    - extract voice features
    - calculate distress
    - calculate risk
    - modify the audio
    """

    if not audio_bytes:
        return AudioValidationResult(
            valid=False,
            reason="Audio recording is empty.",
            mime_type=mime_type,
            size_bytes=0,
        )

    if not mime_type:
        return AudioValidationResult(
            valid=False,
            reason="Audio MIME type is missing.",
            size_bytes=len(audio_bytes),
        )

    normalized_mime = mime_type.lower().strip()

    if normalized_mime not in SUPPORTED_MIME_TYPES:
        return AudioValidationResult(
            valid=False,
            reason=f"Unsupported audio MIME type: {mime_type}",
            mime_type=mime_type,
            size_bytes=len(audio_bytes),
        )

    size_bytes = len(audio_bytes)

    if size_bytes > MAX_AUDIO_SIZE_BYTES:
        return AudioValidationResult(
            valid=False,
            reason="Audio recording exceeds the maximum allowed size.",
            mime_type=mime_type,
            size_bytes=size_bytes,
        )

    if filename:
        suffix = Path(filename).suffix.lower()

        allowed_suffixes = {
            ".wav",
            ".webm",
            ".ogg",
            ".mp4",
            ".m4a",
            ".mp3",
        }

        if suffix and suffix not in allowed_suffixes:
            return AudioValidationResult(
                valid=False,
                reason=f"Unsupported audio file extension: {suffix}",
                mime_type=mime_type,
                size_bytes=size_bytes,
            )

    return AudioValidationResult(
        valid=True,
        mime_type=normalized_mime,
        size_bytes=size_bytes,
    )