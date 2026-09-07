import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.voice.audio_quality import (
    QUALITY_GOOD,
    QUALITY_POOR_BUT_USABLE,
    QUALITY_UNUSABLE,
    assess_audio_quality,
)


class TestAudioQuality(unittest.TestCase):

    @staticmethod
    def generate_audio(
        duration: float = 2.0,
        volume: float = 1.0,
    ) -> bytes:
        """
        Generate synthetic mono PCM WAV audio.

        No real human/victim recordings are used.
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
            "16000",
            "-ac",
            "1",
            "-af",
            f"volume={volume}",
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

    @staticmethod
    def write_temp_audio(audio: bytes) -> Path:
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        )

        temp_file.write(audio)
        temp_file.close()

        return Path(temp_file.name)

    def test_good_audio(self):
        audio = self.generate_audio(
            duration=2.0,
            volume=1.0,
        )

        path = self.write_temp_audio(audio)

        try:
            result = assess_audio_quality(path)

            self.assertTrue(result.usable)
            self.assertEqual(
                result.quality_level,
                QUALITY_GOOD,
            )
            self.assertGreaterEqual(
                result.audio_quality,
                0.70,
            )
            self.assertIsNotNone(result.duration_seconds)
            self.assertIsNotNone(result.rms_energy)
            self.assertIsNotNone(result.silence_ratio)
            self.assertIsNotNone(result.clipping_ratio)

        finally:
            path.unlink(missing_ok=True)

    def test_quiet_audio_is_poor_or_unusable(self):
        audio = self.generate_audio(
            duration=2.0,
            volume=0.01,
        )

        path = self.write_temp_audio(audio)

        try:
            result = assess_audio_quality(path)

            self.assertIn(
                result.quality_level,
                {
                    QUALITY_POOR_BUT_USABLE,
                    QUALITY_UNUSABLE,
                },
            )
            self.assertLess(
                result.audio_quality,
                0.70,
            )

        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_is_unusable(self):
        result = assess_audio_quality(
            "this_file_does_not_exist.wav"
        )

        self.assertFalse(result.usable)
        self.assertEqual(
            result.quality_level,
            QUALITY_UNUSABLE,
        )
        self.assertEqual(
            result.reason,
            "AUDIO_FILE_NOT_FOUND",
        )

    def test_empty_wav_is_unusable(self):
        audio = self.generate_audio(
            duration=0.01,
            volume=0.0,
        )

        path = self.write_temp_audio(audio)

        try:
            result = assess_audio_quality(path)

            self.assertFalse(result.usable)
            self.assertEqual(
                result.quality_level,
                QUALITY_UNUSABLE,
            )

        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()