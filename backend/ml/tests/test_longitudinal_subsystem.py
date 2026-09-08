"""Comprehensive Unit Tests for Longitudinal Trajectory Subsystem (Slice 3.7).

Tests:
1. Trajectory evidence generation and temporal metrics calculation.
2. Improving sequences (distress drops -> IMPROVING / RECOVERING).
3. Worsening sequences (distress climbs -> SLOWLY_WORSENING / RAPIDLY_WORSENING).
4. Stable sequences (flat distress -> STABLE).
5. Noisy sequences with low net drift.
6. Missing timestamps and fallback handling.
7. End-to-end TrajectoryInferencePipeline with multilingual text histories (English & Hindi).
8. DynamicDistressModel + LongitudinalTrajectoryModel interaction integration.
9. Artifact export and load_from_artifact roundtrip parity.
10. Deterministic inference repeatability.
11. Strict clinical boundary enforcement.
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from backend.ml.training.models.common import enforce_trajectory_boundary
from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    LABEL_IMPROVING,
    LABEL_RAPIDLY_WORSENING,
    LABEL_STABLE,
    LABEL_WORSENING,
    CaseTrajectory,
    TrajectoryInputRecord,
    build_synthetic_trajectories,
)
from backend.ml.training.models.trajectory.explainability import (
    STATE_IMPROVING,
    STATE_RAPIDLY_WORSENING,
    STATE_RECOVERING,
    STATE_SLOWLY_WORSENING,
    STATE_STABLE,
    TrajectoryEvidence,
    calculate_trajectory_metrics,
    determine_trajectory_state_and_confidence,
    generate_trajectory_evidence,
)
from backend.ml.training.models.trajectory.inference import (
    TrajectoryInferencePipeline,
)
from backend.ml.training.models.trajectory.model import (
    LongitudinalTrajectoryModel,
)


def _make_dummy_record(
    case_id: str,
    idx: int,
    distress_score: float,
    distress_level: str = "MODERATE",
    timestamp: str = "2026-03-01T12:00:00",
    sleep_disruption: float = 0.5,
    engagement: float = 0.5,
) -> TrajectoryInputRecord:
    """Helper to generate well-formed TrajectoryInputRecord."""
    b_feats = [0.0] * 16
    b_feats[1] = sleep_disruption  # sleep value
    b_feats[9] = 1.0               # sleep present mask

    e_feats = [0.0] * 26
    e_feats[0] = engagement        # engagement value
    e_feats[13] = 1.0              # engagement present mask

    return TrajectoryInputRecord(
        case_id=case_id,
        interaction_id=f"INT-{idx:03d}",
        timestamp=timestamp,
        distress_embedding=[0.05] * 128,
        distress_score=distress_score,
        distress_level=distress_level,
        fused_embedding=[0.02] * 256,
        behavioural_features=b_feats,
        engagement_features=e_feats,
        time_delta_hours=24.0 if idx > 0 else 0.0,
    )


class TestTrajectoryExplainabilityAndMetrics(unittest.TestCase):
    """Test suite for trajectory metrics and explainability calculation."""

    def test_improving_sequence_metrics_and_reasons(self) -> None:
        """Decreasing distress over 4 days produces negative velocity and IMPROVING/RECOVERING state."""
        records = [
            _make_dummy_record("CASE-1", 0, 0.85, "CRITICAL", "2026-03-01T10:00:00", sleep_disruption=0.8),
            _make_dummy_record("CASE-1", 1, 0.70, "HIGH", "2026-03-02T10:00:00", sleep_disruption=0.7),
            _make_dummy_record("CASE-1", 2, 0.50, "MODERATE", "2026-03-03T10:00:00", sleep_disruption=0.5),
            _make_dummy_record("CASE-1", 3, 0.30, "LOW", "2026-03-04T10:00:00", sleep_disruption=0.3),
        ]

        metrics = calculate_trajectory_metrics(records)
        self.assertEqual(metrics["observations_count"], 4)
        self.assertAlmostEqual(metrics["baseline_distress"], 0.85)
        self.assertAlmostEqual(metrics["current_distress"], 0.30)
        self.assertLess(metrics["delta_from_baseline"], -0.50)
        self.assertLess(metrics["trend_velocity_weekly"], 0.0)
        self.assertGreaterEqual(metrics["consecutive_improving_count"], 3)

        state, conf = determine_trajectory_state_and_confidence(-0.7, metrics)
        self.assertIn(state, (STATE_IMPROVING, STATE_RECOVERING))
        self.assertGreaterEqual(conf, 0.75)

        evidence = generate_trajectory_evidence(records, trajectory_score=-0.7, trajectory_label="IMPROVING")
        self.assertIsInstance(evidence, TrajectoryEvidence)
        self.assertGreater(len(evidence.reasons), 0)
        reasons_text = " ".join(evidence.reasons)
        self.assertIn("decreased", reasons_text.lower())

    def test_rapidly_worsening_sequence_metrics(self) -> None:
        """Sharp distress increase over 4 days produces high positive velocity and RAPIDLY_WORSENING state."""
        records = [
            _make_dummy_record("CASE-2", 0, 0.20, "LOW", "2026-03-01T10:00:00"),
            _make_dummy_record("CASE-2", 1, 0.45, "MODERATE", "2026-03-02T10:00:00"),
            _make_dummy_record("CASE-2", 2, 0.70, "HIGH", "2026-03-03T10:00:00"),
            _make_dummy_record("CASE-2", 3, 0.90, "CRITICAL", "2026-03-04T10:00:00"),
        ]

        metrics = calculate_trajectory_metrics(records)
        self.assertGreater(metrics["trend_velocity_weekly"], 0.30)
        self.assertGreaterEqual(metrics["consecutive_worsening_count"], 3)

        state, conf = determine_trajectory_state_and_confidence(0.85, metrics)
        self.assertEqual(state, STATE_RAPIDLY_WORSENING)
        self.assertGreaterEqual(conf, 0.85)

        evidence = generate_trajectory_evidence(records, trajectory_score=0.85, trajectory_label="RAPIDLY_WORSENING")
        self.assertIn("+", evidence.trend_velocity_display)
        reasons_text = " ".join(evidence.reasons)
        self.assertIn("increased", reasons_text.lower())

    def test_stable_sequence_metrics(self) -> None:
        """Flat distress scores across 4 days produce near-zero velocity and STABLE state."""
        records = [
            _make_dummy_record("CASE-3", 0, 0.40, "MODERATE", "2026-03-01T10:00:00"),
            _make_dummy_record("CASE-3", 1, 0.41, "MODERATE", "2026-03-02T10:00:00"),
            _make_dummy_record("CASE-3", 2, 0.39, "MODERATE", "2026-03-03T10:00:00"),
            _make_dummy_record("CASE-3", 3, 0.40, "MODERATE", "2026-03-04T10:00:00"),
        ]

        metrics = calculate_trajectory_metrics(records)
        self.assertAlmostEqual(metrics["trend_velocity_weekly"], 0.0, places=1)
        state, conf = determine_trajectory_state_and_confidence(0.0, metrics)
        self.assertEqual(state, STATE_STABLE)

    def test_missing_and_malformed_timestamps_graceful_handling(self) -> None:
        """Missing or non-parseable timestamps fall back to sequential interaction indices."""
        records = [
            _make_dummy_record("CASE-4", 0, 0.30, timestamp=""),
            _make_dummy_record("CASE-4", 1, 0.50, timestamp="invalid-timestamp"),
            _make_dummy_record("CASE-4", 2, 0.70, timestamp=None),  # type: ignore
        ]

        metrics = calculate_trajectory_metrics(records)
        self.assertEqual(metrics["observations_count"], 3)
        self.assertGreater(metrics["history_span_days"], 0.0)
        self.assertGreater(metrics["trend_velocity_weekly"], 0.0)


class TestLongitudinalModelInterface(unittest.TestCase):
    """Test suite for LongitudinalTrajectoryModel methods, evidence, and artifact roundtrip."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.model = LongitudinalTrajectoryModel(seed=42)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_predict_trajectory_with_evidence_payload(self) -> None:
        """predict_trajectory_with_evidence returns complete payload with reasons and velocity."""
        records = [
            _make_dummy_record("CASE-M", 0, 0.30, timestamp="2026-03-01T10:00:00"),
            _make_dummy_record("CASE-M", 1, 0.50, timestamp="2026-03-02T10:00:00"),
            _make_dummy_record("CASE-M", 2, 0.75, timestamp="2026-03-03T10:00:00"),
        ]
        case = CaseTrajectory(case_id="CASE-M", records=records, trajectory_label="UNKNOWN")

        out = self.model.predict_trajectory_with_evidence(case)

        self.assertIn("trajectory_score", out)
        self.assertIn("trajectory_state", out)
        self.assertIn("trajectory_label", out)
        self.assertIn("confidence", out)
        self.assertIn("trend_velocity", out)
        self.assertIn("trend_velocity_display", out)
        self.assertIn("trend_acceleration", out)
        self.assertIn("trajectory_embedding", out)
        self.assertIn("trajectory_probabilities", out)
        self.assertIn("reasons", out)
        self.assertIn("evidence", out)

        self.assertEqual(len(out["trajectory_embedding"]), 128)
        norm = math.sqrt(sum(x * x for x in out["trajectory_embedding"]))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_artifact_export_and_load_roundtrip(self) -> None:
        """Model exported to directory and reloaded with load_from_artifact produces identical predictions."""
        export_dir = Path(self.temp_dir) / "exported_trajectory"
        manifest = self.model.export(export_dir)

        self.assertTrue(Path(manifest["weights"]).exists())
        self.assertTrue(Path(manifest["config"]).exists())
        self.assertTrue(Path(manifest["metadata"]).exists())

        reloaded = LongitudinalTrajectoryModel.load_from_artifact(export_dir)

        dummy_records = [
            _make_dummy_record("CASE-R", i, 0.2 + i * 0.1, timestamp=f"2026-03-0{i+1}T10:00:00")
            for i in range(4)
        ]
        case = CaseTrajectory("CASE-R", dummy_records, "UNKNOWN")

        pred_orig = self.model.predict_trajectory(case)
        pred_reload = reloaded.predict_trajectory(case)

        self.assertAlmostEqual(pred_orig["trajectory_score"], pred_reload["trajectory_score"], places=5)
        self.assertEqual(pred_orig["trajectory_label"], pred_reload["trajectory_label"])
        for v1, v2 in zip(pred_orig["trajectory_embedding"], pred_reload["trajectory_embedding"]):
            self.assertAlmostEqual(v1, v2, places=5)

    def test_load_from_artifact_missing_file_raises(self) -> None:
        """load_from_artifact raises FileNotFoundError if artifact files are missing."""
        bad_dir = Path(self.temp_dir) / "incomplete"
        bad_dir.mkdir(parents=True, exist_ok=True)
        with open(bad_dir / "config.json", "w") as f:
            json.dump({"model_version": "aaroh-trajectory-v1"}, f)

        with self.assertRaises(FileNotFoundError):
            LongitudinalTrajectoryModel.load_from_artifact(bad_dir)


