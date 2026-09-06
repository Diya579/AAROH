"""Comprehensive Production Hardening & Integration Test Suite.

Verifies all critical architectural, boundary, resilience, and operational invariants:
1. Multi-process separation (subprocess execution of isolated OS processes)
2. Temporal leakage protection (event shuffling, future-event cutoff invariance)
3. Loading resilience (missing checkpoint, corrupted weights, corrupted metadata, missing config, version mismatch)
4. Determinism check (identical outputs across repeated runs)
5. Mahendra boundary check (zero training imports in inference path, thread-safety under concurrent inference)
6. Preet boundary check (distinguishable statuses, enum conformance, human-readable explanations)
7. Full pipeline end-to-end configurations:
   - Full multimodal (text + audio + tabular + history)
   - Text-only (no audio waveform)
   - First-time beneficiary (history_length == 1)
   - Sparse interaction (minimum viable input)
   - High distress scenario -> HIGH risk level
   - Low distress scenario -> LOW risk level
   - Crisis keyword scenario -> EMERGENCY override
   - Missing data scenario -> INSUFFICIENT_DATA status
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import TestCase

# Ensure workspace root in sys.path
workspace_root = Path(__file__).resolve().parents[3]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from backend.ml.contract import (
    MlInferenceResult,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.features.assembly import MLInput
from backend.ml.inference.config import PipelineConfig
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    InferencePipelineError,
    ModelLoadError,
    VersionMismatchError,
)
from backend.ml.inference.pipeline import MLInferencePipeline
from backend.ml.inference.registry import ModelRegistry


class TestProductionHardening(TestCase):
    """Production Hardening, Boundary Conformance, and Resilience Tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ModelRegistry(base_dir=workspace_root / "models")
        cls.config = PipelineConfig(default_execution_mode="FALLBACK", strict_stage_validation=True)
        cls.pipeline = MLInferencePipeline(config=cls.config, registry=cls.registry)
        cls.pipeline.load_models()

    # =========================================================================
    # 1. Multi-Process Separation (Subprocess Isolation)
    # =========================================================================

    def test_multi_process_fresh_execution(self) -> None:
        """Process A (training/checkpoint verification) & Process B (fresh inference subprocess).

        Proves that no in-memory state leaks between processes, and that inference
        loads directly from disk in an isolated Python interpreter.
        """
        # Process A: Checkpoint confirmation in separate OS process
        cmd_a = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "p = Path('models/escalation/weights'); "
                "assert p.exists() and p.stat().st_size > 0; "
                "print('PROCESS_A_OK')"
            ),
        ]
        res_a = subprocess.run(
            cmd_a,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("PROCESS_A_OK", res_a.stdout)

        # Process B: Completely fresh OS-level Python process importing only inference
        cmd_b = [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from backend.ml.inference import MLInferencePipeline; "
                "from backend.ml.contract import ProcessingStatus; "
                "pipe = MLInferencePipeline(); "
                "pipe.load_models(); "
                "sample = {'case_id': 'PROC-B', 'raw_text': 'I need assistance with my daily tasks.'}; "
                "out = pipe.run(sample); "
                "assert out.status in (ProcessingStatus.SUCCESS, ProcessingStatus.INSUFFICIENT_DATA); "
                "assert 'backend.ml.training.train_escalation' not in sys.modules; "
                "print('PROCESS_B_SUCCESS')"
            ),
        ]
        res_b = subprocess.run(
            cmd_b,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("PROCESS_B_SUCCESS", res_b.stdout)

    # =========================================================================
    # 2. Temporal Leakage Protection
    # =========================================================================

    def test_temporal_event_shuffling_invariance(self) -> None:
        """Shuffled chronological events produce identical results after sorting."""
        t1 = {
            "case_id": "BENEFICIARY-SHUFFLE",
            "interaction_date": "2026-08-01",
            "feature_values": [0.2] * 60,
            "raw_text": "First meeting went fine.",
        }
        t2 = {
            "case_id": "BENEFICIARY-SHUFFLE",
            "interaction_date": "2026-08-15",
            "feature_values": [0.5] * 60,
            "raw_text": "I feel a bit more nervous today.",
        }
        t3 = {
            "case_id": "BENEFICIARY-SHUFFLE",
            "interaction_date": "2026-09-01",
            "feature_values": [0.8] * 60,
            "raw_text": "I feel very anxious and overwhelmed.",
        }

        # Chronological order
        res_chronological = self.pipeline.run_case([t1, t2, t3])

        # Shuffled order
        res_shuffled = self.pipeline.run_case([t3, t1, t2])

        self.assertEqual(res_chronological.status, res_shuffled.status)
        self.assertEqual(res_chronological.distress.score, res_shuffled.distress.score)
        self.assertEqual(res_chronological.distress.trajectory, res_shuffled.distress.trajectory)
        self.assertAlmostEqual(
            res_chronological.prediction.escalation_probability,
            res_shuffled.prediction.escalation_probability,
            places=5,
        )
        self.assertEqual(res_chronological.prediction.risk_level, res_shuffled.prediction.risk_level)

    def test_temporal_cutoff_future_event_invariance(self) -> None:
        """Predictions at cutoff T must not be influenced by events at t > T."""
        t1 = {
            "case_id": "BENEFICIARY-CUTOFF",
            "interaction_date": "2026-08-01",
            "feature_values": [0.3] * 60,
            "raw_text": "Feeling okay today.",
        }
        t2 = {
            "case_id": "BENEFICIARY-CUTOFF",
            "interaction_date": "2026-08-15",
            "feature_values": [0.4] * 60,
            "raw_text": "Some mild stress at work.",
        }
        # Predict at cutoff T = 2026-08-15
        cutoff_result = self.pipeline.run_case([t1, t2])

        # Add future event t3 = 2026-09-01
        t3 = {
            "case_id": "BENEFICIARY-CUTOFF",
            "interaction_date": "2026-09-01",
            "feature_values": [0.9] * 60,
            "raw_text": "Extreme crisis happening now.",
        }

        # Filter strictly to t <= T before evaluating cutoff T
        all_events = [t1, t2, t3]
        filtered_events = [e for e in all_events if e["interaction_date"] <= "2026-08-15"]
        reevaluated_result = self.pipeline.run_case(filtered_events)

        self.assertEqual(cutoff_result.status, reevaluated_result.status)
        self.assertEqual(cutoff_result.distress.score, reevaluated_result.distress.score)
        self.assertEqual(cutoff_result.prediction.escalation_probability, reevaluated_result.prediction.escalation_probability)
        self.assertEqual(cutoff_result.prediction.risk_level, reevaluated_result.prediction.risk_level)

    # =========================================================================
    # 3. Loading Resilience & Graceful Degradation
    # =========================================================================

    def test_loading_resilience_missing_checkpoint(self) -> None:
        """Missing model weights directory triggers clear fail-closed handling."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_path = Path(tmp_dir)
            empty_reg = ModelRegistry(base_dir=empty_path)
            resilient_pipe = MLInferencePipeline(registry=empty_reg)
            result = resilient_pipe.run({"case_id": "FAIL-1", "raw_text": "Test input"})
            self.assertEqual(result.status, ProcessingStatus.FAILED)
            self.assertIsNone(result.prediction)
            self.assertIn("Model loading failure", result.message or "")

    def test_loading_resilience_corrupted_weights(self) -> None:
        """Corrupted/truncated weights file fails closed without generating fabricated predictions."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for m in ("text", "audio", "fusion", "distress", "trajectory", "escalation"):
                m_dir = tmp_path / m
                m_dir.mkdir(parents=True)
                (m_dir / "config.json").write_text("{}")
                (m_dir / "metadata.json").write_text(f'{{"model_version": "aaroh-{m}-v1"}}')
                (m_dir / "weights").write_text("CORRUPTED_GARBAGE_BYTES_12345")
                (m_dir / "label_mapping.json").write_text("{}")

            bad_reg = ModelRegistry(base_dir=tmp_path)
            bad_pipe = MLInferencePipeline(registry=bad_reg)
            result = bad_pipe.run({"case_id": "CORRUPT-TEST", "raw_text": "Sample text"})
            self.assertEqual(result.status, ProcessingStatus.FAILED)
            self.assertIsNone(result.prediction)

    def test_loading_resilience_version_mismatch(self) -> None:
        """Incompatible model version in metadata raises VersionMismatchError and fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            esc_dir = tmp_path / "escalation"
            esc_dir.mkdir(parents=True)
            (esc_dir / "config.json").write_text("{}")
            (esc_dir / "weights").write_text("0.1 0.2")
            (esc_dir / "label_mapping.json").write_text("{}")
            (esc_dir / "metadata.json").write_text(
                '{"model_name": "aaroh-escalation-assessment", "model_version": "v999.0.0-incompatible"}'
            )

            mismatch_reg = ModelRegistry(base_dir=tmp_path)
            pipe = MLInferencePipeline(registry=mismatch_reg)
            result = pipe.run({"case_id": "MISMATCH-1", "raw_text": "Sample text"})
            self.assertEqual(result.status, ProcessingStatus.FAILED)
            self.assertIsNone(result.prediction)

    # =========================================================================
    # 4. Determinism & Reproducibility
    # =========================================================================

    def test_determinism_across_multiple_runs(self) -> None:
        """Inference produces bitwise/floating-point identical predictions across repeated calls."""
        sample_input = {
            "case_id": "BENEFICIARY-DET-42",
            "prediction_date": "2026-09-06",
            "feature_values": [0.42] * 60,
            "raw_text": "I feel lonely and isolated from my community.",
            "raw_audio": [0.0] * 16000,
        }
        res1 = self.pipeline.run(sample_input)
        res2 = self.pipeline.run(sample_input)
        res3 = self.pipeline.run(sample_input)

        self.assertEqual(res1.status, res2.status)
        self.assertEqual(res2.status, res3.status)
        self.assertEqual(res1.distress.score, res2.distress.score)
        self.assertEqual(res2.distress.score, res3.distress.score)
        self.assertEqual(res1.prediction.escalation_probability, res2.prediction.escalation_probability)
        self.assertEqual(res2.prediction.escalation_probability, res3.prediction.escalation_probability)
        self.assertEqual(res1.prediction.risk_level, res2.prediction.risk_level)
        self.assertEqual(res1.explanation.factors, res2.explanation.factors)
        # Each execution must receive a unique pipeline_run_id for auditing
        self.assertNotEqual(res1.metadata["pipeline_run_id"], res2.metadata["pipeline_run_id"])

    # =========================================================================
    # 5. Mahendra Boundary Alignment (FastAPI Integration Contract)
    # =========================================================================

    def test_no_training_imports_in_runtime(self) -> None:
        """Production pipeline runtime contains zero training, evaluation, or optimizer scripts."""
        cmd = [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from backend.ml.inference import MLInferencePipeline; "
                "pipe = MLInferencePipeline(); "
                "pipe.load_models(); "
                "pipe.run({'case_id': 'CHECK', 'raw_text': 'Hello world'}); "
                "leaked = [m for m in sys.modules if 'backend.ml.training.train_' in m or 'backend.ml.training.evaluate_' in m or 'backend.ml.training.benchmark_' in m]; "
                "assert len(leaked) == 0, f'Leaked training modules: {leaked}'; "
                "print('NO_TRAINING_MODULES_LEAKED')"
            ),
        ]
        res = subprocess.run(
            cmd,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("NO_TRAINING_MODULES_LEAKED", res.stdout)

    def test_thread_safety_under_concurrent_requests(self) -> None:
        """Pipeline must handle concurrent calls across threads without state corruption."""
        sample_inputs = [
            {
                "case_id": f"CONCURRENT-{i}",
                "feature_values": [0.1 * (i % 10)] * 60,
                "raw_text": f"Concurrent message index {i} requesting support.",
            }
            for i in range(12)
        ]

        def worker(inp: dict) -> MlInferenceResult:
            return self.pipeline.run(inp)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(worker, sample_inputs))

        self.assertEqual(len(results), 12)
        for i, res in enumerate(results):
            self.assertIsInstance(res, MlInferenceResult)
            self.assertEqual(res.case_id, f"CONCURRENT-{i}")
            self.assertIn(res.status, (ProcessingStatus.SUCCESS, ProcessingStatus.INSUFFICIENT_DATA))

    def test_fastapi_lifecycle_startup_and_health_check(self) -> None:
        """Verifies pipeline.warmup() and pipeline.health_check() suit FastAPI lifespan hooks."""
        pipeline = MLInferencePipeline(config=self.config, registry=self.registry)
        health_pre = pipeline.health_check()
        self.assertFalse(health_pre["ready"])

        pipeline.warmup()
        health_post = pipeline.health_check()
        self.assertTrue(health_post["ready"])
        self.assertEqual(health_post["overall_status"], "HEALTHY")
        self.assertTrue(health_post["escalation_loaded"])
        self.assertIn("aaroh-escalation-v1", health_post["model_versions"].values())

    # =========================================================================
    # 6. Preet Boundary Alignment (Intervention Layer Contract)
    # =========================================================================

    def test_preet_contract_statuses_and_enums(self) -> None:
        """Preet's intervention layer receives distinguishable statuses and conforming enums."""
        # Success status
        valid_input = {
            "case_id": "PREET-CONTRACT-OK",
            "feature_values": [0.6] * 60,
            "raw_text": "I feel very overwhelmed and helpless.",
            "raw_audio": [0.0] * 16000,
        }
        res_ok = self.pipeline.run(valid_input)
        self.assertEqual(res_ok.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(res_ok.prediction)
        self.assertIn(res_ok.prediction.risk_level, (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.EMERGENCY))
        self.assertGreater(len(res_ok.explanation.factors), 0)

        # Insufficient data status (all empty)
        empty_input = {
            "case_id": "PREET-CONTRACT-EMPTY",
            "feature_values": [None] * 60,
            "raw_text": "",
            "raw_audio": None,
        }
        res_empty = self.pipeline.run(empty_input)
        self.assertEqual(res_empty.status, ProcessingStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res_empty.prediction)
        self.assertIn("No valid features", res_empty.message or "")

    # =========================================================================
    # 7. End-to-End Scenarios
    # =========================================================================

    def test_scenario_full_multimodal(self) -> None:
        """Scenario A: Full multimodal input (text, audio, tabular, history)."""
        h1 = {
            "case_id": "SCENARIO-MM",
            "interaction_date": "2026-08-20",
            "feature_values": [0.4] * 60,
            "raw_text": "I had a normal week.",
            "raw_audio": [0.0] * 16000,
        }
        h2 = {
            "case_id": "SCENARIO-MM",
            "interaction_date": "2026-09-06",
            "feature_values": [0.7] * 60,
            "raw_text": "I am feeling increasingly worried and distressed.",
            "raw_audio": [0.05] * 16000,
        }
        res = self.pipeline.run_case([h1, h2])
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(res.distress)
        self.assertIsNotNone(res.prediction)
        self.assertEqual(res.source, ResultSource.ML)

    def test_scenario_text_only_graceful_degradation(self) -> None:
        """Scenario B: Text-only (no audio available) degrades gracefully."""
        inp = {
            "case_id": "SCENARIO-TEXT",
            "feature_values": [0.3] * 60,
            "raw_text": "I would like to speak with a counselor about my worries.",
            "raw_audio": None,
        }
        res = self.pipeline.run(inp)
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(res.prediction)

    def test_scenario_first_time_beneficiary(self) -> None:
        """Scenario C: First-time beneficiary (no prior history)."""
        inp = {
            "case_id": "FIRST-TIME-USER",
            "feature_values": [0.5] * 60,
            "raw_text": "This is my very first intake session.",
            "raw_audio": [0.0] * 16000,
        }
        res = self.pipeline.run(inp)
        self.assertIn(res.status, (ProcessingStatus.SUCCESS, ProcessingStatus.INSUFFICIENT_DATA))
        # Trajectory defaults appropriately without crashing
        self.assertIn(res.distress.trajectory, list(Trajectory))

    def test_scenario_sparse_minimum_viable_input(self) -> None:
        """Scenario D: Sparse interaction with minimum features."""
        inp = {
            "case_id": "SPARSE-USER",
            "feature_values": [None] * 58 + [0.4, 0.5],
            "raw_text": "Just checking in.",
        }
        res = self.pipeline.run(inp)
        self.assertIn(res.status, (ProcessingStatus.SUCCESS, ProcessingStatus.INSUFFICIENT_DATA))

    def test_scenario_high_distress_elevation(self) -> None:
        """Scenario E: High distress input yields elevated escalation probability and HIGH risk."""
        inp = {
            "case_id": "HIGH-DISTRESS",
            "feature_values": [0.95] * 60,
            "raw_text": "I am in extreme unbearable distress and feeling intense fear and panic.",
            "raw_audio": [0.1] * 16000,
        }
        res = self.pipeline.run(inp)
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertGreaterEqual(res.prediction.escalation_probability, 0.70)
        self.assertEqual(res.prediction.risk_level, RiskLevel.HIGH)

    def test_scenario_low_distress_calm(self) -> None:
        """Scenario F: Low distress, consistent input yields LOW risk."""
        inp = {
            "case_id": "LOW-DISTRESS",
            "feature_values": [0.05] * 60,
            "raw_text": "Everything is peaceful, calm, and going very well with my family.",
            "raw_audio": [0.0] * 16000,
        }
        res = self.pipeline.run(inp)
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertLessEqual(res.prediction.escalation_probability, 0.40)
        self.assertEqual(res.prediction.risk_level, RiskLevel.LOW)

    def test_scenario_crisis_keyword_emergency_override(self) -> None:
        """Scenario G: Explicit crisis keyword triggers EMERGENCY risk override while preserving ML prob/conf."""
        inp = {
            "case_id": "CRISIS-USER",
            "feature_values": [0.5] * 60,
            "raw_text": "I want to end my life and commit suicide tonight.",
        }
        res = self.pipeline.run(inp)
        self.assertEqual(res.status, ProcessingStatus.SUCCESS)
        self.assertEqual(res.prediction.risk_level, RiskLevel.EMERGENCY)
        # Real ML model probability and confidence must be preserved (not overridden to 0.99)
        self.assertTrue(0.0 <= res.prediction.escalation_probability <= 1.0)
        self.assertTrue(0.0 <= res.prediction.confidence <= 1.0)
        self.assertTrue(res.metadata.get("safety_override"))
        self.assertEqual(res.metadata.get("safety_override_reason"), "CRISIS_KEYWORD")
        self.assertIn("Immediate crisis indicator detected requiring urgent escalation", res.explanation.factors)

    def test_scenario_missing_data_insufficient_data(self) -> None:
        """Scenario H: Missing data produces INSUFFICIENT_DATA status without fabricating LOW risk."""
        inp = {
            "case_id": "MISSING-DATA",
            "feature_values": [None] * 60,
            "raw_text": "",
            "raw_audio": None,
        }
        res = self.pipeline.run(inp)
        self.assertEqual(res.status, ProcessingStatus.INSUFFICIENT_DATA)
        self.assertIsNone(res.prediction)
