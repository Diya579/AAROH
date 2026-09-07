from __future__ import annotations

import threading
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from faster_whisper import WhisperModel
from transformers import AutoModel


# ---------------------------------------------------------
# Model configuration
# ---------------------------------------------------------

INDIC_MODEL_NAME = "ai4bharat/indic-conformer-600m-multilingual"
ENGLISH_MODEL_NAME = "base.en"


# ---------------------------------------------------------
# ASR status constants
# ---------------------------------------------------------

ASR_SUCCESS = "SUCCESS"
ASR_FAILED = "FAILED"
ASR_NO_SPEECH = "NO_SPEECH"
ASR_LOW_CONFIDENCE = "LOW_CONFIDENCE"
ASR_UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"


# ---------------------------------------------------------
# Supported languages
# ---------------------------------------------------------

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "gu": "Gujarati",
    "en": "English",
}


@dataclass
class ASRResult:
    """
    Result returned by the AAROH ASR service.

    asr_confidence is intentionally nullable.

    It must represent ASR/transcription confidence only.
    It must NOT be confused with:
        - ML model confidence
        - escalation probability
        - risk probability
        - language identification probability
    """

    status: str
    transcription: Optional[str]
    language: str
    asr_confidence: Optional[float]
    reason: Optional[str] = None


class ASRService:
    """
    Production ASR service for AAROH.

    Hindi/Gujarati:
        AI4Bharat IndicConformer

    English:
        faster-whisper base.en

    Models are loaded lazily and reused between requests.
    """

    _indic_model = None
    _english_model = None

    _indic_model_lock = threading.Lock()
    _english_model_lock = threading.Lock()

    # Prevent concurrent inference from competing for CPU/model resources.
    _inference_lock = threading.Lock()

    def __init__(self) -> None:
        """
        ASRService does not load models during construction.

        Models are loaded lazily on the first request for the
        corresponding language family.
        """
        pass

    # ---------------------------------------------------------
    # Model loading
    # ---------------------------------------------------------

    @classmethod
    def _get_indic_model(cls):
        """
        Load the IndicConformer model once and reuse it.
        """

        if cls._indic_model is None:
            with cls._indic_model_lock:
                if cls._indic_model is None:
                    cls._indic_model = AutoModel.from_pretrained(
                        INDIC_MODEL_NAME,
                        trust_remote_code=True,
                    )

        return cls._indic_model

    @classmethod
    def _get_english_model(cls) -> WhisperModel:
        """
        Load faster-whisper English model once and reuse it.
        """

        if cls._english_model is None:
            with cls._english_model_lock:
                if cls._english_model is None:
                    cls._english_model = WhisperModel(
                        ENGLISH_MODEL_NAME,
                        device="cpu",
                        compute_type="int8",
                    )

        return cls._english_model

    # ---------------------------------------------------------
    # Audio loading
    # ---------------------------------------------------------

    @staticmethod
    def _load_wav_tensor(audio_path: Path) -> torch.Tensor:
        """
        Load the normalized AAROH WAV file.

        Expected format:
            mono
            16-bit PCM
            16 kHz
        """

        with wave.open(str(audio_path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()

            if channels != 1:
                raise ValueError(
                    "ASR audio must be mono."
                )

            if sample_width != 2:
                raise ValueError(
                    "ASR audio must use 16-bit PCM."
                )

            if sample_rate != 16000:
                raise ValueError(
                    "ASR audio must use 16 kHz sample rate."
                )

            if frame_count <= 0:
                raise ValueError(
                    "ASR audio contains no samples."
                )

            frames = wav_file.readframes(frame_count)

        audio = torch.frombuffer(
            bytearray(frames),
            dtype=torch.int16,
        ).to(torch.float32)

        audio = audio / 32768.0

        return audio.unsqueeze(0)

    # ---------------------------------------------------------
    # IndicConformer inference
    # ---------------------------------------------------------

    @classmethod
    def _transcribe_indic(
        cls,
        audio_path: Path,
        language: str,
    ) -> ASRResult:
        """
        Transcribe Hindi/Gujarati using IndicConformer.
        """

        try:
            wav_tensor = cls._load_wav_tensor(audio_path)

        except (wave.Error, ValueError, OSError):
            return ASRResult(
                status=ASR_FAILED,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="INVALID_ASR_AUDIO",
            )

        try:
            model = cls._get_indic_model()

            with cls._inference_lock:
                with torch.inference_mode():
                    transcription = model(
                        wav_tensor,
                        language,
                        "ctc",
                    )

        except Exception:
            return ASRResult(
                status=ASR_FAILED,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="ASR_INFERENCE_FAILED",
            )

        if not isinstance(transcription, str):
            return ASRResult(
                status=ASR_FAILED,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="INVALID_ASR_OUTPUT",
            )

        transcription = transcription.strip()

        if not transcription:
            return ASRResult(
                status=ASR_NO_SPEECH,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="NO_TRANSCRIPTION",
            )

        # IndicConformer CTC path currently does not expose a
        # calibrated transcription-confidence value.
        #
        # Therefore we deliberately keep this NULL instead of
        # inventing or mislabelling a confidence score.
        return ASRResult(
            status=ASR_SUCCESS,
            transcription=transcription,
            language=language,
            asr_confidence=None,
            reason=None,
        )

    # ---------------------------------------------------------
    # English inference
    # ---------------------------------------------------------

    @classmethod
    def _transcribe_english(
        cls,
        audio_path: Path,
    ) -> ASRResult:
        """
        Transcribe English using faster-whisper.
        """

        try:
            model = cls._get_english_model()

            with cls._inference_lock:
                segments, _info = model.transcribe(
                    str(audio_path),
                    language="en",
                    task="transcribe",
                    beam_size=5,
                    vad_filter=True,
                )

                segments = list(segments)

        except Exception:
            return ASRResult(
                status=ASR_FAILED,
                transcription=None,
                language="en",
                asr_confidence=None,
                reason="ASR_INFERENCE_FAILED",
            )

        transcription = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        if not transcription:
            return ASRResult(
                status=ASR_NO_SPEECH,
                transcription=None,
                language="en",
                asr_confidence=None,
                reason="NO_TRANSCRIPTION",
            )

        # faster-whisper's language_probability is NOT the same
        # thing as transcription confidence.
        #
        # Do not put it into asr_confidence.
        #
        # Until a proper/calibrated transcription-confidence
        # measure is introduced, keep this field NULL.
        return ASRResult(
            status=ASR_SUCCESS,
            transcription=transcription,
            language="en",
            asr_confidence=None,
            reason=None,
        )

    # ---------------------------------------------------------
    # Public transcription API
    # ---------------------------------------------------------

    def transcribe(
        self,
        audio_path: str | Path,
        language: str,
    ) -> ASRResult:
        """
        Transcribe an audio file.

        Parameters:
            audio_path:
                Path to normalized 16 kHz mono PCM WAV.

            language:
                Supported language code:
                    hi = Hindi
                    gu = Gujarati
                    en = English
        """

        # Validate language before touching the filesystem.
        if language not in SUPPORTED_LANGUAGES:
            return ASRResult(
                status=ASR_UNSUPPORTED_LANGUAGE,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="UNSUPPORTED_LANGUAGE",
            )

        path = Path(audio_path)

        if not path.exists() or not path.is_file():
            return ASRResult(
                status=ASR_FAILED,
                transcription=None,
                language=language,
                asr_confidence=None,
                reason="AUDIO_FILE_NOT_FOUND",
            )

        if language == "en":
            return self._transcribe_english(path)

        return self._transcribe_indic(
            path,
            language,
        )