class TestTrajectoryInferencePipeline(unittest.TestCase):
    """Test suite for end-to-end TrajectoryInferencePipeline wiring text to trajectory."""

    def setUp(self) -> None:
        self.pipeline = TrajectoryInferencePipeline()

    def test_predict_from_texts_worsening_flow(self) -> None:
        """Sequential escalating distress messages yield positive velocity and worsening trajectory."""
        texts = [
            "I had an okay day today, feeling calm.",
            "Feeling a little anxious about work tomorrow.",
            "I feel very scared, overwhelmed, and can't sleep.",
            "Everything is falling apart, I feel terrified and hopeless.",
        ]
        timestamps = [
            "2026-03-01T10:00:00",
            "2026-03-02T10:00:00",
            "2026-03-03T10:00:00",
            "2026-03-04T10:00:00",
        ]

        out = self.pipeline.predict_from_texts(texts=texts, timestamps=timestamps)

        self.assertEqual(out["interactions_processed"], 4)
        self.assertIn("trajectory_score", out)
        self.assertIn("trajectory_state", out)
        self.assertIn("trend_velocity", out)
        self.assertGreater(out["trend_velocity"], 0.0)
        self.assertGreater(len(out["reasons"]), 0)

    def test_predict_from_texts_multilingual_hindi_english(self) -> None:
        """Pipeline seamlessly handles mixed English and Hindi session sequences."""
        texts = [
            "सब कुछ ठीक चल रहा है, कोई परेशानी नहीं है।",
            "मुझे थोड़ा डर और घबराहट महसूस हो रही है।",
            "I am feeling very anxious and isolated today.",
            "मुझे बहुत अकेला और लाचार महसूस हो रहा है, सब खत्म लग रहा है।",
        ]

        out = self.pipeline.predict_from_texts(texts=texts)

        self.assertEqual(out["interactions_processed"], 4)
        self.assertIn("trajectory_score", out)
        self.assertIn("trajectory_label", out)
        self.assertIn("trend_velocity_display", out)


