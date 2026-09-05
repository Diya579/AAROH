from __future__ import annotations

import threading
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch
from silero_vad import load_silero_vad, get_speech_timestamps


SAMPLE_RATE = 16000
MIN_SPEECH_DURATION_SECONDS = 0.05


@dataclass
class SpeechSegment:
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


@dataclass
class VADResult:
    usable: bool
    speech_segments: List[SpeechSegment]
    speech_duration_seconds: float
    speech_ratio: Optional[float]
    silence_ratio: Optional[float]
    reason: Optional[str] = None


class VADService:
    _model = None
    _model_lock = threading.Lock()

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            with cls._model_lock:
                if cls._model is None:
                    cls._model = load_silero_vad()
        return cls._model

    @staticmethod
    def _load_wav(audio_path: Path) -> torch.Tensor:
        with wave.open(str(audio_path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()

            if channels != 1:
                raise ValueError("WAV must be mono.")

            if sample_width != 2:
                raise ValueError("WAV must be 16-bit PCM.")

            if sample_rate != SAMPLE_RATE:
                raise ValueError("WAV must be 16 kHz.")

            if frame_count <= 0:
                raise ValueError("WAV contains no audio.")

            frames = wav_file.readframes(frame_count)

        audio = torch.frombuffer(
            bytearray(frames),
            dtype=torch.int16,
        ).to(torch.float32)

        return audio / 32768.0

    def detect(self, audio_path: str | Path) -> VADResult:
        path = Path(audio_path)

        if not path.exists() or not path.is_file():
            return VADResult(
                usable=False,
                speech_segments=[],
                speech_duration_seconds=0.0,
                speech_ratio=None,
                silence_ratio=None,
                reason="AUDIO_FILE_NOT_FOUND",
            )

        try:
            audio = self._load_wav(path)
        except (wave.Error, ValueError, OSError, EOFError):
            return VADResult(
                usable=False,
                speech_segments=[],
                speech_duration_seconds=0.0,
                speech_ratio=None,
                silence_ratio=None,
                reason="AUDIO_READ_FAILED",
            )

        duration_seconds = audio.numel() / SAMPLE_RATE

        try:
            timestamps = get_speech_timestamps(
                audio,
                self._get_model(),
                sampling_rate=SAMPLE_RATE,
            )
        except Exception:
            return VADResult(
                usable=False,
                speech_segments=[],
                speech_duration_seconds=0.0,
                speech_ratio=None,
                silence_ratio=None,
                reason="VAD_INFERENCE_FAILED",
            )

        segments = []

        for timestamp in timestamps:
            start = timestamp["start"] / SAMPLE_RATE
            end = timestamp["end"] / SAMPLE_RATE

            if end - start >= MIN_SPEECH_DURATION_SECONDS:
                segments.append(
                    SpeechSegment(
                        start_seconds=start,
                        end_seconds=end,
                    )
                )

        speech_duration = sum(
            segment.duration_seconds
            for segment in segments
        )

        speech_duration = min(
            speech_duration,
            duration_seconds,
        )

        speech_ratio = speech_duration / duration_seconds
        silence_ratio = 1.0 - speech_ratio

        usable = speech_duration > 0

        return VADResult(
            usable=usable,
            speech_segments=segments,
            speech_duration_seconds=speech_duration,
            speech_ratio=speech_ratio,
            silence_ratio=silence_ratio,
            reason=None if usable else "NO_SPEECH_DETECTED",
        )