from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Protocol, Sequence

from backend.voice.audio_quality import (
    AudioQualityResult,
    assess_audio_quality,
)
from backend.voice.baseline import (
    VoiceBaseline,
    calculate_baseline_deviation,
    calculate_voice_baseline,
)
from backend.voice.energy_variation import (
    EnergyVariationResult,
    calculate_energy_variation,
)
from backend.voice.pause_features import (
    PauseFeatureResult,
    calculate_pause_features,
)
from backend.voice.pitch_variability import (
    PitchVariabilityResult,
    calculate_pitch_variability,
)
from backend.voice.response_latency import (
    ResponseLatencyResult,
    calculate_response_latency,
)
from backend.voice.speech_rate import (
    SpeechRateResult,
    calculate_speech_rate,
)
from backend.voice.vad import (
    VADResult,
    VADService,
)


class VADServiceProtocol(Protocol):
    """
    Interface required by VoiceFeatureExtractor for VAD services.

    Both the real VADService and test doubles such as FakeVADService
    can satisfy this interface.
    """

    def detect(self, audio_path: str | Path) -> VADResult:
        ...


@dataclass
class VoiceFeatureSet:
    speech_rate: Optional[float]
    pause_ratio: Optional[float]
    response_latency: Optional[float]
    pitch_variability: Optional[float]
    energy_variation: Optional[float]
    audio_quality: Optional[float]
    baseline_deviation: Optional[float]

    quality_level: Optional[str]
    usable: bool

    reasons: tuple[str, ...]


class VoiceFeatureExtractor:
    """
    Orchestrates extraction of all locked voice features.

    This class does not:
    - calculate distress
    - calculate escalation probability
    - make intervention decisions
    - write to the database
    - convert missing features into zero

    It only produces voice-derived features.
    """

    def __init__(
        self,
        vad_service: Optional[VADServiceProtocol] = None,
    ) -> None:
        self.vad_service = vad_service or VADService()

    def extract(
        self,
        audio_path: str | Path,
        transcription: Optional[str],
        prompt_end_seconds: Optional[float],
        baseline: Optional[VoiceBaseline] = None,
        historical_sessions: Optional[
            Sequence[Mapping[str, Optional[float]]]
        ] = None,
    ) -> VoiceFeatureSet:

        path = Path(audio_path)
        reasons: list[str] = []

        # ---------------------------------------------------------
        # 1. Audio quality
        # ---------------------------------------------------------
        try:
            quality: AudioQualityResult = assess_audio_quality(path)
        except (OSError, ValueError, EOFError) as exc:
            return VoiceFeatureSet(
                speech_rate=None,
                pause_ratio=None,
                response_latency=None,
                pitch_variability=None,
                energy_variation=None,
                audio_quality=None,
                baseline_deviation=None,
                quality_level=None,
                usable=False,
                reasons=(f"AUDIO_QUALITY_FAILED:{type(exc).__name__}",),
            )

        if not quality.usable:
            return VoiceFeatureSet(
                speech_rate=None,
                pause_ratio=None,
                response_latency=None,
                pitch_variability=None,
                energy_variation=None,
                audio_quality=quality.audio_quality,
                baseline_deviation=None,
                quality_level=quality.quality_level,
                usable=False,
                reasons=(
                    quality.reason or "AUDIO_UNUSABLE",
                ),
            )

        # Audio quality succeeded, but duration must still be available.
        if quality.duration_seconds is None:
            return VoiceFeatureSet(
                speech_rate=None,
                pause_ratio=None,
                response_latency=None,
                pitch_variability=None,
                energy_variation=None,
                audio_quality=quality.audio_quality,
                baseline_deviation=None,
                quality_level=quality.quality_level,
                usable=False,
                reasons=("AUDIO_DURATION_UNAVAILABLE",),
            )

        recording_duration = quality.duration_seconds

        # ---------------------------------------------------------
        # 2. Voice activity detection
        # ---------------------------------------------------------
        vad_result: VADResult = self.vad_service.detect(path)

        if not vad_result.usable:
            return VoiceFeatureSet(
                speech_rate=None,
                pause_ratio=None,
                response_latency=None,
                pitch_variability=None,
                energy_variation=None,
                audio_quality=quality.audio_quality,
                baseline_deviation=None,
                quality_level=quality.quality_level,
                usable=False,
                reasons=(
                    vad_result.reason or "VAD_UNUSABLE",
                ),
            )

        # ---------------------------------------------------------
        # 3. Pause ratio
        # ---------------------------------------------------------
        pause_result: PauseFeatureResult = calculate_pause_features(
            vad_result,
            recording_duration,
        )

        # ---------------------------------------------------------
        # 4. Speech rate
        # ---------------------------------------------------------
        speech_rate_result: SpeechRateResult = calculate_speech_rate(
            vad_result,
            transcription,
        )

        # ---------------------------------------------------------
        # 5. Response latency
        # ---------------------------------------------------------
        latency_result: ResponseLatencyResult = calculate_response_latency(
            vad_result,
            prompt_end_seconds,
        )

        # ---------------------------------------------------------
        # 6. Pitch variability
        # ---------------------------------------------------------
        pitch_result: PitchVariabilityResult = calculate_pitch_variability(
            path,
            vad_result,
        )

        # ---------------------------------------------------------
        # 7. Energy variation
        # ---------------------------------------------------------
        energy_result: EnergyVariationResult = calculate_energy_variation(
            path,
            vad_result,
        )

        # ---------------------------------------------------------
        # 8. Current feature map
        # ---------------------------------------------------------
        current_features: dict[str, Optional[float]] = {
            "speech_rate": speech_rate_result.speech_rate,
            "pause_ratio": pause_result.pause_ratio,
            "response_latency": latency_result.response_latency,
            "pitch_variability": pitch_result.pitch_variability,
            "energy_variation": energy_result.energy_variation,
        }

        # ---------------------------------------------------------
        # 9. Baseline deviation
        # ---------------------------------------------------------
        baseline_deviation: Optional[float] = None

        if baseline is not None:
            baseline_result = calculate_baseline_deviation(
                current_features,
                baseline,
            )

            baseline_deviation = baseline_result.baseline_deviation

            if baseline_result.reason is not None:
                reasons.append(baseline_result.reason)

        elif historical_sessions is not None:
            calculated_baseline = calculate_voice_baseline(
                historical_sessions,
            )

            baseline_result = calculate_baseline_deviation(
                current_features,
                calculated_baseline,
            )

            baseline_deviation = baseline_result.baseline_deviation

            if baseline_result.reason is not None:
                reasons.append(baseline_result.reason)

        # ---------------------------------------------------------
        # 10. Preserve individual feature failure reasons
        # ---------------------------------------------------------
        feature_results = (
            ("pause_ratio", pause_result.reason),
            ("speech_rate", speech_rate_result.reason),
            ("response_latency", latency_result.reason),
            ("pitch_variability", pitch_result.reason),
            ("energy_variation", energy_result.reason),
        )

        for feature_name, reason in feature_results:
            if reason is not None:
                reasons.append(f"{feature_name}:{reason}")

        return VoiceFeatureSet(
            speech_rate=speech_rate_result.speech_rate,
            pause_ratio=pause_result.pause_ratio,
            response_latency=latency_result.response_latency,
            pitch_variability=pitch_result.pitch_variability,
            energy_variation=energy_result.energy_variation,
            audio_quality=quality.audio_quality,
            baseline_deviation=baseline_deviation,
            quality_level=quality.quality_level,
            usable=True,
            reasons=tuple(reasons),
        )