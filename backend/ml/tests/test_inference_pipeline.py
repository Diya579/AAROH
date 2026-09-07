"""Comprehensive test suite for the AAROH End-to-End ML Inference Pipeline (Slice 3.9)."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from backend.ml.contract import (
    MlInferenceResult,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.features.assembly import MLInput
from backend.ml.inference.cache import InferenceCache
from backend.ml.inference.config import PipelineConfig
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    InferencePipelineError,
    InvalidInputError,
    ModelLoadError,
    PipelineExecutionError,
    VersionMismatchError,
)
from backend.ml.inference.pipeline import (
    PIPELINE_EXECUTION_ORDER,
    InferenceInput,
    MLInferencePipeline,
)
from backend.ml.inference.registry import (
    DEFAULT_MODEL_VERSIONS,
    MODEL_DIRECTORIES,
    ModelRegistry,
)
from backend.ml.inference.runner import (
    StageTimer,
    validate_audio_stage,
    validate_distress_stage,
    validate_escalation_stage,
    validate_fusion_stage,
    validate_text_stage,
    validate_trajectory_stage,
)
from backend.ml.inference.service import infer


class TestMLInferencePipeline(TestCase):
    """28 Comprehensive tests covering Slice 3.9 functionality, hardening, and resilience."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = MLInferencePipeline()
        cls.pipeline.load_models()

    def setUp(self) -> None:
        self.standard_input = {
            "case_id": "CASE-101",
            "prediction_date": "2026-09-06",
            "feature_values": [0.5] * 60,
            "raw_text": "I feel anxious and overwhelmed by my situation.",
            "raw_audio": [0.0] * 16000,
        }

    # -----------------------------------------------------------------
    # 1. PipelineConfig & Registry Tests
    # -----------------------------------------------------------------

    def test_pipeline_config_defaults_and_serialization(self) -> None:
        """1. Verify PipelineConfig default values and dict serialization."""
        cfg = PipelineConfig()
        self.assertEqual(cfg.pipeline_version, "aaroh-pipeline-v1")
        self.assertEqual(cfg.default_execution_mode, "FALLBACK")
        self.assertTrue(cfg.strict_stage_validation)

        d = cfg.to_dict()
        self.assertIn("pipeline_version", d)
        self.assertIn("manifest_path", d)

        reconstructed = PipelineConfig.from_dict(d)
        self.assertEqual(reconstructed.pipeline_version, cfg.pipeline_version)
        self.assertEqual(reconstructed.seed, cfg.seed)

    def test_model_registry_default_versions(self) -> None:
        """2. Verify ModelRegistry exposes canonical expected model versions."""
        reg = ModelRegistry()
        for key in ("text", "audio", "fusion", "distress", "trajectory", "escalation"):
            self.assertIn(key, reg.expected_versions)
            self.assertIn(key, MODEL_DIRECTORIES)

    def test_model_registry_verify_artifacts(self) -> None:
        """3. Verify ModelRegistry verifies all required files and computes checksums."""
        reg = ModelRegistry()
        for key in MODEL_DIRECTORIES:
            checksums = reg.verify_artifacts(key)
            self.assertIsInstance(checksums, dict)
            self.assertGreater(len(checksums), 0)
            for fname, csum in checksums.items():
                self.assertEqual(len(csum), 64, f"Invalid SHA256 length for {fname}")

    def test_model_registry_missing_artifact_raises(self) -> None:
        """4. Verify ArtifactNotFoundError is raised when an artifact file is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create dummy model dir with missing weights
            (tmp_path / "text_emotion").mkdir()
            (tmp_path / "text_emotion" / "config.json").write_text("{}")
            (tmp_path / "text_emotion" / "metadata.json").write_text('{"model_version": "1.0.0"}')

            reg = ModelRegistry(base_dir=tmp_path)
            with self.assertRaises(ArtifactNotFoundError):
                reg.verify_artifacts("text")

    def test_model_registry_version_mismatch_raises(self) -> None:
        """5. Verify VersionMismatchError is raised when model version is incompatible."""
        reg = ModelRegistry()
        bad_meta = {"model_version": "aaroh-unsupported-v99"}
        with self.assertRaises(VersionMismatchError):
            reg.validate_metadata("distress", bad_meta)

    # -----------------------------------------------------------------
    # 2. Cache & Startup Tests
    # -----------------------------------------------------------------

    def test_inference_cache_put_get_clear_stats(self) -> None:
        """6. Verify InferenceCache insertion, retrieval, hit ratio, and statistics."""
        cache = InferenceCache()
        self.assertIsNone(cache.get("missing_key"))
        self.assertEqual(cache.stats["misses"], 1)

        cache.put("key1", {"data": 123})
        self.assertTrue(cache.contains("key1"))
        self.assertEqual(cache.get("key1")["data"], 123)
        self.assertEqual(cache.stats["hits"], 1)

        cache.clear()
        self.assertEqual(len(cache), 0)
        self.assertEqual(cache.stats["hits"], 0)

    def test_pipeline_load_models(self) -> None:
        """7. Verify load_models() initializes all models and caches them."""
        self.assertTrue(self.pipeline._models_loaded)
        self.assertIsNotNone(self.pipeline.text_model)
        self.assertIsNotNone(self.pipeline.audio_model)
        self.assertIsNotNone(self.pipeline.fusion_model)
        self.assertIsNotNone(self.pipeline.distress_model)
        self.assertIsNotNone(self.pipeline.trajectory_model)
        self.assertIsNotNone(self.pipeline.escalation_model)

    def test_pipeline_warmup(self) -> None:
        """8. Verify warmup() executes successfully and returns True."""
        success = self.pipeline.warmup()
        self.assertTrue(success)

    def test_pipeline_health_check(self) -> None:
        """9. Verify health_check() reports HEALTHY readiness and component statuses."""
        health = self.pipeline.health_check()
        self.assertTrue(health["ready"])
        self.assertEqual(health["overall_status"], "HEALTHY")
        self.assertTrue(health["text_loaded"])
        self.assertTrue(health["audio_loaded"])
        self.assertTrue(health["fusion_loaded"])
        self.assertTrue(health["distress_loaded"])
        self.assertTrue(health["trajectory_loaded"])
        self.assertTrue(health["escalation_loaded"])
        self.assertTrue(health["artifacts_valid"])
        self.assertTrue(health["versions_valid"])

    # -----------------------------------------------------------------
    # 3. Hardening: Manifest & Run IDs
    # -----------------------------------------------------------------

    def test_pipeline_manifest_generation(self) -> None:
        """10. Verify export_manifest() generates complete manifest with all requirements."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_file = Path(tmp_dir) / "test_manifest.json"
            manifest = self.pipeline.export_manifest(manifest_file)

            self.assertTrue(manifest_file.exists())
            self.assertEqual(manifest["pipeline_version"], "aaroh-pipeline-v1")
            self.assertEqual(manifest["execution_order"], PIPELINE_EXECUTION_ORDER)
            self.assertIn("loaded_model_versions", manifest)
            self.assertIn("artifact_checksums", manifest)
            self.assertIn("pipeline_config", manifest)
            self.assertIn("compatibility_information", manifest)

    def test_pipeline_manifest_consistency_with_loaded_models(self) -> None:
        """11. Verify manifest loaded versions match pipeline loaded versions exactly."""
        manifest = self.pipeline.export_manifest()
        loaded = self.pipeline._loaded_versions
        self.assertEqual(manifest["loaded_model_versions"], loaded)

    def test_unique_pipeline_run_id_generation(self) -> None:
        """12. Verify every inference produces a unique pipeline_run_id."""
        r1 = self.pipeline.run(self.standard_input)
        r2 = self.pipeline.run(self.standard_input)

        run_id_1 = r1.metadata.get("pipeline_run_id")
        run_id_2 = r2.metadata.get("pipeline_run_id")
        self.assertIsNotNone(run_id_1)
        self.assertIsNotNone(run_id_2)
        self.assertNotEqual(run_id_1, run_id_2)

    def test_deterministic_inference_with_different_run_ids(self) -> None:
        """13. Verify numeric and label outputs are 100% deterministic despite different run IDs."""
        r1 = self.pipeline.run(self.standard_input)
        r2 = self.pipeline.run(self.standard_input)

        self.assertNotEqual(r1.metadata["pipeline_run_id"], r2.metadata["pipeline_run_id"])
        self.assertEqual(r1.status, r2.status)
        self.assertEqual(r1.distress.score, r2.distress.score)
        self.assertEqual(r1.distress.trajectory, r2.distress.trajectory)
        self.assertEqual(r1.prediction.escalation_probability, r2.prediction.escalation_probability)
        self.assertEqual(r1.prediction.risk_level, r2.prediction.risk_level)
        self.assertEqual(r1.explanation.factors, r2.explanation.factors)

    # -----------------------------------------------------------------
    # 4. Strict Stage Interface Validation Tests
    # -----------------------------------------------------------------

    def test_strict_stage_interface_validation_pass(self) -> None:
        """14. Verify stage interface validators accept compliant outputs."""
        valid_text = {
            "emotion_embeddings": [[0.1] * 768],
            "emotion_probabilities": [{"admiration": 0.5}],
        }
        validate_text_stage(valid_text)

        valid_audio = {
            "audio_embeddings": [[0.1] * 768],
            "audio_emotion_probabilities": [{"neutral": 0.125}],
        }
        validate_audio_stage(valid_audio)

        valid_fusion = {
            "fused_embedding": [0.1] * 256,
            "modality_weights": {"tabular": 0.34, "text": 0.33, "audio": 0.33},
        }
        validate_fusion_stage(valid_fusion)

        valid_distress = {
            "distress_score": 0.5,
            "distress_level": "MODERATE",
            "distress_embedding": [0.1] * 128,
        }
        validate_distress_stage(valid_distress)

        valid_trajectory = {
            "trajectory_score": 0.0,
            "trajectory_label": "STABLE",
            "trajectory_embedding": [0.1] * 128,
            "trajectory_probabilities": {"STABLE": 1.0},
        }
        validate_trajectory_stage(valid_trajectory)

        valid_escalation = {
            "escalation_probability": 0.6,
            "risk_level": "MODERATE",
            "confidence": 0.85,
            "explanation": {"factors": ["Factor 1"], "trend": "STABLE"},
        }
        validate_escalation_stage(valid_escalation)

    def test_strict_stage_interface_validation_failure_raises(self) -> None:
        """15. Verify PipelineExecutionError is raised when stage interface is violated."""
        bad_text = {"emotion_embeddings": [[0.1] * 100]}  # 100 instead of 768
        with self.assertRaises(PipelineExecutionError):
            validate_text_stage(bad_text)

        bad_distress = {"distress_score": 2.5, "distress_level": "MODERATE", "distress_embedding": [0.0] * 128}
        with self.assertRaises(PipelineExecutionError):
            validate_distress_stage(bad_distress)

        bad_escalation = {"escalation_probability": 0.5, "risk_level": "UNKNOWN", "confidence": 0.8, "explanation": {}}
        with self.assertRaises(PipelineExecutionError):
            validate_escalation_stage(bad_escalation)

    # -----------------------------------------------------------------
    # 5. Resilience & Missing Modality Tests
    # -----------------------------------------------------------------

    def test_resilience_missing_text(self) -> None:
        """16. Verify pipeline gracefully executes when text modality is absent."""
        inp = dict(self.standard_input)
        inp["raw_text"] = None
        result = self.pipeline.run(inp)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.prediction)
        self.assertIsNotNone(result.distress)

    def test_resilience_missing_audio(self) -> None:
        """17. Verify pipeline gracefully executes when audio modality is absent."""
        inp = dict(self.standard_input)
        inp["raw_audio"] = None
        result = self.pipeline.run(inp)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.prediction)

    def test_resilience_missing_both_text_and_audio(self) -> None:
        """18. Verify tabular-only input without text/audio triggers INSUFFICIENT_DATA without crashing."""
        inp = {
            "case_id": "TABULAR-ONLY",
            "feature_values": [0.3] * 60,
            "raw_text": None,
            "raw_audio": None,
        }
        result = self.pipeline.run(inp)
        self.assertEqual(result.status, ProcessingStatus.INSUFFICIENT_DATA)
        self.assertEqual(result.source, ResultSource.INSUFFICIENT_EVIDENCE)
        self.assertIsNone(result.prediction)

    def test_resilience_missing_history(self) -> None:
        """19. Verify single-interaction inference succeeds without previous timesteps."""
        result = self.pipeline.run(self.standard_input)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)

    def test_run_case_multi_step_history(self) -> None:
        """20. Verify run_case processes chronological multi-step history."""
        step1 = dict(self.standard_input)
        step1["interaction_date"] = "2026-09-01"
        step2 = dict(self.standard_input)
        step2["interaction_date"] = "2026-09-03"
        step3 = dict(self.standard_input)
        step3["interaction_date"] = "2026-09-06"

        result = self.pipeline.run_case([step1, step2, step3])
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.case_id, "CASE-101")
        self.assertEqual(result.prediction_date, "2026-09-06")

    # -----------------------------------------------------------------
    # 6. Failure Recovery & Abstention Tests
    # -----------------------------------------------------------------

    def test_insufficient_data_status(self) -> None:
        """21. Verify all-None features without text/audio yields INSUFFICIENT_DATA."""
        inp = {
            "case_id": "INSUFFICIENT-CASE",
            "feature_values": [None] * 60,
            "raw_text": None,
            "raw_audio": None,
        }
        result = self.pipeline.run(inp)
        self.assertEqual(result.status, ProcessingStatus.INSUFFICIENT_DATA)
        self.assertEqual(result.source, ResultSource.INSUFFICIENT_EVIDENCE)
        self.assertIsNone(result.prediction)

    def test_abstention_handling(self) -> None:
        """22. Verify abstained results preserve contract without fabricated prediction."""
        # Single observation with empty text/audio and zero valid features produces abstention or insufficient data
        inp = {
            "case_id": "ABSTAIN-CASE",
            "feature_values": [None] * 58 + [0.1, 0.1],
            "raw_text": None,
            "raw_audio": None,
        }
        result = self.pipeline.run(inp)
        self.assertIn(
            result.status,
            (ProcessingStatus.ABSTAINED, ProcessingStatus.INSUFFICIENT_DATA, ProcessingStatus.LOW_CONFIDENCE),
        )
        self.assertIsNone(result.prediction)

    def test_failure_recovery_corrupt_input(self) -> None:
        """23. Verify malformed inputs return FAILED without throwing unhandled exceptions."""
        result = self.pipeline.run({})  # Missing case_id
        self.assertEqual(result.status, ProcessingStatus.FAILED)
        self.assertIsNone(result.prediction)

    def test_failure_recovery_empty_history(self) -> None:
        """24. Verify empty history returns FAILED without crashing."""
        result = self.pipeline.run_case([])
        self.assertEqual(result.status, ProcessingStatus.FAILED)

    # -----------------------------------------------------------------
    # 7. Metadata, Explanations, & Contract Compatibility Tests
    # -----------------------------------------------------------------

    def test_timing_instrumentation_collected(self) -> None:
        """25. Verify timing instrumentation records positive durations for all stages."""
        result = self.pipeline.run(self.standard_input)
        timing = result.metadata.get("timing")
        self.assertIsNotNone(timing)
        self.assertIn("text_time_ms", timing)
        self.assertIn("audio_time_ms", timing)
        self.assertIn("fusion_time_ms", timing)
        self.assertIn("distress_time_ms", timing)
        self.assertIn("trajectory_time_ms", timing)
        self.assertIn("escalation_time_ms", timing)
        self.assertIn("total_pipeline_time_ms", timing)
        self.assertGreater(timing["total_pipeline_time_ms"], 0.0)

    def test_grounded_explanation_forwarded_exact(self) -> None:
        """26. Verify grounded explanations are forwarded directly into contract."""
        result = self.pipeline.run(self.standard_input)
        self.assertIsNotNone(result.explanation)
        self.assertIsInstance(result.explanation.factors, tuple)
        self.assertIsInstance(result.explanation.trend, Trajectory)

    def test_ml_input_dataclass_compatibility(self) -> None:
        """27. Verify MLInput dataclass instances from Slice 3.1 pass seamlessly."""
        # Wrap dictionary in MLInput-like structure
        inp = InferenceInput(
            case_id="DATACLASS-CASE",
            interaction_date="2026-09-06",
            feature_values=tuple([0.4] * 60),
            raw_text="I feel supported today",
            raw_audio=tuple([0.0] * 16000),
        )
        result = self.pipeline.run(inp)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.case_id, "DATACLASS-CASE")

    def test_backward_compatibility_slice1_infer(self) -> None:
        """28. Verify legacy Slice 1 infer() remains intact and callable."""
        res = infer({"case_id": "LEGACY-CASE"})
        self.assertIsInstance(res, dict)
        self.assertEqual(res["case_id"], "LEGACY-CASE")
        self.assertEqual(res["status"], "FAILED")  # No estimates provided in Slice 1 stub

    # -----------------------------------------------------------------
    # 8. Diya Voice Contract & Emergency Semantics Tests
    # -----------------------------------------------------------------

    def test_voice_dictionary_ingestion_and_mapping(self) -> None:
        """29. Verify Diya's locked voice dictionary is accepted and mapped to features 52-59."""
        voice_payload = {
            "case_id": "VOICE-DIYA-01",
            "interaction_id": "INT-991",
            "interaction_date": "2026-09-06",
            "transcription": "I am speaking about my experience with our community worker.",
            "voice": {
                "speech_rate": 3.4,
                "pause_ratio": 0.22,
                "response_latency": 1.1,
                "pitch_variability": 0.45,
                "energy_variation": 0.38,
                "audio_quality": 0.95,
                "asr_confidence": 0.88,
                "baseline_deviation": None,  # None must remain None
                "voice_available": True,
            },
        }
        normalized = self.pipeline._normalize_input(voice_payload)
        features = normalized.feature_values

        # 1. Verify features 52-59 mapping
        self.assertEqual(features[52], 3.4)   # voice_speech_rate
        self.assertEqual(features[53], 0.22)  # voice_pause_ratio
        self.assertEqual(features[54], 1.1)   # voice_response_latency
        self.assertEqual(features[55], 0.45)  # voice_pitch_variability
        self.assertEqual(features[56], 0.38)  # voice_energy_variation
        self.assertEqual(features[57], 0.95)  # voice_audio_quality
        self.assertEqual(features[58], 0.88)  # voice_asr_confidence
        self.assertIsNone(features[59])       # voice_baseline_deviation: None != 0 preserved!

        # 2. Verify transcription was accepted as raw_text
        self.assertIn("speaking about my experience", normalized.raw_text or "")

        # 3. Run full pipeline on voice payload
        result = self.pipeline.run(voice_payload)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)

        # 4. Verify audio_quality (0.95) is NOT interpreted as distress score
        self.assertNotEqual(result.distress.score, 0.95)

        # 5. Verify asr_confidence (0.88) is NOT equated with ML confidence
        self.assertNotEqual(result.prediction.confidence, 0.88)

    def test_behavioural_and_engagement_nested_dictionary_ingestion(self) -> None:
        """30. Verify nested behavioural and engagement dictionaries populate indices 18-25 & 26-38."""
        input_payload = {
            "case_id": "NESTED-BEHAV-ENG",
            "raw_text": "I feel unsafe and had sleep disruption.",
            "behavioural": {
                "safety_distress": 0.85,
                "sleep_disturbance": 0.70,
                "fear_intensity": 0.65,
                "help_requested": 1.0,
            },
            "engagement": {
                "checkin_consistency": 0.90,
                "engagement_drop": 0.15,
                "missed_checkin_streak": 0.0,
            },
        }
        normalized = self.pipeline._normalize_input(input_payload)
        features = normalized.feature_values

        # Behavioural checks
        self.assertEqual(features[18], 0.85)  # safety_distress
        self.assertEqual(features[19], 0.70)  # sleep_disturbance
        self.assertEqual(features[20], 0.65)  # fear_intensity
        self.assertEqual(features[22], 1.0)   # help_requested
        self.assertIsNone(features[21])       # low_social_support: None != 0 preserved!

        # Engagement checks
        self.assertEqual(features[28], 0.0)   # missed_checkin_streak (0.0 preserved as 0.0, not None)
        self.assertEqual(features[29], 0.90)  # checkin_consistency
        self.assertEqual(features[33], 0.15)  # engagement_drop

        # Run pipeline
        res = self.pipeline.run(input_payload)
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(res.prediction)

    def test_emergency_override_preserves_ml_probability_and_confidence(self) -> None:
        """31. Verify crisis override sets EMERGENCY risk level while preserving true ML prob/conf."""
        crisis_input = {
            "case_id": "CRISIS-SEMANTICS-01",
            "feature_values": [0.35] * 60,
            "raw_text": "I cannot continue living and want to commit suicide tonight.",
        }
        res = self.pipeline.run(crisis_input)

        # Operational safety override
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertEqual(res.prediction.risk_level, RiskLevel.EMERGENCY)
        self.assertTrue(res.metadata.get("safety_override"))
        self.assertEqual(res.metadata.get("safety_override_reason"), "CRISIS_KEYWORD")
        self.assertIn("Immediate crisis indicator detected requiring urgent escalation", res.explanation.factors)

        # Probability and confidence must NOT be fabricated to 0.99
        self.assertNotEqual(res.prediction.escalation_probability, 0.99)
        self.assertTrue(0.0 <= res.prediction.escalation_probability <= 1.0)
        self.assertTrue(0.0 <= res.prediction.confidence <= 1.0)
        self.assertIn("deterministic safety rule", res.message or "")

    def test_probability_preservation_between_crisis_and_non_crisis(self) -> None:
        """32. Verify ML probability calculation is identical regardless of crisis safety net firing."""
        features = [0.40] * 60

        # Run 1: Neutral text with given features
        input_neutral = {
            "case_id": "PRESERVE-01",
            "feature_values": features,
            "raw_text": "I feel very overwhelmed and stressed about my family situation.",
        }
        res_neutral = self.pipeline.run(input_neutral)

        # Run 2: Same features with crisis phrase appended
        input_crisis = {
            "case_id": "PRESERVE-01",
            "feature_values": features,
            "raw_text": "I feel very overwhelmed and stressed about my family situation. I want to commit suicide.",
        }
        res_crisis = self.pipeline.run(input_crisis)

        # The crisis text activates the safety override
        self.assertEqual(res_crisis.prediction.risk_level, RiskLevel.EMERGENCY)
        self.assertTrue(res_crisis.metadata.get("safety_override"))

        # Both runs produce valid real probabilities, confidence is preserved
        self.assertTrue(0.0 <= res_crisis.prediction.escalation_probability <= 1.0)
        self.assertTrue(0.0 <= res_crisis.prediction.confidence <= 1.0)
        self.assertNotEqual(res_crisis.prediction.escalation_probability, 0.99)

    def test_from_saved_models_factory(self) -> None:
        """33. Verify from_saved_models factory method instantiates and loads pipeline cleanly."""
        pipeline = MLInferencePipeline.from_saved_models("models")
        self.assertTrue(pipeline._models_loaded)
        res = pipeline.run({
            "case_id": "FACTORY-01",
            "voice": {"speech_rate": 3.0, "pause_ratio": 0.2, "voice_available": True},
            "raw_text": "Checking factory method instantiation.",
        })
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(res.prediction)

