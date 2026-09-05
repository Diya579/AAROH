"""Voice features contract (locked Voice → ML interface).

Encapsulates voice-derived metrics provided by the voice pipeline (Diya) as defined
in ``docs/ML_API_CONTRACT.md`` and ``docs/DATABASE_CONTRACT.md``.

This module consumes voice metrics only. It does not compute voice features or run ASR.
Preserves None != 0 for absent audio or missing metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from backend.ml.preprocessing import PreprocessedInteraction


@dataclass(frozen=True)
class VoiceFeatures:
    """Strongly typed, immutable container for voice-derived features.

    Consumes acoustic metrics produced by the Voice subsystem.
    Preserves None != 0: if voice is unavailable or a metric wasn't computed,
    it remains None.
    """

    voice_available: bool
    speech_rate: Optional[float] = None
    pause_ratio: Optional[float] = None
    response_latency: Optional[float] = None
    pitch_variability: Optional[float] = None
    energy_variation: Optional[float] = None
    audio_quality: Optional[float] = None
    asr_confidence: Optional[float] = None
    baseline_deviation: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice_available": self.voice_available,
            "speech_rate": self.speech_rate,
            "pause_ratio": self.pause_ratio,
            "response_latency": self.response_latency,
            "pitch_variability": self.pitch_variability,
            "energy_variation": self.energy_variation,
            "audio_quality": self.audio_quality,
            "asr_confidence": self.asr_confidence,
            "baseline_deviation": self.baseline_deviation,
        }

    def to_feature_dict(self) -> dict[str, Any]:
        """Flattens numerical voice features preserving None != 0."""
        features: dict[str, Any] = {
            "voice_available": int(self.voice_available),
        }
        if self.voice_available:
            for metric in (
                "speech_rate",
                "pause_ratio",
                "response_latency",
                "pitch_variability",
                "energy_variation",
                "audio_quality",
                "asr_confidence",
                "baseline_deviation",
            ):
                val = getattr(self, metric)
                if val is not None:
                    features[f"voice_{metric}"] = val
        return features

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> VoiceFeatures:
        """Constructs VoiceFeatures safely from a dictionary mapping."""
        if not data:
            return cls(voice_available=False)

        voice_avail = bool(data.get("voice_available", False))
        if not voice_avail:
            # Check if any voice metric is present even if voice_available wasn't explicitly set
            voice_avail = any(
                data.get(k) is not None
                for k in (
                    "speech_rate",
                    "pause_ratio",
                    "response_latency",
                    "pitch_variability",
                    "energy_variation",
                    "audio_quality",
                    "asr_confidence",
                    "baseline_deviation",
                )
            )

        def _get_float(key: str) -> Optional[float]:
            val = data.get(key)
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        return cls(
            voice_available=voice_avail,
            speech_rate=_get_float("speech_rate"),
            pause_ratio=_get_float("pause_ratio"),
            response_latency=_get_float("response_latency"),
            pitch_variability=_get_float("pitch_variability"),
            energy_variation=_get_float("energy_variation"),
            audio_quality=_get_float("audio_quality"),
            asr_confidence=_get_float("asr_confidence"),
            baseline_deviation=_get_float("baseline_deviation"),
        )

    @classmethod
    def from_preprocessed(cls, interaction: PreprocessedInteraction) -> VoiceFeatures:
        """Extracts VoiceFeatures from a PreprocessedInteraction record."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError("from_preprocessed requires a PreprocessedInteraction instance")

        raw_voice = interaction.voice or {}
        voice_avail = not interaction.missingness.is_voice_missing
        return cls.from_dict({**raw_voice, "voice_available": voice_avail})
