"""
AAROH — Audio Validation

Validates audio files before passing them to the voice pipeline.

Rules enforced:
  - File must be present (non-empty)
  - MIME type must be in the allowed list (checked from content_type field)
  - File extension must be in the allowed list (checked from sanitised filename)
  - File size must not exceed MAX_AUDIO_SIZE_BYTES (default 25 MB)
  - For WAV files: duration must be between MIN_DURATION_SECONDS and
    MAX_DURATION_SECONDS (1–120 s), verified via stdlib `wave` module
  - For other formats: size limit acts as the proxy guard; duration checking
    requires an audio library (mutagen/pydub) not currently installed

SECURITY:
  - Original filenames are never trusted for type detection.
  - Magic bytes are checked for the most common formats.
  - File paths are never returned to callers.
  - No audio content is logged.

Design: validation raises AudioValidationError (a subclass of HTTPException)
so the global error handler produces a standard AAROH error envelope.
"""

from __future__ import annotations

import io
import os
import wave
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_AUDIO_SIZE_BYTES: int = 25 * 1024 * 1024   # 25 MB
MIN_DURATION_SECONDS: float = 1.0
MAX_DURATION_SECONDS: float = 120.0

# Allowed MIME types (content_type supplied by the client — informational only,
# we additionally verify magic bytes below)
ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "application/octet-stream",  # Allow generic binary — extension + magic checked separately
})

# Allowed extensions (derived from sanitised filename, lower-cased)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".wav", ".mp3", ".ogg", ".webm"})

# Magic-byte signatures for supported formats
# (first N bytes of the file)
_WAV_RIFF  = b"RIFF"
_WAV_WAVE  = b"WAVE"
_MP3_ID3   = b"ID3"
_MP3_SYNC1 = b"\xff\xfb"   # MPEG1 Layer3 frame sync
_MP3_SYNC2 = b"\xff\xf3"   # MPEG2 frame sync
_OGG_MAGIC = b"OggS"
_WEBM_EBML = b"\x1a\x45\xdf\xa3"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class AudioValidationError(HTTPException):
    """
    Raised when an uploaded audio file fails validation.
    Subclasses HTTPException so the global handler formats it correctly.
    """
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        # Store code for structured error envelope in main.py global handler
        super().__init__(status_code=status_code, detail=message)
        self.code = code


# ---------------------------------------------------------------------------
# Magic-byte detection
# ---------------------------------------------------------------------------

def _detect_format_from_bytes(header: bytes) -> Optional[str]:
    """
    Returns a detected format string or None if unrecognised.
    Uses the first 12 bytes of the file.
    """
    if header[:4] == _WAV_RIFF and header[8:12] == _WAV_WAVE:
        return "wav"
    if header[:3] == _MP3_ID3 or header[:2] in (_MP3_SYNC1, _MP3_SYNC2):
        return "mp3"
    if header[:4] == _OGG_MAGIC:
        return "ogg"
    if header[:4] == _WEBM_EBML:
        return "webm"
    return None


# ---------------------------------------------------------------------------
# WAV duration check (stdlib only)
# ---------------------------------------------------------------------------

def _wav_duration_seconds(data: bytes) -> Optional[float]:
    """
    Reads WAV duration from raw bytes using the stdlib `wave` module.
    Returns None if the data cannot be parsed as a valid WAV file.
    """
    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate == 0:
                return None
            return frames / float(rate)
    except (wave.Error, EOFError, Exception):
        return None


# ---------------------------------------------------------------------------
# Public validation function
# ---------------------------------------------------------------------------

def validate_audio(file: UploadFile) -> bytes:
    """
    Validates the uploaded audio file and returns the raw bytes on success.

    The returned bytes are used by the caller to write to a secure temp file.
    The UploadFile stream is fully consumed here so it must not be read again.

    Raises:
        AudioValidationError — on any validation failure.

    Does NOT:
        - Return filesystem paths.
        - Log audio content.
        - Trust the original filename for type detection.
    """
    # ------------------------------------------------------------------
    # 1. File presence
    # ------------------------------------------------------------------
    if not file or not file.filename:
        raise AudioValidationError(
            code="AUDIO_MISSING",
            message="No audio file was provided.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # ------------------------------------------------------------------
    # 2. Extension check on sanitised filename
    #    We sanitise by taking only the suffix portion via pathlib.
    # ------------------------------------------------------------------
    safe_stem = Path(file.filename.replace("/", "_").replace("\\", "_"))
    ext = safe_stem.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AudioValidationError(
            code="AUDIO_INVALID_EXTENSION",
            message=(
                f"File extension '{ext or '(none)'}' is not supported. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # ------------------------------------------------------------------
    # 3. MIME type check (client-supplied, informational cross-check)
    # ------------------------------------------------------------------
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise AudioValidationError(
            code="AUDIO_INVALID_MIME",
            message=(
                f"MIME type '{content_type}' is not supported. "
                f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            ),
        )

    # ------------------------------------------------------------------
    # 4. Read file bytes — enforces size limit during read
    # ------------------------------------------------------------------
    # Read one byte more than the limit to detect oversized files.
    limit = MAX_AUDIO_SIZE_BYTES + 1
    data = file.file.read(limit)

    if len(data) > MAX_AUDIO_SIZE_BYTES:
        raise AudioValidationError(
            code="AUDIO_TOO_LARGE",
            message=(
                f"Audio file exceeds the maximum allowed size of "
                f"{MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB."
            ),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    if len(data) == 0:
        raise AudioValidationError(
            code="AUDIO_EMPTY",
            message="Audio file is empty.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # ------------------------------------------------------------------
    # 5. Magic byte verification (independent of filename/MIME)
    # ------------------------------------------------------------------
    header = data[:12]
    detected = _detect_format_from_bytes(header)
    if detected is None:
        raise AudioValidationError(
            code="AUDIO_UNRECOGNISED_FORMAT",
            message=(
                "The file does not appear to be a supported audio format. "
                "Supported formats: WAV, MP3, OGG, WebM."
            ),
        )

    # ------------------------------------------------------------------
    # 6. Duration check (WAV only — uses stdlib wave module)
    # ------------------------------------------------------------------
    if detected == "wav":
        duration = _wav_duration_seconds(data)
        if duration is None:
            raise AudioValidationError(
                code="AUDIO_DECODE_FAILURE",
                message="The WAV file could not be decoded. It may be malformed.",
            )
        if duration < MIN_DURATION_SECONDS:
            raise AudioValidationError(
                code="AUDIO_TOO_SHORT",
                message=(
                    f"Audio duration ({duration:.2f}s) is below the minimum "
                    f"of {MIN_DURATION_SECONDS:.0f} second(s)."
                ),
            )
        if duration > MAX_DURATION_SECONDS:
            raise AudioValidationError(
                code="AUDIO_TOO_LONG",
                message=(
                    f"Audio duration ({duration:.2f}s) exceeds the maximum "
                    f"of {MAX_DURATION_SECONDS:.0f} seconds."
                ),
            )

    return data
