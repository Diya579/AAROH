"""Comprehensive Unit Tests for Dynamic Distress Model (Slice 3.6).

Tests:
1. DistressInputRecord creation, vectorization (301-dim), and None != 0 preservation.
2. Integration with Slice 3.5 MultimodalInputRecord and MultimodalFusionModel.
3. Case-level splitting and strict zero-leakage enforcement.
4. DistressDataset batch iteration.
5. Model instantiation, layer shapes, and exact 4-metric parameter accounting.
6. Execution modes (FALLBACK, PYTORCH_FROZEN, PYTORCH_FINETUNE).
7. Forward pass and latent embedding unit-sphere normalization.
8. Threshold mapping across LOW, MODERATE, HIGH, CRITICAL and custom thresholds.
9. predict_distress() public interface contract and input polymorphism.
10. Clinical boundary enforcement (rejects diagnoses, escalation, future risk, etc.).
11. Checkpoint saving and bit-for-bit reload reproduction.
12. Model export pipeline and artifact completeness.
13. Gradient training step loss reduction.
14. CLI argument parsing for training and evaluation.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from backend.ml.training.evaluate_distress_model import parse_args as parse_eval_args
from backend.ml.training.models.common import (
    enforce_distress_boundary,
    enforce_fusion_boundary,
)
from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    DISTRESS_INPUT_DIM,
    ENGAGEMENT_COUNT,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    DistressDataset,
    DistressInputRecord,
    build_synthetic_distress_records,
    compute_synthetic_distress_score,
    split_distress_records_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_THRESHOLDS,
    DISTILBERT_PARAM_COUNT,
    DISTRESS_EMBEDDING_DIM,
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    EXECUTION_MODE_PYTORCH_FROZEN,
    FROZEN_BACKBONES_PARAM_COUNT,
    INPUT_DIM,
    LEVEL_CRITICAL,
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_MODERATE,
    VALID_DISTRESS_LEVELS,
    WAV2VEC2_PARAM_COUNT,
    DynamicDistressModel,
)
from backend.ml.training.models.fusion.dataset import (
    MultimodalInputRecord,
    build_synthetic_multimodal_records,
)
from backend.ml.training.models.fusion.model import MultimodalFusionModel
from backend.ml.training.train_distress import parse_args as parse_train_args


class TestDynamicDistressModel(unittest.TestCase):
    """Test suite for Dynamic Distress Model and pipeline components."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.seed = 42

    def tearDown(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_distress_input_record_creation_and_vectorization(self) -> None:
        """Verifies DistressInputRecord vectorization and None != 0 preservation."""
        fused_emb = [0.05] * FUSED_EMBEDDING_DIM

        # Record with some present and some None features
        b_feats = [0.8, None, 0.5, None, 1.0, 0.4, -0.1, 0.0]
        e_feats = [1.0, 0.0, None, 0.9, 2.0, None, 1.5, 0.1, 4.0, 3.0, 0.85, -0.2, 0.1]

        rec = DistressInputRecord(
            case_id="CASE-001",
            interaction_date="2026-03-01",
            fused_embedding=fused_emb,
            modality_weights={"tabular": 0.5, "text": 0.3, "audio": 0.2},
            behavioural_features=b_feats,
            engagement_features=e_feats,
            synthetic_distress_score=0.65,
        )

        vec = rec.to_feature_vector()
        self.assertEqual(len(vec), DISTRESS_INPUT_DIM)
        self.assertEqual(len(vec), 301)

        # Verify fused embedding slice
        self.assertEqual(vec[:256], fused_emb)

        # Verify behavioural slice: 8 values + 8 masks = indices 256..272
        b_vals = vec[256:264]
        b_masks = vec[264:272]
        self.assertEqual(b_vals[0], 0.8)
        self.assertEqual(b_masks[0], 1.0)
        self.assertEqual(b_vals[1], 0.0)
        self.assertEqual(b_masks[1], 0.0)  # None represented with mask 0.0
        self.assertEqual(b_vals[7], 0.0)
        self.assertEqual(b_masks[7], 1.0)  # Real 0.0 has mask 1.0

        # Verify modality weights at the end: indices 298..301
        self.assertAlmostEqual(vec[298], 0.5)
        self.assertAlmostEqual(vec[299], 0.3)
        self.assertAlmostEqual(vec[300], 0.2)

    def test_from_multimodal_record_integration(self) -> None:
        """Verifies constructor integrating MultimodalInputRecord and MultimodalFusionModel."""
        mm_records = build_synthetic_multimodal_records(count=5, seed=self.seed)
        fusion_model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)

        rec0 = mm_records[0]
        d_rec = DistressInputRecord.from_multimodal_record(rec0, fusion_model=fusion_model)

        self.assertEqual(len(d_rec.fused_embedding), 256)
        norm = math.sqrt(sum(x * x for x in d_rec.fused_embedding))
        self.assertAlmostEqual(norm, 1.0, places=3)
        self.assertIsNotNone(d_rec.synthetic_distress_score)
        self.assertTrue(0.0 <= d_rec.synthetic_distress_score <= 1.0)
        self.assertEqual(d_rec.label_disclaimer, LABEL_DISCLAIMER)

    def test_case_level_splitting_and_zero_leakage(self) -> None:
        """Verifies deterministic case-level splitting and leakage detection."""
        records = build_synthetic_distress_records(count=60, seed=self.seed)
        train_recs, val_recs = split_distress_records_by_case(records, val_ratio=0.25, seed=self.seed)

        train_cases = set(r.case_id for r in train_recs)
        val_cases = set(r.case_id for r in val_recs)

        self.assertTrue(len(train_cases) > 0)
        self.assertTrue(len(val_cases) > 0)
        self.assertEqual(len(train_cases.intersection(val_cases)), 0)

        # Artificial leakage test
        with self.assertRaises(ValueError):
            validate_no_case_leakage(train_recs, [train_recs[0]])

    def test_distress_dataset_batch_iteration(self) -> None:
        """Verifies dataset length and batch formatting."""
        records = build_synthetic_distress_records(count=20, seed=self.seed)
        ds = DistressDataset(records)
        self.assertEqual(len(ds), 20)

        batches = list(ds.iterate_batches(batch_size=8, shuffle=False, seed=self.seed))
        self.assertEqual(len(batches), 3)  # 8, 8, 4
        self.assertEqual(len(batches[0]["inputs"]), 8)
        self.assertEqual(len(batches[0]["inputs"][0]), DISTRESS_INPUT_DIM)
        self.assertEqual(len(batches[0]["targets"]), 8)
        self.assertEqual(len(batches[2]["inputs"]), 4)

    def test_model_instantiation_and_parameter_accounting(self) -> None:
        """Verifies model structure and accurate 4-metric parameter accounting."""
        model = DynamicDistressModel(seed=self.seed)
        self.assertEqual(model.execution_mode, EXECUTION_MODE_FALLBACK)
        self.assertIsNone(model.text_backbone)
        self.assertIsNone(model.audio_backbone)

        counts = model.get_parameter_counts()
        self.assertEqual(counts["trainable_parameters"], 80_001)
        self.assertEqual(counts["trainable_head_parameters"], 80_001)
        self.assertEqual(counts["backbone_parameters"], 229_774_080)
        self.assertEqual(counts["total_parameters_if_instantiated"], 229_854_081)
        self.assertEqual(counts["actually_instantiated_parameters"], 80_001)

    def test_execution_modes(self) -> None:
        """Verifies explicit execution mode selection and validation."""
        # Fallback mode
        m_fb = DynamicDistressModel(force_mode=EXECUTION_MODE_FALLBACK)
        self.assertEqual(m_fb.execution_mode, EXECUTION_MODE_FALLBACK)
        self.assertEqual(m_fb.get_parameter_counts()["actually_instantiated_parameters"], 80_001)

        # Frozen mode
        m_fr = DynamicDistressModel(force_mode=EXECUTION_MODE_PYTORCH_FROZEN)
        self.assertEqual(m_fr.execution_mode, EXECUTION_MODE_PYTORCH_FROZEN)
        self.assertEqual(m_fr.get_parameter_counts()["actually_instantiated_parameters"], 229_854_081)

        # Finetune mode
        m_ft = DynamicDistressModel(force_mode=EXECUTION_MODE_PYTORCH_FINETUNE)
        self.assertEqual(m_ft.execution_mode, EXECUTION_MODE_PYTORCH_FINETUNE)
        self.assertEqual(m_ft.get_parameter_counts()["actually_instantiated_parameters"], 229_854_081)

        # Invalid mode
        with self.assertRaises(ValueError):
            DynamicDistressModel(force_mode="INVALID_MODE")

    def test_forward_pass_and_embedding_normalization(self) -> None:
        """Verifies forward pass output shapes, scores, and unit-sphere embedding norm."""
        model = DynamicDistressModel(seed=self.seed)
        dummy_input = [0.1] * DISTRESS_INPUT_DIM

        emb, score = model.forward(dummy_input)
        self.assertEqual(len(emb), DISTRESS_EMBEDDING_DIM)
        self.assertEqual(len(emb), 128)

        norm = math.sqrt(sum(x * x for x in emb))
        self.assertAlmostEqual(norm, 1.0, places=4)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_threshold_mapping(self) -> None:
        """Verifies continuous score categorization into LOW, MODERATE, HIGH, CRITICAL."""
        model = DynamicDistressModel()

        self.assertEqual(model.map_score_to_level(0.0), LEVEL_LOW)
        self.assertEqual(model.map_score_to_level(0.24), LEVEL_LOW)
        self.assertEqual(model.map_score_to_level(0.25), LEVEL_MODERATE)
        self.assertEqual(model.map_score_to_level(0.54), LEVEL_MODERATE)
        self.assertEqual(model.map_score_to_level(0.55), LEVEL_HIGH)
        self.assertEqual(model.map_score_to_level(0.79), LEVEL_HIGH)
        self.assertEqual(model.map_score_to_level(0.80), LEVEL_CRITICAL)
        self.assertEqual(model.map_score_to_level(1.0), LEVEL_CRITICAL)

        # Custom thresholds
        custom_model = DynamicDistressModel(thresholds={"low": 0.30, "moderate": 0.60, "high": 0.90})
        self.assertEqual(custom_model.map_score_to_level(0.29), LEVEL_LOW)
        self.assertEqual(custom_model.map_score_to_level(0.35), LEVEL_MODERATE)
        self.assertEqual(custom_model.map_score_to_level(0.70), LEVEL_HIGH)
        self.assertEqual(custom_model.map_score_to_level(0.95), LEVEL_CRITICAL)

        # Invalid threshold ordering
        with self.assertRaises(ValueError):
            DynamicDistressModel(thresholds={"low": 0.60, "moderate": 0.30, "high": 0.90})

    def test_predict_distress_public_interface(self) -> None:
        """Verifies predict_distress accepts records, dicts, and vectors and returns valid schema with model_version."""
        model = DynamicDistressModel(seed=self.seed)
        records = build_synthetic_distress_records(count=3, seed=self.seed)
        rec0 = records[0]

        # 1. Using DistressInputRecord
        res1 = model.predict_distress(rec0)
        self.assertIn("distress_embedding", res1)
        self.assertIn("distress_score", res1)
        self.assertIn("distress_level", res1)
        self.assertIn("model_version", res1)
        self.assertEqual(res1["model_version"], "aaroh-distress-v1")
        self.assertEqual(len(res1["distress_embedding"]), 128)
        self.assertTrue(0.0 <= res1["distress_score"] <= 1.0)
        self.assertIn(res1["distress_level"], VALID_DISTRESS_LEVELS)

        # 2. Using dict with inputs
        res2 = model.predict_distress({"inputs": rec0.to_feature_vector()})
        self.assertEqual(res1["distress_score"], res2["distress_score"])
        self.assertEqual(res2["model_version"], "aaroh-distress-v1")

        # 3. Using raw vector
        res3 = model.predict_distress(rec0.to_feature_vector())
        self.assertEqual(res1["distress_score"], res3["distress_score"])

    def test_versioned_threshold_configuration(self) -> None:
        """Verifies loading thresholds from embedded config.json as well as legacy thresholds.json."""
        # 1. Embedded threshold_configuration in config.json
        embedded_config_file = Path(self.temp_dir) / "custom_config.json"
        embedded_data = {
            "model_type": "dynamic_distress_model",
            "threshold_configuration": {
                "version": "1.0",
                "thresholds": {"low": 0.20, "moderate": 0.50, "high": 0.75},
            },
        }
        with open(embedded_config_file, "w", encoding="utf-8") as f:
            json.dump(embedded_data, f)

        model_embedded = DynamicDistressModel(config_path=embedded_config_file)
        self.assertEqual(model_embedded.thresholds["low"], 0.20)
        self.assertEqual(model_embedded.thresholds["moderate"], 0.50)
        self.assertEqual(model_embedded.thresholds["high"], 0.75)
        self.assertEqual(model_embedded.map_score_to_level(0.18), LEVEL_LOW)
        self.assertEqual(model_embedded.map_score_to_level(0.22), LEVEL_MODERATE)
        self.assertEqual(model_embedded.map_score_to_level(0.55), LEVEL_HIGH)
        self.assertEqual(model_embedded.map_score_to_level(0.80), LEVEL_CRITICAL)

        # 2. Legacy fallback from thresholds.json
        legacy_thresh_file = Path(self.temp_dir) / "legacy_thresholds.json"
        legacy_data = {
            "version": "1.0",
            "thresholds": {"low": 0.22, "moderate": 0.52, "high": 0.78},
        }
        with open(legacy_thresh_file, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        model_legacy = DynamicDistressModel(config_path=legacy_thresh_file)
        self.assertEqual(model_legacy.thresholds["low"], 0.22)
        self.assertEqual(model_legacy.thresholds["moderate"], 0.52)
        self.assertEqual(model_legacy.thresholds["high"], 0.78)

        # 3. Flat dictionary fallback
        flat_file = Path(self.temp_dir) / "flat_thresholds.json"
        with open(flat_file, "w", encoding="utf-8") as f:
            json.dump({"low": 0.15, "moderate": 0.45, "high": 0.70}, f)
        model_flat = DynamicDistressModel(config_path=flat_file)
        self.assertEqual(model_flat.thresholds["low"], 0.15)
        self.assertEqual(model_flat.thresholds["moderate"], 0.45)
        self.assertEqual(model_flat.thresholds["high"], 0.70)

    def test_clinical_boundary_enforcement(self) -> None:
        """Verifies that clinical boundary checker rejects forbidden medical and trajectory terms."""
        forbidden_terms = [
            "diagnosis",
            "clinical_diagnosis",
            "medical_diagnosis",
            "escalation",
            "escalation_probability",
            "future_risk",
            "future_prediction",
            "depression",
            "anxiety",
            "ptsd",
            "suicide",
            "suicide_risk",
            "suicide_prediction",
            "treatment",
            "treatment_recommendation",
            "intervention",
            "intervention_recommendation",
            "phq",
            "gad",
            "trajectory",
            "longitudinal_prediction",
        ]
        for term in forbidden_terms:
            with self.assertRaises(ValueError):
                enforce_distress_boundary(term)

        # Allowed terms should pass cleanly
        allowed_terms = ["distress_embedding", "distress_score", "distress_level", "model_version"]
        for term in allowed_terms:
            enforce_distress_boundary(term)

    def test_checkpoint_save_and_reload(self) -> None:
        """Verifies checkpoint saving and exact weight restoration."""
        model = DynamicDistressModel(seed=self.seed)
        chk_file = Path(self.temp_dir) / "checkpoint.pt"

        records = build_synthetic_distress_records(count=10, seed=self.seed)
        rec = records[0]
        out_before = model.predict_distress(rec)

        model.save_checkpoint(chk_file, epoch=2, metrics={"loss": 0.042})
        self.assertTrue(chk_file.exists())

        reload_model = DynamicDistressModel(seed=self.seed + 100)
        meta = reload_model.load_checkpoint(chk_file)
        self.assertEqual(meta["epoch"], 2)

        out_after = reload_model.predict_distress(rec)
        self.assertEqual(out_before["distress_score"], out_after["distress_score"])
        self.assertEqual(out_before["distress_level"], out_after["distress_level"])
        self.assertEqual(out_before["distress_embedding"], out_after["distress_embedding"])
        self.assertEqual(out_before["model_version"], out_after["model_version"])

    def test_export_pipeline_and_artifacts(self) -> None:
        """Verifies export produces all required files with embedded thresholds, metadata, and disclaimer."""
        model = DynamicDistressModel(seed=self.seed)
        export_dir = Path(self.temp_dir) / "exported_distress_model"
        artifacts = model.export(export_dir, metrics={"mae": 0.035, "rmse": 0.048})

        expected_keys = {"weights", "config", "metadata", "metrics", "label_mapping"}
        self.assertEqual(set(artifacts.keys()), expected_keys)

        for key, path_str in artifacts.items():
            self.assertTrue(os.path.exists(path_str), f"Exported file for {key} missing at {path_str}")

        # Check config.json content (embedded versioned thresholds)
        with open(artifacts["config"], "r", encoding="utf-8") as f:
            cfg = json.load(f)
            self.assertEqual(cfg["model_version"], "aaroh-distress-v1")
            self.assertIn("threshold_configuration", cfg)
            th_cfg = cfg["threshold_configuration"]
            self.assertEqual(th_cfg["version"], "1.0")
            self.assertEqual(th_cfg["model_version"], "aaroh-distress-v1")
            self.assertEqual(th_cfg["thresholds"]["low"], 0.25)
            self.assertEqual(th_cfg["thresholds"]["moderate"], 0.55)
            self.assertEqual(th_cfg["thresholds"]["high"], 0.80)
            self.assertIn("disclaimer", th_cfg)
            self.assertEqual(cfg["thresholds"]["low"], 0.25)

        # Check metadata.json content
        with open(artifacts["metadata"], "r", encoding="utf-8") as f:
            meta = json.load(f)
            self.assertEqual(meta["model_name"], "aaroh-dynamic-distress")
            self.assertEqual(meta["model_version"], "aaroh-distress-v1")
            self.assertEqual(meta["execution_mode"], EXECUTION_MODE_FALLBACK)
            self.assertEqual(meta["label_disclaimer"], LABEL_DISCLAIMER)
            self.assertIn("parameter_counts", meta)
            self.assertIn("instantiation_note", meta)

        # Check label_mapping.json content
        with open(artifacts["label_mapping"], "r", encoding="utf-8") as f:
            lm = json.load(f)
            self.assertEqual(lm["task"], "dynamic_distress_estimation")
            self.assertEqual(lm["disclaimer"], LABEL_DISCLAIMER)
            self.assertEqual(lm["levels"], list(VALID_DISTRESS_LEVELS))

    def test_training_step_loss_reduction(self) -> None:
        """Verifies training step produces finite loss and updates weights."""
        model = DynamicDistressModel(seed=self.seed)
        records = build_synthetic_distress_records(count=16, seed=self.seed)
        ds = DistressDataset(records)
        batches = list(ds.iterate_batches(batch_size=8, shuffle=False))

        losses = []
        for _ in range(3):
            for b in batches:
                l = model.train_step(b, lr=1e-2)
                losses.append(l)

        self.assertTrue(all(math.isfinite(l) for l in losses))
        self.assertTrue(all(l >= 0.0 for l in losses))

    def test_cli_argument_parsing(self) -> None:
        """Verifies command-line argument parsers for training and evaluation."""
        import sys
        old_argv = sys.argv

        try:
            sys.argv = [
                "train_distress.py",
                "--epochs", "2",
                "--batch-size", "8",
                "--lr", "0.005",
                "--smoke-test",
                "--unfreeze-backbone",
            ]
            t_args = parse_train_args()
            self.assertEqual(t_args.epochs, 2)
            self.assertEqual(t_args.batch_size, 8)
            self.assertEqual(t_args.lr, 0.005)
            self.assertTrue(t_args.smoke_test)
            self.assertTrue(t_args.unfreeze_backbone)

            sys.argv = [
                "evaluate_distress_model.py",
                "--model-dir", "custom/distress",
                "--sample-count", "40",
            ]
            e_args = parse_eval_args()
            self.assertEqual(e_args.model_dir, "custom/distress")
            self.assertEqual(e_args.sample_count, 40)
        finally:
            sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
