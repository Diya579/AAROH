"""Unit tests for Longitudinal Trajectory Model (Slice 3.7).

Verifies:
- Trajectory dataset creation & 432-dim feature vector packing.
- Chronological ordering & sorting integrity.
- History shorter than window pads correctly (left-pad with zeros).
- History equal to window passes unchanged.
- History longer than window truncates to most recent interactions.
- Chronological ordering preserved after truncation.
- Padding mask correctness.
- Case-level splitting with zero data leakage.
- Model instantiation and 4-metric parameter accounting.
- Execution modes (FALLBACK, PYTORCH_FROZEN, PYTORCH_FINETUNE).
- Forward pass, embedding normalization, and probability distribution.
- Public predict_trajectory() interface schema.
- Training step gradient descent & loss computation.
- Checkpoint saving and reloading.
- Export pipeline and artifact validation.
- Strict clinical boundary enforcement.
- CLI argument parsing.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.ml.training.evaluate_trajectory_model import parse_args as parse_eval_args
from backend.ml.training.models.common import enforce_trajectory_boundary
from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    DISTRESS_EMBEDDING_DIM,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    LABEL_IMPROVING,
    LABEL_RAPIDLY_WORSENING,
    LABEL_STABLE,
    LABEL_TO_ID,
    LABEL_WORSENING,
    TIMESTEP_INPUT_DIM,
    TRAJECTORY_DEFINITIONS,
    TRAJECTORY_EMBEDDING_DIM,
    TRAJECTORY_INTERNAL_SCORES,
    VALID_TRAJECTORY_LABELS,
    CaseTrajectory,
    TrajectoryDataset,
    TrajectoryInputRecord,
    TrajectoryLabel,
    build_synthetic_trajectories,
    determine_synthetic_trajectory_label,
    split_trajectories_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.trajectory.model import (
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    LongitudinalTrajectoryModel,
)
from backend.ml.training.train_trajectory import parse_args as parse_train_args


class TestLongitudinalTrajectoryModel(unittest.TestCase):
    """Test suite for Longitudinal Trajectory Model."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.seed = 42

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_trajectory_record_and_feature_packing(self) -> None:
        """Verifies TrajectoryInputRecord vector packing produces exact 432-dim vector."""
        rec = TrajectoryInputRecord(
            case_id="CASE-001",
            interaction_id="CASE-001-INT-01",
            timestamp="2026-01-01T10:00:00Z",
            distress_embedding=[0.05] * DISTRESS_EMBEDDING_DIM,
            distress_score=0.45,
            distress_level="MODERATE",
            fused_embedding=[0.02] * FUSED_EMBEDDING_DIM,
            behavioural_features=[0.1] * 8 + [0.0] * 8,
            engagement_features=[0.2] * 13 + [0.0] * 13,
            time_delta_hours=12.0,
            synthetic_trajectory_label="STABLE",
            history_length=1,
        )
        vec = rec.to_timestep_vector()
        self.assertEqual(len(vec), TIMESTEP_INPUT_DIM)
        self.assertEqual(len(vec), 432)
        # Check distress level one-hot: MODERATE is index 1 in (LOW, MODERATE, HIGH, CRITICAL)
        # Offset: 256 (fused) + 128 (distress_emb) + 1 (score) = 385
        self.assertEqual(vec[385], 0.0)  # LOW
        self.assertEqual(vec[386], 1.0)  # MODERATE
        self.assertEqual(vec[387], 0.0)  # HIGH
        self.assertEqual(vec[388], 0.0)  # CRITICAL

    def test_case_chronological_ordering(self) -> None:
        """Verifies CaseTrajectory enforces and preserves strict chronological sorting."""
        r1 = TrajectoryInputRecord(
            case_id="C1", interaction_id="I1", timestamp="2026-01-02T10:00:00Z",
            distress_embedding=[0.0] * 128, distress_score=0.3, distress_level="LOW",
            fused_embedding=[0.0] * 256, behavioural_features=[0.0] * 16,
            engagement_features=[0.0] * 26, time_delta_hours=24.0,
        )
        r2 = TrajectoryInputRecord(
            case_id="C1", interaction_id="I2", timestamp="2026-01-01T10:00:00Z",
            distress_embedding=[0.0] * 128, distress_score=0.2, distress_level="LOW",
            fused_embedding=[0.0] * 256, behavioural_features=[0.0] * 16,
            engagement_features=[0.0] * 26, time_delta_hours=0.0,
        )
        # Passing unsorted records should be sorted automatically
        case = CaseTrajectory(case_id="C1", records=[r1, r2], trajectory_label="STABLE")
        self.assertEqual(case.records[0].interaction_id, "I2")
        self.assertEqual(case.records[1].interaction_id, "I1")

    def test_history_window_shorter_than_window_pads_correctly(self) -> None:
        """Verifies sequences shorter than history_window are left-padded with zeros."""
        records = []
        for i in range(4):
            records.append(
                TrajectoryInputRecord(
                    case_id="C_SHORT", interaction_id=f"INT-{i}",
                    timestamp=f"2026-01-0{i+1}T10:00:00Z",
                    distress_embedding=[0.1] * 128, distress_score=0.2 + i * 0.05,
                    distress_level="LOW", fused_embedding=[0.1] * 256,
                    behavioural_features=[0.1] * 16, engagement_features=[0.1] * 26,
                    time_delta_hours=24.0,
                )
            )
        case = CaseTrajectory(case_id="C_SHORT", records=records, trajectory_label="STABLE")
        windowed_vecs, mask, seq_len = case.get_windowed_sequence(history_window=10)

        self.assertEqual(len(windowed_vecs), 10)
        self.assertEqual(seq_len, 4)
        # First 6 must be padded (mask = True, vector = all zeros)
        for t in range(6):
            self.assertTrue(mask[t])
            self.assertTrue(all(v == 0.0 for v in windowed_vecs[t]))
        # Last 4 must be valid interactions (mask = False)
        for t in range(6, 10):
            self.assertFalse(mask[t])
            self.assertFalse(all(v == 0.0 for v in windowed_vecs[t]))

    def test_history_window_equal_passes_unchanged(self) -> None:
        """Verifies sequences exactly equal to history_window pass unchanged with no padding."""
        records = []
        for i in range(10):
            records.append(
                TrajectoryInputRecord(
                    case_id="C_EXACT", interaction_id=f"INT-{i:02d}",
                    timestamp=f"2026-01-{i+1:02d}T10:00:00Z",
                    distress_embedding=[0.1] * 128, distress_score=0.3,
                    distress_level="MODERATE", fused_embedding=[0.1] * 256,
                    behavioural_features=[0.1] * 16, engagement_features=[0.1] * 26,
                    time_delta_hours=24.0,
                )
            )
        case = CaseTrajectory(case_id="C_EXACT", records=records, trajectory_label="STABLE")
        windowed_vecs, mask, seq_len = case.get_windowed_sequence(history_window=10)

        self.assertEqual(len(windowed_vecs), 10)
        self.assertEqual(seq_len, 10)
        self.assertTrue(all(m is False for m in mask))

    def test_history_window_longer_truncates_to_most_recent(self) -> None:
        """Verifies sequences longer than history_window retain ONLY the most recent interactions."""
        records = []
        for i in range(15):
            records.append(
                TrajectoryInputRecord(
                    case_id="C_LONG", interaction_id=f"INT-{i:02d}",
                    timestamp=f"2026-01-{i+1:02d}T10:00:00Z",
                    distress_embedding=[0.1] * 128, distress_score=0.1 + i * 0.05,
                    distress_level="MODERATE", fused_embedding=[0.1] * 256,
                    behavioural_features=[0.1] * 16, engagement_features=[0.1] * 26,
                    time_delta_hours=24.0,
                )
            )
        case = CaseTrajectory(case_id="C_LONG", records=records, trajectory_label="WORSENING")
        windowed_vecs, mask, seq_len = case.get_windowed_sequence(history_window=10)

        self.assertEqual(len(windowed_vecs), 10)
        self.assertEqual(seq_len, 10)
        self.assertTrue(all(m is False for m in mask))

        # Check that the first retained vector corresponds to INT-05 (most recent 10 are INT-05 to INT-14)
        expected_first = records[5].to_timestep_vector()
        expected_last = records[14].to_timestep_vector()
        self.assertEqual(windowed_vecs[0], expected_first)
        self.assertEqual(windowed_vecs[-1], expected_last)

    def test_case_split_zero_leakage(self) -> None:
        """Verifies that case splitting produces zero case leakage across splits."""
        trajectories = build_synthetic_trajectories(case_count=20, seed=self.seed)
        train_trajs, val_trajs = split_trajectories_by_case(trajectories, val_ratio=0.25, seed=self.seed)

        train_cases = set(t.case_id for t in train_trajs)
        val_cases = set(t.case_id for t in val_trajs)
        self.assertEqual(len(train_cases.intersection(val_cases)), 0)

        # Artificial leakage raises ValueError
        with self.assertRaises(ValueError):
            validate_no_case_leakage(train_trajs, [train_trajs[0]])

    def test_model_instantiation_and_parameter_accounting(self) -> None:
        """Verifies model structure and 4-metric parameter accounting."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        self.assertEqual(model.execution_mode, EXECUTION_MODE_FALLBACK)
        self.assertIsNone(model.text_backbone)
        self.assertIsNone(model.audio_backbone)

        counts = model.get_parameter_counts()
        self.assertEqual(counts["trainable_parameters"], 113_348)
        self.assertEqual(counts["backbone_parameters"], 229_774_080)
        self.assertEqual(counts["total_parameters_if_instantiated"], 113_348 + 229_774_080)
        self.assertEqual(counts["actually_instantiated_parameters"], 113_348)

    def test_execution_modes(self) -> None:
        """Verifies explicit execution mode selection."""
        m_fb = LongitudinalTrajectoryModel(force_mode=EXECUTION_MODE_FALLBACK)
        self.assertEqual(m_fb.execution_mode, EXECUTION_MODE_FALLBACK)
        self.assertEqual(m_fb.get_parameter_counts()["actually_instantiated_parameters"], 113_348)

        m_fr = LongitudinalTrajectoryModel(force_mode=EXECUTION_MODE_PYTORCH_FROZEN)
        self.assertEqual(m_fr.execution_mode, EXECUTION_MODE_PYTORCH_FROZEN)
        self.assertEqual(m_fr.get_parameter_counts()["trainable_parameters"], 163_012)

        m_ft = LongitudinalTrajectoryModel(force_mode=EXECUTION_MODE_PYTORCH_FINETUNE)
        self.assertEqual(m_ft.execution_mode, EXECUTION_MODE_PYTORCH_FINETUNE)
        self.assertEqual(m_ft.get_parameter_counts()["trainable_parameters"], 163_012)

        with self.assertRaises(ValueError):
            LongitudinalTrajectoryModel(force_mode="INVALID_MODE")

    def test_forward_pass_and_embedding_norm(self) -> None:
        """Verifies forward pass output shapes, probabilities sum to 1.0, and unit sphere norm."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        dummy_sequence = [[0.1] * TIMESTEP_INPUT_DIM for _ in range(10)]
        mask = [True] * 4 + [False] * 6

        emb, probs = model.forward(dummy_sequence, mask)
        self.assertEqual(len(emb), TRAJECTORY_EMBEDDING_DIM)
        self.assertEqual(len(probs), 4)

        norm = math.sqrt(sum(x * x for x in emb))
        self.assertAlmostEqual(norm, 1.0, places=4)
        self.assertAlmostEqual(sum(probs), 1.0, places=4)

    def test_predict_trajectory_public_interface(self) -> None:
        """Verifies predict_trajectory accepts CaseTrajectory, records, or vectors and returns valid schema."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        trajs = build_synthetic_trajectories(case_count=2, seed=self.seed)
        traj = trajs[0]

        # 1. Using CaseTrajectory
        res1 = model.predict_trajectory(traj)
        self.assertIn("trajectory_embedding", res1)
        self.assertIn("trajectory_probabilities", res1)
        self.assertIn("trajectory_score", res1)
        self.assertIn("trajectory_label", res1)
        self.assertIn("model_version", res1)
        self.assertEqual(res1["model_version"], "aaroh-trajectory-v1")
        self.assertEqual(len(res1["trajectory_embedding"]), 128)
        self.assertIn(res1["trajectory_label"], VALID_TRAJECTORY_LABELS)
        self.assertTrue(-1.0 <= res1["trajectory_score"] <= 1.0)

        # 2. Using list of records
        res2 = model.predict_trajectory(traj.records)
        self.assertEqual(res1["trajectory_label"], res2["trajectory_label"])
        self.assertEqual(res1["trajectory_score"], res2["trajectory_score"])

    def test_training_step_loss_reduction(self) -> None:
        """Verifies training step decreases loss over iterations."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        trajectories = build_synthetic_trajectories(case_count=12, seed=self.seed)
        ds = TrajectoryDataset(trajectories, history_window=10)
        batches = list(ds.iterate_batches(batch_size=4, shuffle=False))

        losses = []
        for _ in range(4):
            for b in batches:
                l = model.train_step(b, lr=5e-3)
                losses.append(l)

        self.assertTrue(all(math.isfinite(l) for l in losses))
        self.assertTrue(all(l >= 0.0 for l in losses))
        self.assertLessEqual(losses[-1], losses[0])

    def test_checkpoint_save_and_reload(self) -> None:
        """Verifies checkpoint saving and exact weight restoration."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        chk_file = Path(self.temp_dir) / "checkpoint.pt"

        trajs = build_synthetic_trajectories(case_count=3, seed=self.seed)
        out_before = model.predict_trajectory(trajs[0])

        model.save_checkpoint(chk_file, epoch=2, metrics={"loss": 0.12})
        self.assertTrue(chk_file.exists())

        reload_model = LongitudinalTrajectoryModel(seed=self.seed + 100)
        meta = reload_model.load_checkpoint(chk_file)
        self.assertEqual(meta["epoch"], 2)

        out_after = reload_model.predict_trajectory(trajs[0])
        self.assertEqual(out_before["trajectory_label"], out_after["trajectory_label"])
        self.assertEqual(out_before["trajectory_score"], out_after["trajectory_score"])
        self.assertEqual(out_before["trajectory_embedding"], out_after["trajectory_embedding"])

    def test_export_pipeline_and_artifacts(self) -> None:
        """Verifies export produces all 5 required files with valid schema."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        export_dir = Path(self.temp_dir) / "exported_trajectory_model"
        artifacts = model.export(export_dir, metrics={"accuracy": 0.85})

        expected_keys = {"weights", "config", "metadata", "metrics", "label_mapping"}
        self.assertEqual(set(artifacts.keys()), expected_keys)

        for key, path_str in artifacts.items():
            self.assertTrue(os.path.exists(path_str), f"Exported file for {key} missing at {path_str}")

        # Check config.json content
        with open(artifacts["config"], "r", encoding="utf-8") as f:
            cfg = json.load(f)
            self.assertEqual(cfg["model_type"], "longitudinal_trajectory_model")
            self.assertEqual(cfg["model_version"], "aaroh-trajectory-v1")
            self.assertEqual(cfg["history_window"], 10)
            self.assertEqual(cfg["trajectory_embedding_dim"], 128)
            self.assertEqual(cfg["num_classes"], 4)

        # Check label_mapping.json content
        with open(artifacts["label_mapping"], "r", encoding="utf-8") as f:
            lm = json.load(f)
            self.assertEqual(lm["task"], "longitudinal_trajectory_estimation")
            self.assertEqual(lm["labels"], list(VALID_TRAJECTORY_LABELS))
            self.assertIn("STABLE", lm["definitions"])
            self.assertIn("IMPROVING", lm["definitions"])
            self.assertIn("WORSENING", lm["definitions"])
            self.assertIn("RAPIDLY_WORSENING", lm["definitions"])

    def test_clinical_boundary_enforcement(self) -> None:
        """Verifies that clinical boundary checker rejects forbidden medical, escalation, and diagnostic terms."""
        forbidden_terms = [
            "diagnosis",
            "clinical_diagnosis",
            "escalation",
            "future_risk",
            "depression",
            "anxiety",
            "ptsd",
            "suicide",
            "suicide_risk",
            "treatment",
            "intervention",
            "confidence",
            "explanation",
            "phq",
            "gad",
        ]
        for term in forbidden_terms:
            with self.assertRaises(ValueError):
                enforce_trajectory_boundary(term)

        allowed_terms = [
            "trajectory_embedding",
            "trajectory_probabilities",
            "trajectory_score",
            "trajectory_label",
            "model_version",
        ]
        for term in allowed_terms:
            enforce_trajectory_boundary(term)

    def test_synthetic_trajectory_generation_distribution(self) -> None:
        """Verifies synthetic trajectory builder produces all 4 patterns."""
        trajectories = build_synthetic_trajectories(case_count=16, seed=self.seed)
        labels = [t.trajectory_label for t in trajectories]
        for lbl in VALID_TRAJECTORY_LABELS:
            self.assertIn(lbl, labels, f"Missing pattern {lbl} in generated trajectories")

    def test_centralized_trajectory_label_definitions(self) -> None:
        """Verifies that every exported label exists in the centralized definition with canonical scores."""
        expected_scores = {
            TrajectoryLabel.IMPROVING: -1.0,
            TrajectoryLabel.STABLE: 0.0,
            TrajectoryLabel.WORSENING: 0.5,
            TrajectoryLabel.RAPIDLY_WORSENING: 1.0,
        }
        for member in TrajectoryLabel:
            # 1. Canonical score check
            self.assertEqual(member.internal_score, expected_scores[member])
            self.assertEqual(TRAJECTORY_INTERNAL_SCORES[member], expected_scores[member])
            # 2. Definition check
            self.assertIn(member, TRAJECTORY_DEFINITIONS)
            self.assertTrue(len(member.definition) > 10)
            # 3. Label string check
            self.assertIn(member.value, VALID_TRAJECTORY_LABELS)

        # Ensure exact count matches
        self.assertEqual(len(TrajectoryLabel), 4)
        self.assertEqual(len(VALID_TRAJECTORY_LABELS), 4)

    def test_trajectory_score_computed_from_centralized_definition(self) -> None:
        """Verifies that trajectory_score is computed strictly via sum(prob * internal_score)."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        trajs = build_synthetic_trajectories(case_count=3, seed=self.seed)
        for t in trajs:
            out = model.predict_trajectory(t)
            probs = out["trajectory_probabilities"]

            # Compute expected score from centralized enum
            expected_score = sum(
                probs[tl.value] * tl.internal_score
                for tl in TrajectoryLabel
            )
            expected_score = round(max(-1.0, min(1.0, expected_score)), 4)
            self.assertAlmostEqual(out["trajectory_score"], expected_score, places=4)

    def test_modifying_internal_score_mapping_updates_trajectory_score_automatically(self) -> None:
        """Verifies that modifying the internal score mapping updates trajectory_score without code changes."""
        model = LongitudinalTrajectoryModel(seed=self.seed)
        trajs = build_synthetic_trajectories(case_count=1, seed=self.seed)
        t = trajs[0]

        # Initial prediction
        out1 = model.predict_trajectory(t)
        initial_score = out1["trajectory_score"]

        # Temporarily modify TRAJECTORY_INTERNAL_SCORES
        original_worsening_score = TRAJECTORY_INTERNAL_SCORES[TrajectoryLabel.WORSENING]
        try:
            TRAJECTORY_INTERNAL_SCORES[TrajectoryLabel.WORSENING] = 0.95
            out2 = model.predict_trajectory(t)

            # Recomputed score should reflect the updated mapping
            expected_new_score = sum(
                out2["trajectory_probabilities"][tl.value] * tl.internal_score
                for tl in TrajectoryLabel
            )
            expected_new_score = round(max(-1.0, min(1.0, expected_new_score)), 4)
            self.assertAlmostEqual(out2["trajectory_score"], expected_new_score, places=4)
        finally:
            # Restore canonical mapping
            TRAJECTORY_INTERNAL_SCORES[TrajectoryLabel.WORSENING] = original_worsening_score

        # Confirm restored prediction equals initial prediction
        out3 = model.predict_trajectory(t)
        self.assertEqual(out3["trajectory_score"], initial_score)

    def test_cli_argument_parsing(self) -> None:
        """Verifies training and evaluation CLI argument parsers."""
        import sys
        old_argv = sys.argv
        try:
            sys.argv = [
                "train_trajectory.py",
                "--epochs", "3",
                "--batch-size", "16",
                "--lr", "0.002",
                "--smoke-test",
                "--history-window", "8",
            ]
            t_args = parse_train_args()
            self.assertEqual(t_args.epochs, 3)
            self.assertEqual(t_args.batch_size, 16)
            self.assertEqual(t_args.lr, 0.002)
            self.assertTrue(t_args.smoke_test)
            self.assertEqual(t_args.history_window, 8)

            sys.argv = [
                "evaluate_trajectory_model.py",
                "--model-dir", "custom/trajectory",
                "--case-count", "20",
                "--history-window", "12",
            ]
            e_args = parse_eval_args()
            self.assertEqual(e_args.model_dir, "custom/trajectory")
            self.assertEqual(e_args.case_count, 20)
            self.assertEqual(e_args.history_window, 12)
        finally:
            sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
