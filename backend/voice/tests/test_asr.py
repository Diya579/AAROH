import tempfile
import unittest
import wave
from pathlib import Path

from backend.voice.asr import (
    ASR_FAILED,
    ASR_NO_SPEECH,
    ASR_UNSUPPORTED_LANGUAGE,
    ASRService,
    SUPPORTED_LANGUAGES,
)


class TestASRService(unittest.TestCase):

    def setUp(self):
        self.service = ASRService()

    def test_supported_languages_are_defined(self):
        self.assertEqual(
            set(SUPPORTED_LANGUAGES.keys()),
            {"hi", "gu", "en"},
        )

    def test_missing_audio_returns_failure(self):
        result = self.service.transcribe(
            "does_not_exist.wav",
            "hi",
        )

        self.assertEqual(
            result.status,
            ASR_FAILED,
        )

        self.assertIsNone(result.transcription)
        self.assertIsNone(result.asr_confidence)
        self.assertEqual(
            result.reason,
            "AUDIO_FILE_NOT_FOUND",
        )

    def test_unsupported_language_is_rejected(self):
        result = self.service.transcribe(
            "does_not_exist.wav",
            "ta",
        )

        self.assertEqual(
            result.status,
            ASR_UNSUPPORTED_LANGUAGE,
        )

        self.assertIsNone(result.transcription)
        self.assertIsNone(result.asr_confidence)
        self.assertEqual(
            result.reason,
            "UNSUPPORTED_LANGUAGE",
        )

    def test_empty_audio_returns_no_speech(self):
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        )

        path = Path(temp_file.name)
        temp_file.close()

        try:
            with wave.open(str(path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b"")

            result = self.service.transcribe(
                path,
                "en",
            )

            self.assertIn(
                result.status,
                {ASR_FAILED, ASR_NO_SPEECH},
            )

            self.assertIsNone(result.transcription)

        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()