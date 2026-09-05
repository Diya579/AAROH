"""ML Input Assembly layer (Slice 3.1).

Combines TextFeatures, BehaviouralFeatures, EngagementFeatures, LongitudinalFeatures,
and optional VoiceFeatures into a standardized, deterministic ML input representation (MLInput).

Guarantees:
- Centralized, permanent feature ordering via FEATURE_REGISTRY (User Modification).
- Explainability mapping: feature index → feature name → original source.
- Strict preservation of the None != 0 invariant.
- Schema validation, range validation, and optional feature masking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Iterable, Mapping, Optional, Sequence

from backend.ml.features.behavioural import extract_behavioural_features
from backend.ml.features.engagement import extract_engagement_features
from backend.ml.features.extractor import extract_text_features
from backend.ml.features.longitudinal import extract_longitudinal_features
from backend.ml.features.registry import (
    FEATURE_NAMES,
    FEATURE_REGISTRY,
    FEATURE_SOURCES,
    ML_INPUT_SCHEMA_VERSION,
    TOTAL_FEATURES_COUNT,
    get_feature_definition,
    validate_feature_value,
)
from backend.ml.features.types import (
    BehaviouralFeatures,
    EngagementFeatures,
    LongitudinalFeatures,
    TextFeatures,
)
from backend.ml.features.voice import VoiceFeatures
from backend.ml.preprocessing import PreprocessedInteraction


@dataclass(frozen=True)
class MLInput:
    """Standardized, immutable container for all assembled ML features.

    Preserves the None != 0 invariant: missing features remain explicitly None.
    Maintains a deterministic feature vector aligned with FEATURE_REGISTRY.
    """

    schema_version: str
    case_id: str
    interaction_date: str
    text_features: TextFeatures
    behavioural_features: BehaviouralFeatures
    engagement_features: EngagementFeatures
    longitudinal_features: LongitudinalFeatures
    voice_features: Optional[VoiceFeatures]
    feature_names: tuple[str, ...]
    feature_sources: tuple[str, ...]
    feature_values: tuple[Optional[float], ...]
    available_features: tuple[str, ...]
    missing_features: tuple[str, ...]
    feature_mask: tuple[bool, ...]
    metadata: Mapping[str, Any]

    def feature_vector(
        self, impute_missing: Optional[float] = None
    ) -> tuple[Optional[float], ...]:
        """Returns the ordered, deterministic numeric feature representation.

        Preserves None != 0 by default. If impute_missing is provided,
        replaces None (or masked values) with that specified value.
        """
        if impute_missing is None:
            return self.feature_values

        return tuple(
            impute_missing if (val is None or not self.feature_mask[i]) else val
            for i, val in enumerate(self.feature_values)
        )

    def get_feature(self, name_or_index: str | int) -> Optional[float]:
        """Returns the numerical feature value by name or index."""
        defn = get_feature_definition(name_or_index)
        return self.feature_values[defn.index]

    def get_feature_metadata(self, name_or_index: str | int) -> dict[str, Any]:
        """Returns the explainability mapping: index → name → source + value."""
        defn = get_feature_definition(name_or_index)
        val = self.feature_values[defn.index]
        is_masked = not self.feature_mask[defn.index]
        return {
            "index": defn.index,
            "name": defn.name,
            "source": defn.source,
            "description": defn.description,
            "value": val,
            "is_available": val is not None,
            "is_masked": is_masked,
            "min_value": defn.min_value,
            "max_value": defn.max_value,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serializes the assembled ML input to a dictionary."""
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "interaction_date": self.interaction_date,
            "feature_count": len(self.feature_values),
            "available_feature_count": len(self.available_features),
            "missing_feature_count": len(self.missing_features),
            "feature_vector": list(self.feature_vector()),
            "feature_mask": list(self.feature_mask),
            "available_features": list(self.available_features),
            "missing_features": list(self.missing_features),
            "text": self.text_features.to_dict(),
            "behavioural": self.behavioural_features.to_dict(),
            "engagement": self.engagement_features.to_dict(),
            "longitudinal": self.longitudinal_features.to_dict(),
            "voice": None if self.voice_features is None else self.voice_features.to_dict(),
            "metadata": dict(self.metadata),
        }


