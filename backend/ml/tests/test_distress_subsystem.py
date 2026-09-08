"""Comprehensive Unit Tests for Dynamic Distress Subsystem (Slice 3.6).

Tests:
1. DistressEvidence generation, confidence scoring, and explanation attribution.
2. Multilingual lexicon matching (English & Hindi) and protective factor identification.
3. DynamicDistressModel.predict_distress_with_evidence interface and output contract.
4. DynamicDistressModel.load_from_artifact round-trip serialization and deterministic parity.
5. DistressInferencePipeline end-to-end text-to-distress flow.
6. Edge case handling: empty text, missing tabular features, and None preservation.
7. Strict clinical boundary enforcement (no diagnoses, PHQ/GAD scores, or suicide risk).
8. Evaluation metric calculation (MAE, RMSE, Pearson r, Macro F1, Per-level metrics).
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from backend.ml.training.evaluate_distress_model import evaluate_distress
from backend.ml.training.models.common import enforce_distress_boundary
from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    DISTRESS_INPUT_DIM,
    ENGAGEMENT_COUNT,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    DistressDataset,
    DistressInputRecord,
    build_synthetic_distress_records,
)
from backend.ml.training.models.distress.explainability import (
    DistressEvidence,
    calculate_distress_confidence,
    generate_distress_evidence,
)
from backend.ml.training.models.distress.inference import (
    DistressInferencePipeline,
    _project_text_to_distress_fused_embedding,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_THRESHOLDS,
    LEVEL_CRITICAL,
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_MODERATE,
    VALID_DISTRESS_LEVELS,
    DynamicDistressModel,
)


class TestDistressExplainability(unittest.TestCase):
    """Test suite for distress evidence generation and explainability engine."""

    def test_calculate_distress_confidence_bounds(self) -> None:
        """Confidence score must strictly stay within [0.50, 0.99]."""
        # Deep within interval (0.10 is far from 0.25 threshold)
        conf_high = calculate_distress_confidence(
            score=0.10,
            thresholds=DEFAULT_THRESHOLDS,
        )
        self.assertGreaterEqual(conf_high, 0.50)
        self.assertLessEqual(conf_high, 0.99)
        self.assertGreater(conf_high, 0.75)

        # Right on the boundary (0.25 is distance 0.0 from low threshold)
        conf_boundary = calculate_distress_confidence(
            score=0.25,
            thresholds=DEFAULT_THRESHOLDS,
        )
        self.assertGreaterEqual(conf_boundary, 0.50)
        self.assertLessEqual(conf_boundary, 0.99)
        self.assertLess(conf_boundary, conf_high)

    def test_generate_distress_evidence_structure(self) -> None:
        """Evidence output must adhere strictly to structured machine-readable format."""
        emotions = {"fear": 0.65, "sadness": 0.40, "joy": 0.02, "optimism": 0.05}
        evidence = generate_distress_evidence(
            distress_score=0.68,
            distress_level="HIGH",
            thresholds=DEFAULT_THRESHOLDS,
            model_version="1.0.0",
            raw_text="I feel terrified and hopeless about everything. मुझे बहुत डर लग रहा है",
            emotion_probabilities=emotions,
        )

        self.assertIsInstance(evidence, DistressEvidence)
        d = evidence.to_dict()

        # Core keys
        self.assertIn("distress_score", d)
        self.assertIn("distress_level", d)
        self.assertIn("confidence", d)
        self.assertIn("main_contributors", d)
        self.assertIn("top_emotion_drivers", d)
        self.assertIn("protective_factors", d)
        self.assertIn("lexicon_matches", d)
        self.assertIn("modality_weights", d)
        self.assertIn("label_disclaimer", d)

        # Content verification
        self.assertEqual(d["distress_level"], "HIGH")
        self.assertAlmostEqual(d["distress_score"], 0.68)
        self.assertIn("fear", [item["emotion"] for item in d["top_emotion_drivers"]])
        self.assertIn("hopeless", [w for words in d["lexicon_matches"].values() for w in words])
        self.assertIn("डर", [w for words in d["lexicon_matches"].values() for w in words])
        self.assertEqual(d["label_disclaimer"], LABEL_DISCLAIMER)

    def test_protective_factors_identification(self) -> None:
        """Positive emotions (joy, optimism, gratitude) are surfaced as protective factors."""
        emotions = {"joy": 0.55, "gratitude": 0.40, "relief": 0.30, "sadness": 0.05}
        evidence = generate_distress_evidence(
            distress_score=0.15,
            distress_level="LOW",
            thresholds=DEFAULT_THRESHOLDS,
            model_version="1.0.0",
            raw_text="Thank you so much, I am feeling much better and hopeful.",
            emotion_probabilities=emotions,
        )
        d = evidence.to_dict()
        self.assertGreater(len(d["protective_factors"]), 0)
        prot_names = [p["emotion"] for p in d["protective_factors"]]
        self.assertIn("joy", prot_names)


class TestDynamicDistressModelInterface(unittest.TestCase):
    """Test suite for DynamicDistressModel interface extensions and artifact handling."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.model = DynamicDistressModel(seed=42)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_predict_distress_with_evidence(self) -> None:
        """predict_distress_with_evidence returns complete payload without breaking core contracts."""
        record = build_synthetic_distress_records(count=1, seed=42)[0]
        out = self.model.predict_distress_with_evidence(
            record=record,
            raw_text="Experiencing overwhelming panic and anxiety.",
            emotion_probabilities={"fear": 0.7, "nervousness": 0.5},
        )

        self.assertIn("distress_score", out)
        self.assertIn("distress_level", out)
        self.assertIn("distress_embedding", out)
        self.assertIn("model_version", out)
        self.assertIn("confidence", out)
        self.assertIn("main_contributors", out)
        self.assertIn("evidence", out)

        self.assertGreaterEqual(out["distress_score"], 0.0)
        self.assertLessEqual(out["distress_score"], 1.0)
        self.assertIn(out["distress_level"], VALID_DISTRESS_LEVELS)
        self.assertEqual(len(out["distress_embedding"]), 128)

        # Embedding norm check (unit sphere)
        norm = math.sqrt(sum(x * x for x in out["distress_embedding"]))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_artifact_export_and_load_roundtrip(self) -> None:
        """Exporting model and loading via load_from_artifact produces identical predictions."""
        export_dir = Path(self.temp_dir) / "exported_distress"
        export_manifest = self.model.export(export_dir)

        self.assertTrue(Path(export_manifest["config"]).exists())
        self.assertTrue(Path(export_manifest["metadata"]).exists())
        self.assertTrue(Path(export_manifest["weights"]).exists())

        # Load into a clean instance via classmethod
        reloaded_model = DynamicDistressModel.load_from_artifact(export_dir)

        test_records = build_synthetic_distress_records(count=5, seed=123)
        for rec in test_records:
            pred_orig = self.model.predict_distress(rec)
            pred_reloaded = reloaded_model.predict_distress(rec)

            self.assertAlmostEqual(pred_orig["distress_score"], pred_reloaded["distress_score"], places=5)
            self.assertEqual(pred_orig["distress_level"], pred_reloaded["distress_level"])
            for o_val, r_val in zip(pred_orig["distress_embedding"], pred_reloaded["distress_embedding"]):
                self.assertAlmostEqual(o_val, r_val, places=5)

    def test_load_from_artifact_missing_file_raises(self) -> None:
        """load_from_artifact raises FileNotFoundError if artifact files are missing."""
        bad_dir = Path(self.temp_dir) / "incomplete_distress"
        bad_dir.mkdir(parents=True, exist_ok=True)
        # Only create config.json
        with open(bad_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump({"model_version": "1.0.0"}, f)

        with self.assertRaises(FileNotFoundError):
            DynamicDistressModel.load_from_artifact(bad_dir)


class TestDistressInferencePipeline(unittest.TestCase):
    """Test suite for high-level DistressInferencePipeline."""

    def setUp(self) -> None:
        self.pipeline = DistressInferencePipeline()

    def test_empty_text_behavior(self) -> None:
        """Empty or whitespace text must safely default to 0.0 distress and LOW level."""
        res = self.pipeline.predict_from_text("")
        self.assertEqual(res["distress_score"], 0.0)
        self.assertEqual(res["distress_level"], "LOW")
        self.assertIn("Empty text input", res["main_contributors"][0])

        res_spaces = self.pipeline.predict_from_text("    ")
        self.assertEqual(res_spaces["distress_score"], 0.0)
        self.assertEqual(res_spaces["distress_level"], "LOW")

    def test_predict_from_text_multilingual(self) -> None:
        """Pipeline handles both English and Hindi distress statements."""
        # English distress
        out_en = self.pipeline.predict_from_text("I feel overwhelmed, panicked, and scared.")
        self.assertGreater(out_en["distress_score"], 0.0)
        self.assertIn(out_en["distress_level"], VALID_DISTRESS_LEVELS)
        self.assertIn("emotion_probabilities", out_en)
        self.assertGreater(len(out_en["evidence"]["lexicon_matches"]), 0)

        # Hindi distress
        out_hi = self.pipeline.predict_from_text("मुझे बहुत घबराहट और डर लग रहा है, बहुत अकेला महसूस हो रहा है")
        self.assertGreater(out_hi["distress_score"], 0.0)
        self.assertIn(out_hi["distress_level"], VALID_DISTRESS_LEVELS)
        self.assertIn("emotion_probabilities", out_hi)
        self.assertGreater(len(out_hi["evidence"]["lexicon_matches"]), 0)

    def test_predict_from_emotions_direct(self) -> None:
        """Pipeline can run directly from precomputed emotion probabilities."""
        emotions = {"fear": 0.85, "sadness": 0.60, "anger": 0.20}
        out = self.pipeline.predict_from_emotions(emotions, raw_text="Precomputed emotions test")
        self.assertGreater(out["distress_score"], 0.0)
        self.assertIn(out["distress_level"], VALID_DISTRESS_LEVELS)
        self.assertEqual(out["evidence"]["distress_level"], out["distress_level"])

    def test_none_preservation_in_features(self) -> None:
        """None values in tabular features are preserved as missingness masks."""
        # Provide partially missing behavioural and engagement features
        b_features = [0.5, None, 0.8, None, 0.2, None, None, 0.9]
        e_features = [None] * ENGAGEMENT_COUNT

        out = self.pipeline.predict_from_text(
            "Feeling anxious today.",
            behavioural_features=b_features,
            engagement_features=e_features,
        )
        self.assertGreaterEqual(out["distress_score"], 0.0)
        self.assertLessEqual(out["distress_score"], 1.0)
        # Should record tabular modality in modality_weights
        self.assertIn("tabular", out["evidence"]["modality_weights"])


class TestClinicalAndRegulatoryBoundaries(unittest.TestCase):
    """Test suite ensuring strict regulatory and clinical boundaries."""

    PROHIBITED_KEYS = [
        "diagnosis",
        "diagnostic_code",
        "phq_score",
        "gad_score",
        "suicide_risk",
        "self_harm_risk",
        "future_risk",
        "treatment_recommendation",
        "prescribe_medication",
    ]

    def test_dynamic_distress_model_boundary_keys(self) -> None:
        """DynamicDistressModel outputs must NEVER contain prohibited clinical concepts."""
        model = DynamicDistressModel()
        record = build_synthetic_distress_records(count=1, seed=999)[0]

        pred = model.predict_distress(record)
        for key in self.PROHIBITED_KEYS:
            self.assertNotIn(key, pred)

        pred_ev = model.predict_distress_with_evidence(record)
        for key in self.PROHIBITED_KEYS:
            self.assertNotIn(key, pred_ev)
            self.assertNotIn(key, pred_ev["evidence"])

    def test_enforce_distress_boundary_helper(self) -> None:
        """enforce_distress_boundary raises ValueError if prohibited keys are introduced."""
        valid_keys = [
            "distress_score",
            "distress_level",
            "distress_embedding",
            "model_version",
        ]
        # Should pass without exception
        for k in valid_keys:
            enforce_distress_boundary(k)

        # Should fail with prohibited key
        for bad_key in ["diagnosis", "phq_score", "future_risk", "treatment_recommendation"]:
            with self.assertRaises(ValueError):
                enforce_distress_boundary(bad_key)


class TestDistressEvaluationMetrics(unittest.TestCase):
    """Test suite verifying distress evaluation metrics calculation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evaluate_distress_computes_regression_and_classification_metrics(self) -> None:
        """evaluate_distress computes MAE, RMSE, Pearson r, and Macro F1."""
        model_dir = "models/distress"
        out_file = str(Path(self.temp_dir) / "eval_out" / "metrics.json")

        report = evaluate_distress(
            model_dir=model_dir,
            output_file=out_file,
            seed=42,
            sample_count=20,
        )

        # Verification
        self.assertIn("mae", report)
        self.assertIn("rmse", report)
        self.assertIn("pearson_correlation", report)
        self.assertIn("macro_f1", report)
        self.assertIn("weighted_f1", report)
        self.assertIn("per_level_metrics", report)
        self.assertTrue(report["clinical_boundaries_enforced"])

        for lvl in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            self.assertIn(lvl, report["per_level_metrics"])
            self.assertIn("precision", report["per_level_metrics"][lvl])
            self.assertIn("recall", report["per_level_metrics"][lvl])
            self.assertIn("f1", report["per_level_metrics"][lvl])

        self.assertTrue(Path(out_file).exists())


if __name__ == "__main__":
    unittest.main()
