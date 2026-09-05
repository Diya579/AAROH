"""Comprehensive unit tests for ML Input Assembly layer (Slice 3.1).

Verifies:
- Deterministic and permanent feature ordering (User Modification)
- Identical vectors across runs
- Preservation of None != 0 for missing values
- Optional voice features (consumed via locked Voice contract)
- Schema and type validation
- Explainability mapping (index → name → source)
- Schema versioning (ML_INPUT_SCHEMA_VERSION)
- Optional feature masking
- Range validation with descriptive errors
- Batch assembly and end-to-end assembly from PreprocessedInteraction
"""

import unittest

from backend.ml.features.assembly import (
    MLInput,
    MLInputAssembler,
    assemble_ml_input,
    assemble_ml_input_batch,
)
from backend.ml.features.behavioural import extract_behavioural_features
from backend.ml.features.engagement import extract_engagement_features
from backend.ml.features.extractor import extract_text_features
from backend.ml.features.longitudinal import extract_longitudinal_features
from backend.ml.features.registry import (
    FEATURE_INDEX_TO_NAME,
    FEATURE_NAME_TO_INDEX,
    FEATURE_NAMES,
    FEATURE_REGISTRY,
    FEATURE_SOURCE_MAP,
    FEATURE_SOURCES,
    ML_INPUT_SCHEMA_VERSION,
    TOTAL_FEATURES_COUNT,
    FeatureDefinition,
    get_feature_definition,
    validate_feature_value,
)
from backend.ml.features.types import (
    BehaviouralFeatures,
    DistressIndicators,
    EngagementFeatures,
    HelpSeekingIndicators,
    LexicalMetrics,
    LongitudinalFeatures,
    SafetyIndicators,
    TextFeatures,
    TextQualityMetadata,
)
from backend.ml.features.voice import VoiceFeatures
from backend.ml.preprocessing import preprocess_interaction


