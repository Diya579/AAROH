"""Regression Test Suite for ML Execution Mode Guards and Fail-Closed Semantics.

Verifies the 10 mandatory safety and compatibility requirements:
TEST 1: FALLBACK runtime + FALLBACK artifacts -> inference succeeds.
TEST 2: NEURAL runtime + FALLBACK artifacts -> hard failure (ExecutionModeError).
TEST 3: FALLBACK runtime + NEURAL artifacts -> hard failure (ExecutionModeError).
TEST 4: Explicit NEURAL mode + neural inference failure -> NeuralExecutionError (no silent fallback).
TEST 5: Explicit FALLBACK mode -> deterministic representation intentionally selected (neural not attempted).
TEST 6: Invalid execution mode/config value -> explicit validation failure (no inference).
TEST 7: Representation mismatch -> explicit failure before incompatible inference.
TEST 8: Normal existing production inference -> unchanged behavior.
TEST 9: Existing emergency/crisis safety override -> unchanged behavior.
TEST 10: Saved-model loading and existing artifact verification -> unchanged/pass.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from backend.ml.contract import (
    MlInferenceResult,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.features.assembly import MLInput
from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_NEURAL,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    VALID_EXECUTION_MODES,
    PipelineConfig,
    is_execution_mode_compatible,
)
from backend.ml.inference.exceptions import (
    ExecutionModeError,
    InferencePipelineError,
    ModelLoadError,
    NeuralExecutionError,
)
from backend.ml.inference.pipeline import InferenceInput, MLInferencePipeline
from backend.ml.inference.registry import MODEL_DIRECTORIES, ModelRegistry
from backend.ml.training.models.audio_emotion.model import AudioEmotionModel
from backend.ml.training.models.distress.model import DynamicDistressModel
from backend.ml.training.models.fusion.model import MultimodalFusionModel
from backend.ml.training.models.mental_health_language.model import MentalHealthLanguageModel
from backend.ml.training.models.stress.model import StressModel
from backend.ml.training.models.text_emotion.model import TextEmotionModel
from backend.ml.training.models.trajectory.model import LongitudinalTrajectoryModel


class TestExecutionModeGuards(TestCase):
    """Rigorous verification of fail-closed guards, mode compatibility, and regression safety."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.models_dir = Path(__file__).resolve().parents[3] / "models"

    def _create_sample_input(self, text: str = "I have been feeling very stressed and anxious lately.") -> dict:
        return {
            "case_id": "BENEFICIARY-GUARD-TEST",
            "prediction_date": "2026-09-06",
            "feature_values": [0.5] * 60,
            "raw_text": text,
            "raw_audio": [0.02 * ((i % 50) - 25) for i in range(16000)],
        }

    # -------------------------------------------------------------------------
    # TEST 1: FALLBACK runtime + FALLBACK artifacts -> inference succeeds
    # -------------------------------------------------------------------------
    def test_1_fallback_runtime_with_fallback_artifacts_succeeds(self) -> None:
        """TEST 1: FALLBACK runtime with FALLBACK disk artifacts successfully boots and infers."""
        pipeline = MLInferencePipeline(execution_mode=EXECUTION_MODE_FALLBACK)
        pipeline.load_models()

        sample_input = self._create_sample_input()
        result = pipeline.run(sample_input)

        self.assertIsInstance(result, MlInferenceResult)
        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.source, ResultSource.ML)
        self.assertIsNotNone(result.prediction)
        self.assertIsNotNone(result.distress)
        self.assertIsNotNone(result.explanation)
        self.assertIn(result.prediction.risk_level, (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.EMERGENCY))
        self.assertGreaterEqual(result.distress.score, 0.0)
        self.assertLessEqual(result.distress.score, 1.0)
        self.assertGreaterEqual(result.prediction.escalation_probability, 0.0)
        self.assertLessEqual(result.prediction.escalation_probability, 1.0)
        self.assertGreater(result.prediction.confidence, 0.0)
        self.assertTrue(len(result.explanation.factors) > 0)

    # -------------------------------------------------------------------------
    # TEST 2: NEURAL runtime + FALLBACK artifacts -> hard failure (ExecutionModeError)
    # -------------------------------------------------------------------------
    def test_2_neural_runtime_with_fallback_artifacts_hard_fails(self) -> None:
        """TEST 2: NEURAL runtime configured against production FALLBACK artifacts raises ExecutionModeError."""
        pipeline = MLInferencePipeline(execution_mode=EXECUTION_MODE_NEURAL)
        with self.assertRaises(ExecutionModeError) as ctx:
            pipeline.load_models()

        err_msg = str(ctx.exception).lower()
        self.assertTrue(
            "execution mode mismatch" in err_msg or "execution_mode mismatch" in err_msg,
            f"Error message should describe execution mode mismatch: {err_msg}",
        )
        self.assertIn("neural", err_msg)

    # -------------------------------------------------------------------------
    # TEST 3: FALLBACK runtime + NEURAL artifacts -> hard failure (ExecutionModeError)
    # -------------------------------------------------------------------------
    def test_3_fallback_runtime_with_neural_artifacts_hard_fails(self) -> None:
        """TEST 3: FALLBACK runtime configured against NEURAL artifacts raises ExecutionModeError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_models = Path(temp_dir) / "models"
            # Copy existing artifacts
            shutil.copytree(self.models_dir, temp_models)

            # Mutate text model metadata to specify NEURAL mode
            text_meta_path = temp_models / "text_emotion" / "metadata.json"
            with open(text_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["execution_mode"] = EXECUTION_MODE_NEURAL
            meta["training_representation"] = "distilbert-base-multilingual-cased"
            with open(text_meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            # Initialize pipeline pointing to mutated artifacts with FALLBACK runtime
            reg = ModelRegistry(models_dir=temp_models)
            cfg = PipelineConfig(manifest_path=str(temp_models / "pipeline_manifest.json"), execution_mode=EXECUTION_MODE_FALLBACK)
            pipeline = MLInferencePipeline(config=cfg, registry=reg)

            with self.assertRaises(ExecutionModeError) as ctx:
                pipeline.load_models()

            err_msg = str(ctx.exception).lower()
            self.assertTrue(
                "execution mode mismatch" in err_msg or "execution_mode mismatch" in err_msg,
                f"Error message should describe execution mode mismatch: {err_msg}",
            )
            self.assertIn("neural", err_msg)

    # -------------------------------------------------------------------------
    # TEST 4: Explicit NEURAL mode + neural inference failure -> NeuralExecutionError
    # -------------------------------------------------------------------------
    def test_4_neural_inference_failure_fails_closed_no_fallback(self) -> None:
        """TEST 4: In NEURAL mode, neural failure raises NeuralExecutionError and NEVER returns fallback."""
        # 1. TextEmotionModel under NEURAL mode
        text_model = TextEmotionModel(execution_mode=EXECUTION_MODE_NEURAL)

        # Case A: When torch_model is None (e.g. PyTorch not installed or weights not loaded)
        text_model.torch_model = None
        with self.assertRaises(NeuralExecutionError) as ctx_a:
            text_model.encode_and_predict(["Sample test sentence."])
        self.assertTrue("torch_model is not initialized" in str(ctx_a.exception) or "not installed" in str(ctx_a.exception))

        # Case B: When torch_model raises a runtime failure (e.g. forward pass CUDA / device crash)
        mock_torch = MagicMock()
        mock_torch.tensor.side_effect = RuntimeError("Simulated neural layer hardware failure")
        mock_torch.no_grad.return_value = MagicMock()
        mock_transformers = MagicMock()

        with patch.dict("sys.modules", {"torch": mock_torch, "transformers": mock_transformers}):
            text_model.torch_model = MagicMock(side_effect=RuntimeError("Simulated neural layer hardware failure"))
            text_model.tokenizer = MagicMock()
            with self.assertRaises(NeuralExecutionError) as ctx_b:
                text_model.encode_and_predict(["Sample test sentence."])
            self.assertIn("Neural inference failed", str(ctx_b.exception))

        # 2. AudioEmotionModel under NEURAL mode
        audio_model = AudioEmotionModel(execution_mode=EXECUTION_MODE_NEURAL)
        audio_model.torch_model = None
        dummy_waveform = [0.01 * i for i in range(16000)]
        with self.assertRaises(NeuralExecutionError) as ctx_c:
            audio_model.encode_and_predict([dummy_waveform])
        self.assertTrue("torch_model is not initialized" in str(ctx_c.exception) or "not installed" in str(ctx_c.exception))

        # Case C: Audio model runtime failure
        mock_audio_torch = MagicMock()
        mock_audio_torch.tensor.side_effect = RuntimeError("Simulated wav2vec2 failure")
        mock_audio_torch.no_grad.return_value = MagicMock()

        with patch.dict("sys.modules", {"torch": mock_audio_torch, "transformers": mock_transformers}):
            audio_model.torch_model = MagicMock()
            with self.assertRaises(NeuralExecutionError) as ctx_d:
                audio_model.encode_and_predict([dummy_waveform])
            self.assertIn("Neural inference failed", str(ctx_d.exception))

    # -------------------------------------------------------------------------
    # TEST 5: Explicit FALLBACK mode -> deterministic representation intentionally selected
    # -------------------------------------------------------------------------
    def test_5_explicit_fallback_mode_selects_deterministic_no_neural(self) -> None:
        """TEST 5: Explicit FALLBACK mode intentionally executes deterministic logic without neural backbones."""
        text_model = TextEmotionModel(execution_mode=EXECUTION_MODE_FALLBACK)
        self.assertIsNone(text_model.torch_model)

        audio_model = AudioEmotionModel(execution_mode=EXECUTION_MODE_FALLBACK)
        self.assertIsNone(audio_model.torch_model)

        # Verify deterministic outputs are generated cleanly
        sample_texts = ["मुझे बहुत चिंता हो रही है", "I feel hopeless"]
        res_text = text_model.encode_and_predict(sample_texts)
        self.assertEqual(len(res_text["emotion_probabilities"]), 2)
        self.assertEqual(len(res_text["emotion_embeddings"]), 2)
        self.assertEqual(len(res_text["emotion_embeddings"][0]), 768)

        # Verify repeatability (mathematical determinism)
        res_text_repeat = text_model.encode_and_predict(sample_texts)
        self.assertEqual(res_text["emotion_embeddings"], res_text_repeat["emotion_embeddings"])

    # -------------------------------------------------------------------------
    # TEST 6: Invalid execution mode/config value -> explicit validation failure
    # -------------------------------------------------------------------------
    def test_6_invalid_execution_mode_config_validation_failure(self) -> None:
        """TEST 6: Invalid execution mode values are rejected with ExecutionModeError across all entry points."""
        invalid_modes = ["FALBACK", "fallback", "neural-ish", "", None, "pytorch", "UNKNOWN"]

        for invalid in invalid_modes:
            # PipelineConfig validation
            with self.assertRaises(ExecutionModeError):
                PipelineConfig(execution_mode=invalid)  # type: ignore

            # MLInferencePipeline validation
            with self.assertRaises(ExecutionModeError):
                MLInferencePipeline(execution_mode=invalid)  # type: ignore

            # Model representations validation
            if invalid is not None:
                with self.assertRaises(ExecutionModeError):
                    TextEmotionModel(execution_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    AudioEmotionModel(execution_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    StressModel(execution_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    MentalHealthLanguageModel(execution_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    MultimodalFusionModel(force_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    DynamicDistressModel(force_mode=invalid)

                with self.assertRaises(ExecutionModeError):
                    LongitudinalTrajectoryModel(force_mode=invalid)

    # -------------------------------------------------------------------------
    # TEST 7: Representation mismatch -> explicit failure before incompatible inference
    # -------------------------------------------------------------------------
    def test_7_representation_mismatch_fails_closed(self) -> None:
        """TEST 7: ModelRegistry.validate_metadata detects representation and mode mismatches fail-closed."""
        registry = ModelRegistry()

        # Valid FALLBACK metadata passes
        valid_meta = {
            "model_version": "1.0.0",
            "execution_mode": "FALLBACK",
            "training_representation": "deterministic_hash",
        }
        registry.validate_metadata("text", valid_meta, execution_mode="FALLBACK")

        # Incompatible training representation in metadata under FALLBACK runtime
        incompatible_rep_meta = {
            "model_version": "1.0.0",
            "execution_mode": "FALLBACK",
            "training_representation": "neural_distilbert_transformer",
        }
        with self.assertRaises(ExecutionModeError) as ctx1:
            registry.validate_metadata("text", incompatible_rep_meta, execution_mode="FALLBACK")
        self.assertIn("representation mismatch", str(ctx1.exception).lower())

        # Incompatible execution mode in metadata
        mode_mismatch_meta = {
            "model_version": "1.0.0",
            "execution_mode": "NEURAL",
            "training_representation": "neural_backbone",
        }
        with self.assertRaises(ExecutionModeError) as ctx2:
            registry.validate_metadata("text", mode_mismatch_meta, execution_mode="FALLBACK")
        self.assertIn("execution mode mismatch", str(ctx2.exception).lower())

    # -------------------------------------------------------------------------
    # TEST 8: Normal existing production inference -> unchanged behavior
    # -------------------------------------------------------------------------
    def test_8_normal_production_inference_unchanged(self) -> None:
        """TEST 8: Production inference yields exact expected contract, scores, and explanations."""
        pipeline = MLInferencePipeline()
        pipeline.load_models()

        sample_input = self._create_sample_input("I am feeling moderately overwhelmed with work.")
        result = pipeline.run(sample_input)

        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.source, ResultSource.ML)
        self.assertIsNotNone(result.distress)
        self.assertIsNotNone(result.prediction)
        self.assertIsNotNone(result.explanation)
        self.assertIsInstance(result.distress.score, float)
        self.assertIsInstance(result.distress.trajectory, Trajectory)
        self.assertIsInstance(result.prediction.risk_level, RiskLevel)
        self.assertIsInstance(result.prediction.confidence, float)
        self.assertIsInstance(result.explanation.factors, tuple)
        self.assertGreater(len(result.explanation.factors), 0)
        self.assertEqual(result.metadata["execution_mode"], "FALLBACK")

    # -------------------------------------------------------------------------
    # TEST 9: Existing emergency/crisis safety override -> unchanged behavior
    # -------------------------------------------------------------------------
    def test_9_emergency_crisis_safety_override_unchanged(self) -> None:
        """TEST 9: Crisis keywords trigger EMERGENCY safety override with preserved authentic ML metadata."""
        pipeline = MLInferencePipeline()
        pipeline.load_models()

        crisis_input = self._create_sample_input("I want to end my life, I cannot take this pain anymore.")
        result = pipeline.run(crisis_input)

        self.assertEqual(result.status, ProcessingStatus.SUCCESS)
        self.assertEqual(result.source, ResultSource.ML)
        self.assertIsNotNone(result.prediction)
        self.assertEqual(result.prediction.risk_level, RiskLevel.EMERGENCY)
        self.assertIsNotNone(result.distress)
        self.assertGreaterEqual(result.distress.score, 0.0)
        self.assertLessEqual(result.distress.score, 1.0)
        self.assertIn("immediate crisis", result.explanation.factors[0].lower())

        # Verify safety_override metadata preserves authentic ML evaluation
        self.assertTrue(result.metadata.get("safety_override"))
        self.assertEqual(result.metadata.get("safety_override_reason"), "CRISIS_KEYWORD")
        self.assertGreaterEqual(result.prediction.escalation_probability, 0.0)
        self.assertGreaterEqual(result.prediction.confidence, 0.0)

    # -------------------------------------------------------------------------
    # TEST 10: Saved-model loading and existing artifact verification -> pass
    # -------------------------------------------------------------------------
    def test_10_saved_model_loading_and_existing_artifact_verification(self) -> None:
        """TEST 10: Model artifacts on disk pass integrity verification and health checks."""
        pipeline = MLInferencePipeline()
        pipeline.load_models()

        # All 6 required models verified
        for key in MODEL_DIRECTORIES:
            pipeline.registry.verify_artifacts(key)

        health = pipeline.health_check()
        self.assertEqual(health["overall_status"], "HEALTHY")
        self.assertTrue(health["ready"])

        manifest = pipeline.manifest
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["execution_mode"], "FALLBACK")
        self.assertEqual(manifest["pipeline_version"], "aaroh-pipeline-v1")

    # -------------------------------------------------------------------------
    # TEST 11: Manifest corruption or read failure fails closed (ModelLoadError)
    # -------------------------------------------------------------------------
    def test_11_manifest_corruption_or_read_failure_fails_closed(self) -> None:
        """TEST 11: Corrupted or unreadable pipeline_manifest.json fails closed and prevents inference."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_models = Path(temp_dir) / "models"
            shutil.copytree(self.models_dir, temp_models)

            # Case A: Corrupted JSON in pipeline_manifest.json
            manifest_path = temp_models / "pipeline_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write('{"execution_mode": "FALLBACK", "corrupted_syntax: }')

            reg = ModelRegistry(models_dir=temp_models)
            cfg = PipelineConfig(manifest_path=str(manifest_path), execution_mode=EXECUTION_MODE_FALLBACK)
            pipeline = MLInferencePipeline(config=cfg, registry=reg)

            with self.assertRaises(ModelLoadError) as ctx_a:
                pipeline.load_models()
            self.assertIn("Failed to read or parse pipeline manifest", str(ctx_a.exception))

            # Case B: Read error (OSError) on pipeline_manifest.json
            with patch("builtins.open", side_effect=OSError("Simulated I/O failure on manifest")):
                pipeline_b = MLInferencePipeline(config=cfg, registry=reg)
                with self.assertRaises(ModelLoadError) as ctx_b:
                    pipeline_b.load_models()
                self.assertIn("Failed to read or parse pipeline manifest", str(ctx_b.exception))

            # Case C: Missing manifest is handled gracefully without crash
            manifest_path.unlink()
            pipeline_c = MLInferencePipeline(config=cfg, registry=reg)
            pipeline_c.load_models()
            self.assertTrue(pipeline_c._models_loaded)

    # -------------------------------------------------------------------------
    # TEST 12: Full execution mode compatibility matrix
    # -------------------------------------------------------------------------
    def test_12_execution_mode_compatibility_matrix(self) -> None:
        """TEST 12: Rigorously verifies all combinations of runtime mode and artifact mode."""
        registry = ModelRegistry()

        # Expected compatibility matrix: (runtime_mode, artifact_mode) -> expected_compatible (bool)
        compatibility_matrix = {
            # 1. Exact matches (All ALLOW)
            (EXECUTION_MODE_FALLBACK, EXECUTION_MODE_FALLBACK): True,
            (EXECUTION_MODE_NEURAL, EXECUTION_MODE_NEURAL): True,
            (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_PYTORCH_FROZEN): True,
            (EXECUTION_MODE_PYTORCH_FINETUNE, EXECUTION_MODE_PYTORCH_FINETUNE): True,

            # 2. Fallback vs Neural cross-modes (All FAIL)
            (EXECUTION_MODE_FALLBACK, EXECUTION_MODE_NEURAL): False,
            (EXECUTION_MODE_NEURAL, EXECUTION_MODE_FALLBACK): False,
            (EXECUTION_MODE_FALLBACK, EXECUTION_MODE_PYTORCH_FROZEN): False,
            (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_FALLBACK): False,
            (EXECUTION_MODE_FALLBACK, EXECUTION_MODE_PYTORCH_FINETUNE): False,
            (EXECUTION_MODE_PYTORCH_FINETUNE, EXECUTION_MODE_FALLBACK): False,

            # 3. Cross-neural modes
            (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_PYTORCH_FINETUNE): False,  # Frozen cannot run finetuned
            (EXECUTION_MODE_PYTORCH_FINETUNE, EXECUTION_MODE_PYTORCH_FROZEN): False,  # Finetuned requires finetuned
            (EXECUTION_MODE_NEURAL, EXECUTION_MODE_PYTORCH_FROZEN): True,             # Umbrella neural accepts frozen
            (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_NEURAL): True,             # Frozen accepts generic neural
            (EXECUTION_MODE_NEURAL, EXECUTION_MODE_PYTORCH_FINETUNE): True,           # Umbrella neural accepts finetuned
            (EXECUTION_MODE_PYTORCH_FINETUNE, EXECUTION_MODE_NEURAL): False,          # Finetuned requires finetuned
        }

        for (runtime_mode, artifact_mode), expected_allowed in compatibility_matrix.items():
            # Verify standalone compatibility helper
            is_compat = is_execution_mode_compatible(runtime_mode, artifact_mode)
            self.assertEqual(
                is_compat,
                expected_allowed,
                f"Compatibility mismatch for ({runtime_mode}, {artifact_mode}): expected {expected_allowed}, got {is_compat}",
            )

            # Verify ModelRegistry.validate_metadata enforcement
            dummy_meta = {"model_version": "1.0.0", "execution_mode": artifact_mode}
            if expected_allowed:
                try:
                    registry.validate_metadata("text", dummy_meta, execution_mode=runtime_mode)
                except ExecutionModeError as e:
                    self.fail(f"Expected ALLOW for ({runtime_mode}, {artifact_mode}), but raised: {e}")
            else:
                with self.assertRaises(ExecutionModeError, msg=f"Expected FAIL for ({runtime_mode}, {artifact_mode})"):
                    registry.validate_metadata("text", dummy_meta, execution_mode=runtime_mode)
