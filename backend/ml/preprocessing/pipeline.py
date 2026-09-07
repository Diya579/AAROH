"""Preprocessing pipeline orchestrator.

Chains input validation, multilingual Unicode text normalization, and missingness
assessment into a standardized, deterministic PreprocessedInteraction record.
Preserves unknown fields in `metadata` for forward compatibility.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from backend.ml.preprocessing.missingness import assess_missingness
from backend.ml.preprocessing.text import preprocess_text
from backend.ml.preprocessing.types import (
    NormalizedText,
    PreprocessedInteraction,
    ValidationResult,
)
from backend.ml.preprocessing.validation import (
    KNOWN_INTERACTION_FIELDS,
    validate_interaction_payload,
)


class InteractionPreprocessingPipeline:
    """Deterministic preprocessing pipeline for single interactions.

    Guarantees:
    - Multilingual Unicode preservation (NFKC).
    - Missing values remain explicitly None (no zero imputation).
    - Unknown/unrecognized fields are preserved in ``metadata``.
    - Unknown languages are preserved with a warning, not failing the pipeline.
    """

    def __init__(
        self,
        *,
        lowercase_text: bool = True,
        unicode_form: str = "NFKC",
    ) -> None:
        self.lowercase_text = lowercase_text
        self.unicode_form = unicode_form

    def validate(self, raw_interaction: Mapping[str, Any]) -> ValidationResult:
        """Validates interaction fields and returns a ValidationResult."""
        return validate_interaction_payload(raw_interaction)

    def process_text(
        self, raw_text: Optional[str], language: Optional[str]
    ) -> Optional[NormalizedText]:
        """Normalizes and quality-checks text."""
        return preprocess_text(
            raw_text,
            language=language,
            lowercase=self.lowercase_text,
            unicode_form=self.unicode_form,
        )

    def extract_unrecognized_metadata(
        self, raw_interaction: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Extracts any unknown/unrecognized fields into a metadata dictionary.

        Ensures forward compatibility so future feature additions are never lost.
        """
        return {
            k: v
            for k, v in raw_interaction.items()
            if k not in KNOWN_INTERACTION_FIELDS
        }

    def transform(self, raw_interaction: Mapping[str, Any]) -> PreprocessedInteraction:
        """Transforms a raw interaction dictionary into a PreprocessedInteraction."""
        # 1. Validation
        validation = self.validate(raw_interaction)
        cleaned = validation.cleaned_data

        case_id = cleaned.get("case_id") or str(raw_interaction.get("case_id", "UNKNOWN"))
        interaction_date = cleaned.get("interaction_date") or str(
            raw_interaction.get("interaction_date", "")
        )
        language = cleaned.get("language", "unknown")

        # 2. Text Normalization
        text_input = cleaned.get("text_response")
        norm_text = self.process_text(text_input, language=language)

        # 3. Behavioural ratings (explicitly preserving None, never 0)
        behavioural: dict[str, Optional[float]] = {
            "safety_response": (
                float(cleaned["safety_response"])
                if cleaned.get("safety_response") is not None
                else None
            ),
            "sleep_disruption": (
                float(cleaned["sleep_disruption"])
                if cleaned.get("sleep_disruption") is not None
                else None
            ),
            "fear_level": (
                float(cleaned["fear_level"])
                if cleaned.get("fear_level") is not None
                else None
            ),
            "social_support": (
                float(cleaned["social_support"])
                if cleaned.get("social_support") is not None
                else None
            ),
        }

        # 4. Engagement flags
        engagement: dict[str, Any] = {
            "response_completed": cleaned.get("response_completed", True),
            "voice_available": cleaned.get("voice_available", False),
            "help_requested": cleaned.get("help_requested", False),
            "data_quality": cleaned.get("data_quality", "good"),
            "channel": raw_interaction.get("channel"),
        }

        # 5. Voice metrics (preserving None)
        voice_keys = (
            "speech_rate",
            "pause_ratio",
            "response_latency",
            "pitch_variability",
            "energy_variation",
            "audio_quality",
            "asr_confidence",
        )
        voice: dict[str, Optional[float]] = {
            vk: cleaned.get(vk) for vk in voice_keys
        }

        # 6. Forward-compatible metadata (capturing unrecognized fields)
        metadata = self.extract_unrecognized_metadata(raw_interaction)

        # 7. Missingness Assessment
        missingness = assess_missingness(cleaned)

        return PreprocessedInteraction(
            case_id=case_id,
            interaction_date=interaction_date,
            language=language,
            text=norm_text,
            behavioural=behavioural,
            engagement=engagement,
            voice=voice,
            metadata=metadata,
            missingness=missingness,
            validation=validation,
        )

    def transform_batch(
        self, raw_interactions: Iterable[Mapping[str, Any]]
    ) -> list[PreprocessedInteraction]:
        """Processes an iterable of raw interaction payloads deterministically."""
        return [self.transform(item) for item in raw_interactions]


# Default singleton pipeline instance
_DEFAULT_PIPELINE = InteractionPreprocessingPipeline()


def preprocess_interaction(
    raw_interaction: Mapping[str, Any],
    pipeline: Optional[InteractionPreprocessingPipeline] = None,
) -> PreprocessedInteraction:
    """Convenience functional interface for preprocessing a single interaction."""
    p = pipeline or _DEFAULT_PIPELINE
    return p.transform(raw_interaction)


def preprocess_interaction_batch(
    raw_interactions: Iterable[Mapping[str, Any]],
    pipeline: Optional[InteractionPreprocessingPipeline] = None,
) -> list[PreprocessedInteraction]:
    """Convenience functional interface for preprocessing multiple interactions."""
    p = pipeline or _DEFAULT_PIPELINE
    return p.transform_batch(raw_interactions)
