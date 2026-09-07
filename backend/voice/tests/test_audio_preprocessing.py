import subprocess
import unittest

from backend.voice.audio_preprocessing import (
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    TARGET_CHANNELS,
    TARGET_SAMPLE_RATE,
    preprocess_audio,
)


class TestAudioPreprocessing(unittest.TestCase):

    @staticmethod
    def generate_test_audio(duration: float = 2.0) -> bytes:
        """
        Generate synthetic WAV audio using FFmpeg.

        This avoids using real human/victim recordings during testing.
        """

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={duration}",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            "pipe:1",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to generate test audio: "
                + result.stderr.decode(errors="replace")
            )

        return result.stdout

    def test_valid_audio_is_normalized(self):
        audio = self.generate_test_audio(2.0)

        result = preprocess_audio(
            audio,
            input_extension=".wav",
        )

        self.assertTrue(result.success)
        self.assertIsNone(result.reason)
        self.assertIsNotNone(result.duration_seconds)
        self.assertEqual(result.sample_rate, TARGET_SAMPLE_RATE)
        self.assertEqual(result.channels, TARGET_CHANNELS)
        self.assertIsNotNone(result.output_path)

    def test_empty_audio_is_rejected(self):
        result = preprocess_audio(b"", ".wav")

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "EMPTY_AUDIO")

    def test_invalid_audio_is_rejected(self):
        result = preprocess_audio(
            b"this is not audio",
            ".wav",
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.reason,
            "INVALID_OR_UNREADABLE_AUDIO",
        )

    def test_audio_too_short_is_rejected(self):
        audio = self.generate_test_audio(
            MIN_DURATION_SECONDS / 2
        )

        result = preprocess_audio(
            audio,
            ".wav",
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.reason,
            "AUDIO_TOO_SHORT",
        )

    def test_audio_too_long_is_rejected(self):
        audio = self.generate_test_audio(
            MAX_DURATION_SECONDS + 1
        )

        result = preprocess_audio(
            audio,
            ".wav",
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.reason,
            "AUDIO_TOO_LONG",
        )


if __name__ == "__main__":
    unittest.main()