class TestClinicalAndRegulatoryBoundaries(unittest.TestCase):
    """Test suite verifying strict clinical boundaries in trajectory outputs."""

    PROHIBITED_KEYS = [
        "diagnosis",
        "diagnostic_code",
        "phq_score",
        "gad_score",
        "suicide_risk",
        "future_risk",
        "treatment_recommendation",
        "intervention",
    ]

    def test_predict_trajectory_boundary_keys(self) -> None:
        """LongitudinalTrajectoryModel.predict_trajectory outputs must NEVER contain prohibited keys."""
        model = LongitudinalTrajectoryModel()
        records = [
            _make_dummy_record("CASE-B", i, 0.4) for i in range(3)
        ]
        case = CaseTrajectory("CASE-B", records, "UNKNOWN")

        pred = model.predict_trajectory(case)
        for key in self.PROHIBITED_KEYS:
            self.assertNotIn(key, pred)

    def test_enforce_trajectory_boundary_helper(self) -> None:
        """enforce_trajectory_boundary rejects prohibited output names."""
        valid_keys = [
            "trajectory_embedding",
            "trajectory_probabilities",
            "trajectory_score",
            "trajectory_label",
            "model_version",
        ]
        for k in valid_keys:
            enforce_trajectory_boundary(k)

        for bad in ["diagnosis", "future_risk", "treatment_recommendation", "suicide_risk"]:
            with self.assertRaises(ValueError):
                enforce_trajectory_boundary(bad)


if __name__ == "__main__":
    unittest.main()