class TestInputAssembly(unittest.TestCase):
    def setUp(self) -> None:
        self.assembler = MLInputAssembler()

        # Build sample preprocessed interaction for reusable feature fixtures
        self.raw_interaction = {
            "case_id": "CASE-301",
            "interaction_date": "2026-09-01",
            "language": "hi",
            "text_response": "मुझे बहुत डर लग रहा है, कृपया मदद चाहिए।",
            "safety_response": 2,
            "sleep_disruption": 4,
            "fear_level": 5,
            "social_support": 1,
            "completed": True,
            "response_delay_hours": 1.5,
        }
        self.preprocessed = preprocess_interaction(self.raw_interaction)
        self.text_feat = extract_text_features(self.preprocessed)
        self.beh_feat = extract_behavioural_features(self.preprocessed)
        self.eng_feat = extract_engagement_features(self.preprocessed)
        self.long_feat = extract_longitudinal_features(self.preprocessed)

    def test_feature_registry_invariants(self) -> None:
        """Verifies feature registry is permanent, contiguous, and un-duplicated (User Modification)."""
        self.assertEqual(len(FEATURE_REGISTRY), TOTAL_FEATURES_COUNT)
        self.assertEqual(len(FEATURE_NAMES), TOTAL_FEATURES_COUNT)

        # Contiguous indices from 0 to TOTAL_FEATURES_COUNT - 1
        for i, defn in enumerate(FEATURE_REGISTRY):
            self.assertEqual(defn.index, i)
            self.assertEqual(FEATURE_NAME_TO_INDEX[defn.name], i)
            self.assertEqual(FEATURE_INDEX_TO_NAME[i], defn.name)

        # Lookup helpers
        d0 = get_feature_definition(0)
        self.assertEqual(d0.name, "text_word_count")
        d_name = get_feature_definition("longitudinal_distress_velocity")
        self.assertEqual(d_name.source, "longitudinal")

        # Invalid index / name
        with self.assertRaises(IndexError):
            get_feature_definition(9999)
        with self.assertRaises(KeyError):
            get_feature_definition("non_existent_feature")

    def test_deterministic_feature_ordering_and_vector_stability(self) -> None:
        """Verifies feature vector ordering is identical across repeated runs."""
        input1 = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
            case_id="CASE-301",
            interaction_date="2026-09-01",
        )
        input2 = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
            case_id="CASE-301",
            interaction_date="2026-09-01",
        )

        # Same vector
        vec1 = input1.feature_vector()
        vec2 = input2.feature_vector()
        self.assertEqual(vec1, vec2)
        self.assertEqual(len(vec1), TOTAL_FEATURES_COUNT)
        self.assertEqual(input1.feature_names, FEATURE_NAMES)

    def test_missing_values_preservation_none_not_zero(self) -> None:
        """Verifies None != 0: missing features remain None and are not converted to 0.0."""
        # Completely absent feature containers across all modalities
        empty_text = TextFeatures(
            text_available=False,
            lexical=None,
            distress=None,
            help_seeking=None,
            safety=None,
            quality=None,
        )
        empty_beh = BehaviouralFeatures(
            behavioural_available=False,
            safety_distress=None,
            sleep_disturbance=None,
            fear_intensity=None,
            low_social_support=None,
            help_requested=None,
            composite_distress=None,
            change_from_previous=None,
            change_from_baseline=None,
        )
        empty_eng = EngagementFeatures(
            engagement_available=False,
            completed_checkin=None,
            missed_checkin=None,
            missed_checkin_streak=None,
            checkin_consistency=None,
            response_delay=None,
            average_response_delay=None,
            response_frequency=None,
            engagement_drop=None,
            interaction_count=0,
        )
        empty_long = LongitudinalFeatures(
            longitudinal_available=False,
            observation_count=0,
            history_span_days=None,
            current_distress=None,
            baseline_distress=None,
            previous_distress=None,
            delta_from_baseline=None,
            delta_from_previous=None,
            distress_velocity=None,
            distress_acceleration=None,
            distress_volatility=None,
            peak_distress=None,
            trough_distress=None,
            sustained_distress_count=None,
            longitudinal_trend="UNKNOWN",
        )

        ml_input = self.assembler.assemble(
            text_features=empty_text,
            behavioural_features=empty_beh,
            engagement_features=empty_eng,
            longitudinal_features=empty_long,
            voice_features=None,
        )

        vector = ml_input.feature_vector()
        # All features should strictly be None
        self.assertTrue(all(v is None for v in vector))
        self.assertEqual(len(ml_input.missing_features), TOTAL_FEATURES_COUNT)
        self.assertEqual(len(ml_input.available_features), 0)

        # But explicit imputation replaces None only when requested
        imputed = ml_input.feature_vector(impute_missing=0.0)
        self.assertTrue(all(v == 0.0 for v in imputed))

        # Partial missingness: when text is present but voice is absent
        input_partial = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=empty_beh,
            engagement_features=empty_eng,
            longitudinal_features=empty_long,
            voice_features=None,
        )
        self.assertIsNotNone(input_partial.get_feature("text_word_count"))
        self.assertIsNone(input_partial.get_feature("behavioural_safety_distress"))
        self.assertIsNone(input_partial.get_feature("voice_speech_rate"))

    def test_optional_voice_features(self) -> None:
        """Verifies optional VoiceFeatures integration via the locked Voice contract."""
        # Case A: voice is None
        input_no_voice = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
            voice_features=None,
        )
        self.assertIsNone(input_no_voice.voice_features)
        self.assertIsNone(input_no_voice.get_feature("voice_speech_rate"))
        self.assertIn("voice_speech_rate", input_no_voice.missing_features)

        # Case B: voice is provided
        voice_feat = VoiceFeatures(
            voice_available=True,
            speech_rate=2.8,
            pause_ratio=0.31,
            response_latency=2.4,
            pitch_variability=0.14,
            energy_variation=0.22,
            audio_quality=0.86,
            asr_confidence=0.92,
            baseline_deviation=0.37,
        )
        input_with_voice = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
            voice_features=voice_feat,
        )
        self.assertIsNotNone(input_with_voice.voice_features)
        self.assertAlmostEqual(input_with_voice.get_feature("voice_speech_rate"), 2.8)
        self.assertAlmostEqual(input_with_voice.get_feature("voice_audio_quality"), 0.86)
        self.assertIn("voice_speech_rate", input_with_voice.available_features)

    def test_explainability_mapping(self) -> None:
        """Verifies mapping: feature index → feature name → original source."""
        ml_input = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
        )

        meta_fear = ml_input.get_feature_metadata("text_fear")
        self.assertEqual(meta_fear["name"], "text_fear")
        self.assertEqual(meta_fear["source"], "text")
        self.assertEqual(meta_fear["index"], FEATURE_NAME_TO_INDEX["text_fear"])
        self.assertTrue(meta_fear["is_available"])

        meta_beh = ml_input.get_feature_metadata("behavioural_composite_distress")
        self.assertEqual(meta_beh["source"], "behavioural")

        meta_long = ml_input.get_feature_metadata("longitudinal_current_distress")
        self.assertEqual(meta_long["source"], "longitudinal")

    def test_schema_versioning(self) -> None:
        """Verifies ML_INPUT_SCHEMA_VERSION presence and consistency."""
        self.assertEqual(ML_INPUT_SCHEMA_VERSION, "3.1.0")
        ml_input = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
        )
        self.assertEqual(ml_input.schema_version, ML_INPUT_SCHEMA_VERSION)

    def test_feature_masking(self) -> None:
        """Verifies feature masking hides specified features from the active mask and imputed vector."""
        ml_input = self.assembler.assemble(
            text_features=self.text_feat,
            behavioural_features=self.beh_feat,
            engagement_features=self.eng_feat,
            longitudinal_features=self.long_feat,
            mask_feature_names=["text_fear", "text_word_count"],
        )

        idx_fear = FEATURE_NAME_TO_INDEX["text_fear"]
        idx_wc = FEATURE_NAME_TO_INDEX["text_word_count"]
        self.assertFalse(ml_input.feature_mask[idx_fear])
        self.assertFalse(ml_input.feature_mask[idx_wc])

        # Imputed vector should replace masked features with the imputed value
        imputed = ml_input.feature_vector(impute_missing=-999.0)
        self.assertEqual(imputed[idx_fear], -999.0)
        self.assertEqual(imputed[idx_wc], -999.0)

    def test_schema_validation_type_checks(self) -> None:
        """Verifies assembler rejects invalid feature container types with TypeError."""
        with self.assertRaises(TypeError):
            self.assembler.assemble(
                text_features="invalid_text",  # type: ignore[arg-type]
                behavioural_features=self.beh_feat,
                engagement_features=self.eng_feat,
                longitudinal_features=self.long_feat,
            )
        with self.assertRaises(TypeError):
            self.assembler.assemble(
                text_features=self.text_feat,
                behavioural_features={"invalid": "dict"},  # type: ignore[arg-type]
                engagement_features=self.eng_feat,
                longitudinal_features=self.long_feat,
            )
        with self.assertRaises(TypeError):
            self.assembler.assemble(
                text_features=self.text_feat,
                behavioural_features=self.beh_feat,
                engagement_features=self.eng_feat,
                longitudinal_features=self.long_feat,
                voice_features="invalid_voice",  # type: ignore[arg-type]
            )

    def test_invalid_feature_ranges(self) -> None:
        """Verifies range validation rejects out-of-bounds metrics with descriptive ValueError."""
        # Direct range validator check
        with self.assertRaises(ValueError) as ctx:
            validate_feature_value("text_fear", 1.5)
        self.assertIn("exceeds maximum allowed 1.0", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            validate_feature_value("text_word_count", -5.0)
        self.assertIn("is below minimum allowed 0.0", str(ctx.exception))

        # Assembler check when a feature object contains an invalid range
        bad_beh = BehaviouralFeatures(
            behavioural_available=True,
            safety_distress=2.5,  # Invalid: max allowed is 1.0
            sleep_disturbance=None,
            fear_intensity=None,
            low_social_support=None,
            help_requested=None,
            composite_distress=None,
            change_from_previous=None,
            change_from_baseline=None,
        )
        with self.assertRaises(ValueError):
            self.assembler.assemble(
                text_features=self.text_feat,
                behavioural_features=bad_beh,
                engagement_features=self.eng_feat,
                longitudinal_features=self.long_feat,
            )

    def test_batch_assembly(self) -> None:
        """Verifies batch assembly processing."""
        item = (self.text_feat, self.beh_feat, self.eng_feat, self.long_feat, None)
        batch = self.assembler.assemble_batch([item, item], case_ids=["C1", "C2"])
        self.assertEqual(len(batch), 2)
        self.assertEqual(batch[0].case_id, "C1")
        self.assertEqual(batch[1].case_id, "C2")

    def test_assemble_from_preprocessed_convenience(self) -> None:
        """Verifies end-to-end convenience method."""
        ml_input = self.assembler.assemble_from_preprocessed(self.preprocessed)
        self.assertEqual(ml_input.case_id, "CASE-301")
        self.assertEqual(ml_input.interaction_date, "2026-09-01")
        self.assertAlmostEqual(ml_input.get_feature("behavioural_fear_intensity"), 1.0)
        self.assertIsNotNone(ml_input.get_feature("text_word_count"))

        # Serialization check
        d = ml_input.to_dict()
        self.assertEqual(d["schema_version"], ML_INPUT_SCHEMA_VERSION)
        self.assertEqual(d["feature_count"], TOTAL_FEATURES_COUNT)
        self.assertEqual(len(d["feature_vector"]), TOTAL_FEATURES_COUNT)


if __name__ == "__main__":
    unittest.main()
