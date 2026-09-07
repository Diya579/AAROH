import unittest

from backend.voice.audio_validation import (
    MAX_AUDIO_SIZE_BYTES,
    validate_audio_input,
)


class TestAudioValidation(unittest.TestCase):

    def test_empty_audio_is_rejected(self):
        result = validate_audio_input(
            audio_bytes=b"",
            mime_type="audio/wav",
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "Audio recording is empty.")

    def test_missing_mime_type_is_rejected(self):
        result = validate_audio_input(
            audio_bytes=b"fake-audio",
            mime_type="",
        )

        self.assertFalse(result.valid)

    def test_unsupported_mime_type_is_rejected(self):
        result = validate_audio_input(
            audio_bytes=b"fake-audio",
            mime_type="video/mp4",
        )

        self.assertFalse(result.valid)

    def test_valid_wav_is_accepted(self):
        result = validate_audio_input(
            audio_bytes=b"fake-wav-data",
            mime_type="audio/wav",
            filename="recording.wav",
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.mime_type, "audio/wav")

    def test_valid_webm_is_accepted(self):
        result = validate_audio_input(
            audio_bytes=b"fake-webm-data",
            mime_type="audio/webm",
            filename="recording.webm",
        )

        self.assertTrue(result.valid)

    def test_oversized_audio_is_rejected(self):
        audio = b"x" * (MAX_AUDIO_SIZE_BYTES + 1)

        result = validate_audio_input(
            audio_bytes=audio,
            mime_type="audio/wav",
        )

        self.assertFalse(result.valid)

    def test_invalid_extension_is_rejected(self):
        result = validate_audio_input(
            audio_bytes=b"fake-audio",
            mime_type="audio/wav",
            filename="recording.txt",
        )

        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()