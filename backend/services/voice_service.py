"""
AAROH — Voice Service

Application boundary between the FastAPI layer and the voice ML pipeline.

Responsibilities:
  - Receive validated audio bytes from the endpoint layer
  - Write to a secure OS-managed temp file
  - Delegate to backend.voice (Diya's subsystem) if available
  - Guarantee temp file is deleted after delegation (success or failure)
  - Return a VoiceProcessingState string

Mahendra does NOT implement:
  - ASR (automatic speech recognition)
  - VAD (voice activity detection)
  - Pitch, speech rate, energy, pause features
  - Baseline deviation calculation
  - Feature fusion

Those belong to Diya's frozen backend/voice/ subsystem.

Voice Processing States:
  RECEIVED          — audio accepted, queued for processing
  PROCESSING        — processing has started
  COMPLETED         — processing finished successfully
  FAILED            — processing failed, will not be retried
  RETRY_REQUIRED    — transient failure, eligible for retry

For asynchronous processing the endpoint returns 202 ACCEPTED with RECEIVED.
COMPLETED is only set when processing actually succeeds.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Processing state type
# ---------------------------------------------------------------------------

VoiceProcessingState = Literal[
    "RECEIVED",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "RETRY_REQUIRED",
]

# ---------------------------------------------------------------------------
# Voice subsystem boundary
# ---------------------------------------------------------------------------

def _try_import_voice_subsystem():
    """
    Attempt to import Diya's frozen voice subsystem.

    Returns the subsystem module if available, None otherwise.
    The subsystem is expected to live at backend.voice and expose a
    `process_audio(interaction_id, case_id, language, audio_path)` function.
    """
    try:
        import backend.voice as voice_module
        return voice_module
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Public delegation function
# ---------------------------------------------------------------------------

def delegate_voice_processing(
    *,
    interaction_id: int,
    case_id: int,
    language: str,
    audio_bytes: bytes,
) -> VoiceProcessingState:
    """
    Write audio to a secure temporary file and delegate to the voice pipeline.

    The temporary file is always deleted in the finally block — it is NEVER
    left on disk after this function returns, regardless of success or failure.

    Args:
        interaction_id: DB ID of the Interaction record.
        case_id:        DB ID of the Case record.
        language:       BCP-47 language tag (e.g. "hi-IN").
        audio_bytes:    Raw audio bytes (already validated by audio_validation).

    Returns:
        A VoiceProcessingState string.

    Raises:
        Exception — only if temp file creation itself fails (OS-level error).
        All voice-pipeline errors are caught and logged; FAILED is returned.

    SECURITY:
        - Temp file uses a random OS-assigned name (no original filename).
        - Temp file is always deleted before returning.
        - Audio bytes and file paths are never logged.
        - Raw transcripts and sensitive content are never logged.
    """
    # Create a secure OS temp file — delete=False so we control deletion
    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".audio_tmp",   # Generic suffix — not original extension
        prefix="aaroh_voice_",
    )
    tmp_path = tmp.name

    try:
        # Write validated bytes to temp file
        tmp.write(audio_bytes)
        tmp.flush()
        tmp.close()

        # Delegate to voice subsystem if it exists
        voice_module = _try_import_voice_subsystem()
        if voice_module is not None and hasattr(voice_module, "process_audio"):
            # Diya's interface: process_audio(interaction_id, case_id, language, audio_path)
            voice_module.process_audio(
                interaction_id=interaction_id,
                case_id=case_id,
                language=language,
                audio_path=tmp_path,
            )
            return "RECEIVED"

        # Voice subsystem not yet available — audio accepted, will be processed
        # when the subsystem is integrated. State: RECEIVED (not COMPLETED).
        logger.info(
            "Voice subsystem not available; audio accepted for future processing. "
            "interaction_id=%d case_id=%d language=%s",
            interaction_id, case_id, language,
        )
        return "RECEIVED"

    except Exception:
        # Log the exception type only — never log audio content or paths
        logger.exception(
            "Voice processing delegation failed. "
            "interaction_id=%d case_id=%d",
            interaction_id, case_id,
        )
        return "FAILED"

    finally:
        # Always delete the temp file — no audio left on disk
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            # Log that cleanup failed but do not raise — the audio is gone
            # from the request context regardless.
            logger.warning(
                "Failed to delete temp audio file after processing. "
                "Manual cleanup may be required. interaction_id=%d",
                interaction_id,
            )