class MLInputAssembler:
    """Assembles multimodal features into a standardized MLInput object.

    Enforces schema checks, range validation, feature registry indexing,
    and deterministic ordering.
    """

    def assemble(
        self,
        text_features: TextFeatures,
        behavioural_features: BehaviouralFeatures,
        engagement_features: EngagementFeatures,
        longitudinal_features: LongitudinalFeatures,
        voice_features: Optional[VoiceFeatures] = None,
        case_id: str = "",
        interaction_date: str = "",
        mask_feature_names: Optional[Collection[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> MLInput:
        """Assembles feature objects into a deterministic MLInput."""
        # 1. Strict Schema / Type Validation
        if not isinstance(text_features, TextFeatures):
            raise TypeError(
                f"Expected TextFeatures instance, got {type(text_features).__name__}"
            )
        if not isinstance(behavioural_features, BehaviouralFeatures):
            raise TypeError(
                f"Expected BehaviouralFeatures instance, got {type(behavioural_features).__name__}"
            )
        if not isinstance(engagement_features, EngagementFeatures):
            raise TypeError(
                f"Expected EngagementFeatures instance, got {type(engagement_features).__name__}"
            )
        if not isinstance(longitudinal_features, LongitudinalFeatures):
            raise TypeError(
                f"Expected LongitudinalFeatures instance, got {type(longitudinal_features).__name__}"
            )
        if voice_features is not None and not isinstance(voice_features, VoiceFeatures):
            raise TypeError(
                f"Expected VoiceFeatures instance or None, got {type(voice_features).__name__}"
            )

        # 2. Extract values from each modality
        raw_values: dict[str, Optional[float]] = {}

        # --- Text features ---
        if text_features.text_available:
            if text_features.lexical is not None:
                lex = text_features.lexical
                raw_values["text_word_count"] = float(lex.word_count)
                raw_values["text_character_count"] = float(lex.character_count)
                raw_values["text_sentence_count"] = float(lex.sentence_count)
                raw_values["text_average_word_length"] = float(lex.average_word_length)
                raw_values["text_uppercase_ratio"] = float(lex.uppercase_ratio)
                raw_values["text_punctuation_ratio"] = float(lex.punctuation_ratio)

            if text_features.distress is not None:
                d = text_features.distress
                raw_values["text_fear"] = float(d.fear)
                raw_values["text_hopelessness"] = float(d.hopelessness)
                raw_values["text_isolation"] = float(d.isolation)
                raw_values["text_helplessness"] = float(d.helplessness)
                raw_values["text_intimidation"] = float(d.intimidation)
                raw_values["text_sadness"] = float(d.sadness)
                raw_values["text_anxiety"] = float(d.anxiety)

            if text_features.help_seeking is not None:
                hs = text_features.help_seeking
                raw_values["text_asking_for_help"] = float(hs.asking_for_help)
                raw_values["text_requesting_support"] = float(hs.requesting_support)
                raw_values["text_emergency_language"] = float(hs.emergency_language)

            if text_features.safety is not None:
                sf = text_features.safety
                raw_values["text_urgency"] = float(sf.urgency)
                raw_values["text_danger_related_wording"] = float(sf.danger_related_wording)

        # --- Behavioural features ---
        if behavioural_features.behavioural_available:
            b = behavioural_features
            raw_values["behavioural_safety_distress"] = b.safety_distress
            raw_values["behavioural_sleep_disturbance"] = b.sleep_disturbance
            raw_values["behavioural_fear_intensity"] = b.fear_intensity
            raw_values["behavioural_low_social_support"] = b.low_social_support
            raw_values["behavioural_help_requested"] = b.help_requested
            raw_values["behavioural_composite_distress"] = b.composite_distress
            raw_values["behavioural_change_from_previous"] = b.change_from_previous
            raw_values["behavioural_change_from_baseline"] = b.change_from_baseline

        # --- Engagement features ---
        if engagement_features.engagement_available:
            e = engagement_features
            raw_values["engagement_completed_checkin"] = e.completed_checkin
            raw_values["engagement_missed_checkin"] = e.missed_checkin
            raw_values["engagement_missed_checkin_streak"] = (
                float(e.missed_checkin_streak) if e.missed_checkin_streak is not None else None
            )
            raw_values["engagement_checkin_consistency"] = e.checkin_consistency
            raw_values["engagement_response_delay"] = e.response_delay
            raw_values["engagement_average_response_delay"] = e.average_response_delay
            raw_values["engagement_response_frequency"] = e.response_frequency
            raw_values["engagement_engagement_drop"] = e.engagement_drop
            raw_values["engagement_recent_activity_count"] = (
                float(e.recent_activity_count) if e.recent_activity_count is not None else None
            )
            raw_values["engagement_inactivity_duration"] = e.inactivity_duration
            raw_values["engagement_score"] = e.engagement_score
            raw_values["engagement_change_from_previous"] = e.change_from_previous
            raw_values["engagement_change_from_baseline"] = e.change_from_baseline

        # --- Longitudinal features ---
        if longitudinal_features.longitudinal_available:
            l = longitudinal_features
            raw_values["longitudinal_observation_count"] = float(l.observation_count)
            raw_values["longitudinal_history_span_days"] = (
                float(l.history_span_days) if l.history_span_days is not None else None
            )
            raw_values["longitudinal_current_distress"] = l.current_distress
            raw_values["longitudinal_baseline_distress"] = l.baseline_distress
            raw_values["longitudinal_previous_distress"] = l.previous_distress
            raw_values["longitudinal_delta_from_baseline"] = l.delta_from_baseline
            raw_values["longitudinal_delta_from_previous"] = l.delta_from_previous
            raw_values["longitudinal_distress_velocity"] = l.distress_velocity
            raw_values["longitudinal_distress_acceleration"] = l.distress_acceleration
            raw_values["longitudinal_distress_volatility"] = l.distress_volatility
            raw_values["longitudinal_peak_distress"] = l.peak_distress
            raw_values["longitudinal_trough_distress"] = l.trough_distress
            raw_values["longitudinal_sustained_distress_count"] = (
                float(l.sustained_distress_count) if l.sustained_distress_count is not None else None
            )

        # --- Voice features (Optional) ---
        if voice_features is not None and voice_features.voice_available:
            v = voice_features
            raw_values["voice_speech_rate"] = v.speech_rate
            raw_values["voice_pause_ratio"] = v.pause_ratio
            raw_values["voice_response_latency"] = v.response_latency
            raw_values["voice_pitch_variability"] = v.pitch_variability
            raw_values["voice_energy_variation"] = v.energy_variation
            raw_values["voice_audio_quality"] = v.audio_quality
            raw_values["voice_asr_confidence"] = v.asr_confidence
            raw_values["voice_baseline_deviation"] = v.baseline_deviation

        # 3. Assemble strictly by FEATURE_REGISTRY ordering
        values_list: list[Optional[float]] = []
        available: list[str] = []
        missing: list[str] = []
        mask: list[bool] = []
        masked_names = set(mask_feature_names or ())

        for defn in FEATURE_REGISTRY:
            val = raw_values.get(defn.name)

            # Range validation (rejects invalid feature values with descriptive errors)
            if val is not None:
                validate_feature_value(defn.name, val)
                values_list.append(val)
                available.append(defn.name)
                # Feature is present; mask is True unless explicitly masked
                mask.append(defn.name not in masked_names)
            else:
                # Missing value: preserve None != 0
                values_list.append(None)
                missing.append(defn.name)
                mask.append(False)

        return MLInput(
            schema_version=ML_INPUT_SCHEMA_VERSION,
            case_id=case_id,
            interaction_date=interaction_date,
            text_features=text_features,
            behavioural_features=behavioural_features,
            engagement_features=engagement_features,
            longitudinal_features=longitudinal_features,
            voice_features=voice_features,
            feature_names=FEATURE_NAMES,
            feature_sources=FEATURE_SOURCES,
            feature_values=tuple(values_list),
            available_features=tuple(available),
            missing_features=tuple(missing),
            feature_mask=tuple(mask),
            metadata=dict(metadata or {}),
        )

    def assemble_from_preprocessed(
        self,
        interaction: PreprocessedInteraction,
        history: Optional[Sequence[PreprocessedInteraction]] = None,
        voice_features: Optional[VoiceFeatures] = None,
        mask_feature_names: Optional[Collection[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> MLInput:
        """Convenience helper extracting multimodal features and assembling an MLInput."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError(
                "assemble_from_preprocessed requires a PreprocessedInteraction instance"
            )

        text_feat = extract_text_features(interaction)
        beh_feat = extract_behavioural_features(interaction, history=history)
        eng_feat = extract_engagement_features(interaction, history=history)
        long_feat = extract_longitudinal_features(interaction, history=history)

        voice_feat = voice_features
        if voice_feat is None and not interaction.missingness.is_voice_missing:
            voice_feat = VoiceFeatures.from_preprocessed(interaction)

        return self.assemble(
            text_features=text_feat,
            behavioural_features=beh_feat,
            engagement_features=eng_feat,
            longitudinal_features=long_feat,
            voice_features=voice_feat,
            case_id=interaction.case_id,
            interaction_date=interaction.interaction_date,
            mask_feature_names=mask_feature_names,
            metadata=metadata,
        )

    def assemble_batch(
        self,
        items: Iterable[
            tuple[
                TextFeatures,
                BehaviouralFeatures,
                EngagementFeatures,
                LongitudinalFeatures,
                Optional[VoiceFeatures],
            ]
        ],
        case_ids: Optional[Sequence[str]] = None,
    ) -> list[MLInput]:
        """Assembles multiple feature tuples in batch."""
        results: list[MLInput] = []
        for i, item in enumerate(items):
            cid = case_ids[i] if case_ids and i < len(case_ids) else ""
            results.append(
                self.assemble(
                    text_features=item[0],
                    behavioural_features=item[1],
                    engagement_features=item[2],
                    longitudinal_features=item[3],
                    voice_features=item[4],
                    case_id=cid,
                )
            )
        return results


# Functional convenience entry points
_DEFAULT_ASSEMBLER = MLInputAssembler()


def assemble_ml_input(
    text_features: TextFeatures,
    behavioural_features: BehaviouralFeatures,
    engagement_features: EngagementFeatures,
    longitudinal_features: LongitudinalFeatures,
    voice_features: Optional[VoiceFeatures] = None,
    case_id: str = "",
    interaction_date: str = "",
    mask_feature_names: Optional[Collection[str]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> MLInput:
    """Convenience function to assemble an MLInput using the default assembler."""
    return _DEFAULT_ASSEMBLER.assemble(
        text_features=text_features,
        behavioural_features=behavioural_features,
        engagement_features=engagement_features,
        longitudinal_features=longitudinal_features,
        voice_features=voice_features,
        case_id=case_id,
        interaction_date=interaction_date,
        mask_feature_names=mask_feature_names,
        metadata=metadata,
    )


def assemble_ml_input_batch(
    items: Iterable[
        tuple[
            TextFeatures,
            BehaviouralFeatures,
            EngagementFeatures,
            LongitudinalFeatures,
            Optional[VoiceFeatures],
        ]
    ],
    case_ids: Optional[Sequence[str]] = None,
) -> list[MLInput]:
    """Convenience function to assemble multiple MLInputs in batch."""
    return _DEFAULT_ASSEMBLER.assemble_batch(items, case_ids=case_ids)
