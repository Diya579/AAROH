"""Unit tests for Interpretable Logistic Regression Escalation Assessment Model (Slice 3.8 Revision).

Tests:
1. Probability output is bounded in [0.0, 1.0].
2. Confidence score is bounded in [0.0, 1.0] and decoupled from probability.
3. Target horizon is configurable (EscalationConfig.target_horizon_days).
4. Threshold mapping to LOW, MODERATE, HIGH (strictly no CRITICAL).
5. Grounded explainability: factors traceable to real positive feature contributions.
6. Missing evidence does NOT imply LOW risk (produces INSUFFICIENT_DATA / ABSTAINED, not 0.0).
7. Abstention behaviour across INSUFFICIENT_DATA and LOW_CONFIDENCE.
8. Deterministic inference: repeated calls with same input produce identical output.
9. No future leakage: inserting interactions after cutoff time does NOT alter prediction at cutoff.
10. Version metadata and lineage persistence.
11. Export of standard production artifacts.
12. Checkpoint save and load.
13. Calibration metrics generation (Brier score, ROC-AUC, PR-AUC, ECE).
14. Strict clinical boundary enforcement.
15. CLI argument parsing.
"""

from __future__ import annotations

import copy
import datetime
import json
import math
import os
import random
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.ml.contract import ProcessingStatus, ResultSource, RiskLevel
from backend.ml.training.evaluate_escalation_model import (
    compute_brier_score,
    compute_calibration_curve,
    compute_pr_auc,
    compute_roc_auc,
    parse_args as parse_eval_args,
)
from backend.ml.training.models.common import enforce_escalation_boundary
from backend.ml.training.models.escalation.dataset import (
    DEFAULT_TARGET_HORIZON_DAYS,
    DEFAULT_THRESHOLD_LOW_MODERATE,
    DEFAULT_THRESHOLD_MODERATE_HIGH,
    ESCALATION_FEATURE_NAMES,
    LABEL_DISCLAIMER,
    ConfidencePolicyConfig,
    EscalationConfig,
    EscalationInputRecord,
    build_synthetic_escalation_records,
    filter_interactions_by_cutoff,
    split_escalation_records_by_case,
    validate_no_case_leakage,
)
from backend.ml.training.models.escalation.model import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MODEL_VERSION,
    EscalationAssessmentModel,
)
from backend.ml.training.train_escalation import parse_args as parse_train_args


class TestEscalationAssessmentModel(unittest.TestCase):
    """Unit test suite for Slice 3.8 Escalation Assessment Model."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.seed = 42

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_probability_bounded_unit_interval(self) -> None:
        """Verifies predict_proba outputs valid probabilities in [0.0, 1.0] summing to 1.0."""
        model = EscalationAssessmentModel(seed=self.seed)
        records = build_synthetic_escalation_records(case_count=5, seed=self.seed)

        for r in records:
            p0, p1 = model.predict_proba(r)
            self.assertTrue(0.0 <= p0 <= 1.0, f"p0 out of bounds: {p0}")
            self.assertTrue(0.0 <= p1 <= 1.0, f"p1 out of bounds: {p1}")
            self.assertAlmostEqual(p0 + p1, 1.0, places=3)

    def test_confidence_policy_decoupled_from_probability(self) -> None:
        """Verifies confidence is in [0.0, 1.0] and evaluates evidence quality, NOT probability magnitude."""
        model = EscalationAssessmentModel(seed=self.seed)

        # High risk with rich evidence
        rich_high = EscalationInputRecord(
            case_id="CASE-RICH-HIGH",
            interaction_id="INT-01",
            timestamp="2026-01-05T10:00:00Z",
            distress_score=0.90,
            distress_level="CRITICAL",
            trajectory_score=0.85,
            trajectory_label="RAPIDLY_WORSENING",
            text_available=True,
            audio_available=True,
            history_length=10,
            valid_observation_count=8,
            baseline_deviation=0.45,
        )
        # Low risk with rich evidence
        rich_low = EscalationInputRecord(
            case_id="CASE-RICH-LOW",
            interaction_id="INT-01",
            timestamp="2026-01-05T10:00:00Z",
            distress_score=0.10,
            distress_level="LOW",
            trajectory_score=-0.60,
            trajectory_label="IMPROVING",
            text_available=True,
            audio_available=True,
            history_length=10,
            valid_observation_count=8,
            baseline_deviation=0.02,
        )

        out_high = model.predict_escalation(rich_high)
        out_low = model.predict_escalation(rich_low)

        self.assertTrue(out_high["escalation_probability"] > 0.70)
        self.assertTrue(out_low["escalation_probability"] < 0.30)

        # Both rich cases should have high confidence (> 0.80) despite opposite risk levels!
        self.assertTrue(0.0 <= out_high["confidence"] <= 1.0)
        self.assertTrue(0.0 <= out_low["confidence"] <= 1.0)
        self.assertTrue(out_high["confidence"] >= 0.80)
        self.assertTrue(out_low["confidence"] >= 0.80)

    def test_configurable_target_horizon(self) -> None:
        """Verifies target horizon is configurable and exposed in prediction output."""
        cfg_14 = EscalationConfig(target_horizon_days=14)
        model_14 = EscalationAssessmentModel(config=cfg_14, seed=self.seed)
        rec = build_synthetic_escalation_records(case_count=1, seed=self.seed)[0]

        res_14 = model_14.predict_escalation(rec)
        self.assertEqual(res_14["target_horizon_days"], 14)

        # Config validation
        with self.assertRaises(ValueError):
            EscalationConfig(target_horizon_days=0)

    def test_threshold_mapping_low_moderate_high(self) -> None:
        """Verifies mapping to LOW, MODERATE, HIGH thresholds without CRITICAL."""
        cfg = EscalationConfig(threshold_low_moderate=0.40, threshold_moderate_high=0.75)
        self.assertEqual(cfg.get_risk_level(0.20), RiskLevel.LOW)
        self.assertEqual(cfg.get_risk_level(0.399), RiskLevel.LOW)
        self.assertEqual(cfg.get_risk_level(0.40), RiskLevel.MODERATE)
        self.assertEqual(cfg.get_risk_level(0.749), RiskLevel.MODERATE)
        self.assertEqual(cfg.get_risk_level(0.75), RiskLevel.HIGH)
        self.assertEqual(cfg.get_risk_level(0.99), RiskLevel.HIGH)

        # Verify no CRITICAL exists in RiskLevel
        self.assertNotIn("CRITICAL", [m.value for m in RiskLevel])

    def test_grounded_explainability(self) -> None:
        """Verifies explanations are traceable to real positive feature contributions."""
        model = EscalationAssessmentModel(seed=self.seed)
        high_risk_record = EscalationInputRecord(
            case_id="CASE-EXP",
            interaction_id="INT-EXP",
            timestamp="2026-01-05T10:00:00Z",
            distress_score=0.85,
            distress_level="HIGH",
            trajectory_score=0.70,
            trajectory_label="RAPIDLY_WORSENING",
            baseline_deviation=0.40,
            help_requested=1.0,
            engagement_drop=0.50,
            valid_observation_count=7,
        )
        res = model.predict_escalation(high_risk_record)
        explanation = res["explanation"]
        self.assertIn("factors", explanation)
        self.assertIn("trend", explanation)
        self.assertIn("baseline_deviation", explanation)
        self.assertIn("model_version", explanation)

        factors = explanation["factors"]
        self.assertTrue(len(factors) > 0)
        # Check that factors reference actual drivers present in record
        self.assertTrue(
            any("trajectory" in f.lower() or "distress" in f.lower() or "help" in f.lower() for f in factors)
        )

    def test_missing_evidence_does_not_imply_low_risk(self) -> None:
        """Verifies that missing evidence causes abstention rather than fabricating LOW risk or 0.0 probability."""
        model = EscalationAssessmentModel(seed=self.seed)
        # Record with empty / missing evidence
        starved_record = EscalationInputRecord(
            case_id="CASE-STARVED",
            interaction_id="INT-STARVED",
            timestamp="2026-01-01T10:00:00Z",
            distress_score=0.0,
            distress_level="LOW",
            text_available=False,
            audio_available=False,
            valid_observation_count=0,
            history_length=0,
        )
        res = model.predict_escalation(starved_record)

        # Must NOT return probability = 0.0 or risk_level = LOW
        self.assertIsNone(res["escalation_probability"])
        self.assertIsNone(res["risk_level"])
        self.assertIn(res["status"], (ProcessingStatus.INSUFFICIENT_DATA.value, ProcessingStatus.ABSTAINED.value))
        self.assertEqual(res["source"], ResultSource.INSUFFICIENT_EVIDENCE.value)

    def test_abstention_behaviour(self) -> None:
        """Verifies abstention returns documented statuses without fabricated scores."""
        model = EscalationAssessmentModel(seed=self.seed)
        sparse_record = EscalationInputRecord(
            case_id="CASE-SPARSE",
            interaction_id="INT-SPARSE",
            timestamp="2026-01-01T10:00:00Z",
            distress_score=0.0,
            distress_level="LOW",
            valid_observation_count=1,
            text_available=False,
            audio_available=False,
        )
        out = model.predict_escalation(sparse_record)
        self.assertEqual(out["status"], ProcessingStatus.INSUFFICIENT_DATA.value)
        self.assertIsNone(out["escalation_probability"])

    def test_deterministic_inference(self) -> None:
        """Verifies inference produces identical results for identical inputs."""
        model = EscalationAssessmentModel(seed=self.seed)
        rec = build_synthetic_escalation_records(case_count=1, seed=self.seed)[0]

        res1 = model.predict_escalation(rec, prediction_date="2026-01-01")
        res2 = model.predict_escalation(rec, prediction_date="2026-01-01")

        self.assertEqual(res1["escalation_probability"], res2["escalation_probability"])
        self.assertEqual(res1["confidence"], res2["confidence"])
        self.assertEqual(res1["risk_level"], res2["risk_level"])
        self.assertEqual(res1["explanation"]["factors"], res2["explanation"]["factors"])

    def test_no_future_leakage(self) -> None:
        """Temporal Leakage Test:
        Prediction at cutoff time T MUST remain strictly identical after future interactions (T + delta) are added.
        """
        model = EscalationAssessmentModel(seed=self.seed)
        cutoff_time = "2026-01-10T12:00:00Z"

        # Past interaction
        past_record = EscalationInputRecord(
            case_id="CASE-TEMPORAL",
            interaction_id="INT-01",
            timestamp="2026-01-08T10:00:00Z",
            distress_score=0.45,
            distress_level="MODERATE",
            trajectory_score=0.20,
            trajectory_label="WORSENING",
            valid_observation_count=6,
        )
        # Assessment at time T
        history_before = [past_record]
        valid_before = filter_interactions_by_cutoff(history_before, cutoff_time)
        pred_before = model.predict_escalation(valid_before[-1], prediction_date=cutoff_time[:10])

        # Insert future interaction at T + 3 days
        future_record = EscalationInputRecord(
            case_id="CASE-TEMPORAL",
            interaction_id="INT-02",
            timestamp="2026-01-13T10:00:00Z",  # Future!
            distress_score=0.95,
            distress_level="CRITICAL",
            trajectory_score=0.90,
            trajectory_label="RAPIDLY_WORSENING",
            valid_observation_count=6,
        )
        history_after = [past_record, future_record]
        valid_after = filter_interactions_by_cutoff(history_after, cutoff_time)

        # Assessment at cutoff T again
        pred_after = model.predict_escalation(valid_after[-1], prediction_date=cutoff_time[:10])

        self.assertEqual(len(valid_before), len(valid_after))
        self.assertEqual(pred_before["escalation_probability"], pred_after["escalation_probability"])
        self.assertEqual(pred_before["risk_level"], pred_after["risk_level"])
        self.assertEqual(pred_before["confidence"], pred_after["confidence"])

    def test_versioning_and_metadata_persistence(self) -> None:
        """Verifies metadata includes model_version, dataset_version, target_horizon_days, upstream_models."""
        model = EscalationAssessmentModel(seed=self.seed)
        export_dir = Path(self.temp_dir) / "exported_meta"
        artifacts = model.export(export_dir)

        with open(artifacts["metadata"], "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.assertEqual(meta["model_version"], DEFAULT_MODEL_VERSION)
        self.assertEqual(meta["dataset_version"], "3.8.0")
        self.assertEqual(meta["target_horizon_days"], DEFAULT_TARGET_HORIZON_DAYS)
        self.assertIn("upstream_models", meta)
        self.assertEqual(meta["upstream_models"]["fusion"], "aaroh-fusion-v1")
        self.assertEqual(meta["upstream_models"]["distress"], "aaroh-distress-v1")
        self.assertEqual(meta["upstream_models"]["trajectory"], "aaroh-trajectory-v1")

    def test_checkpoint_save_and_load(self) -> None:
        """Verifies checkpoint saving and exact parameter restoration."""
        model = EscalationAssessmentModel(seed=self.seed)
        chk_file = Path(self.temp_dir) / "checkpoint.pt"

        records = build_synthetic_escalation_records(case_count=3, seed=self.seed)
        pred_before = model.predict_escalation(records[0])

        model.save_checkpoint(chk_file, metrics={"loss": 0.25})
        self.assertTrue(chk_file.exists())

        reloaded = EscalationAssessmentModel(seed=self.seed + 10)
        reloaded.load_checkpoint(chk_file)

        pred_after = reloaded.predict_escalation(records[0])
        self.assertEqual(pred_before["escalation_probability"], pred_after["escalation_probability"])
        self.assertEqual(pred_before["confidence"], pred_after["confidence"])
        self.assertEqual(pred_before["risk_level"], pred_after["risk_level"])

    def test_calibration_metrics_generation(self) -> None:
        """Verifies Brier score, ROC-AUC, PR-AUC, and calibration bins computation."""
        y_true = [0, 0, 1, 1, 0, 1, 1, 0]
        y_prob = [0.15, 0.25, 0.85, 0.70, 0.30, 0.90, 0.65, 0.20]

        brier = compute_brier_score(y_true, y_prob)
        self.assertTrue(0.0 <= brier <= 1.0)

        roc_auc = compute_roc_auc(y_true, y_prob)
        self.assertTrue(0.50 <= roc_auc <= 1.0)

        pr_auc = compute_pr_auc(y_true, y_prob)
        self.assertTrue(0.0 <= pr_auc <= 1.0)

        calib = compute_calibration_curve(y_true, y_prob, n_bins=5)
        self.assertIn("expected_calibration_error", calib)
        self.assertIn("bins", calib)
        self.assertEqual(len(calib["bins"]), 5)

    def test_clinical_boundary_enforcement(self) -> None:
        """Verifies clinical boundary rejects psychiatric diagnosis and medical advice."""
        forbidden = [
            "clinical_diagnosis",
            "medical_diagnosis",
            "psychiatric_diagnosis",
            "depression",
            "anxiety",
            "ptsd",
            "suicide",
            "suicide_risk",
            "treatment_recommendation",
            "medication",
            "prescription",
            "intervention_plan",
            "phq9",
            "gad7",
            "critical",
        ]
        for term in forbidden:
            with self.assertRaises(ValueError):
                enforce_escalation_boundary(term)

        allowed = [
            "case_id",
            "prediction_date",
            "escalation_probability",
            "target_horizon_days",
            "confidence",
            "risk_level",
            "explanation",
            "factors",
            "trend",
            "baseline_deviation",
            "model_version",
            "LOW",
            "MODERATE",
            "HIGH",
        ]
        for term in allowed:
            enforce_escalation_boundary(term)

    def test_cli_argument_parsing(self) -> None:
        """Verifies CLI argument parsers for training and evaluation."""
        train_args = parse_train_args(["--smoke-test", "--epochs", "50", "--target-horizon-days", "14"])
        self.assertTrue(train_args.smoke_test)
        self.assertEqual(train_args.epochs, 50)
        self.assertEqual(train_args.target_horizon_days, 14)

        eval_args = parse_eval_args(["--case-count", "30", "--seed", "123"])
        self.assertEqual(eval_args.case_count, 30)
        self.assertEqual(eval_args.seed, 123)

    def test_temporal_leakage_shuffled_future_invariance(self) -> None:
        """Procedure:
        1. Generate prediction at cutoff T.
        2. Append multiple future interactions (> T).
        3. Shuffle the ordering of only those future interactions.
        4. Generate prediction again using cutoff T.
        Prediction must remain strictly identical.
        """
        model = EscalationAssessmentModel(seed=self.seed)
        cutoff_t = "2026-01-05T12:00:00Z"

        # Historical interactions up to cutoff T
        int_0 = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-00",
            timestamp="2026-01-01T10:00:00Z",
            distress_score=0.40,
            distress_level="MODERATE",
            trajectory_score=0.20,
            trajectory_label="STABLE",
            valid_observation_count=3,
            history_length=1,
        )
        int_1 = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-01",
            timestamp="2026-01-03T10:00:00Z",
            distress_score=0.60,
            distress_level="MODERATE",
            trajectory_score=0.40,
            trajectory_label="WORSENING",
            valid_observation_count=4,
            history_length=2,
        )
        int_2 = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-02",
            timestamp="2026-01-05T10:00:00Z",
            distress_score=0.75,
            distress_level="HIGH",
            trajectory_score=0.65,
            trajectory_label="WORSENING",
            valid_observation_count=5,
            history_length=3,
        )
        historical = [int_0, int_1, int_2]

        # Prediction at cutoff T on filtered historical interactions
        valid_at_t = filter_interactions_by_cutoff(historical, cutoff_timestamp=cutoff_t)
        self.assertEqual(len(valid_at_t), 3)
        pred_1 = model.predict_escalation(valid_at_t[-1])

        # Multiple future interactions (> T) with extreme distress / varying values
        future_a = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-03",
            timestamp="2026-01-08T10:00:00Z",
            distress_score=0.95,
            distress_level="CRITICAL",
            trajectory_score=0.90,
            trajectory_label="RAPIDLY_WORSENING",
            valid_observation_count=6,
            history_length=4,
        )
        future_b = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-04",
            timestamp="2026-01-12T10:00:00Z",
            distress_score=0.10,
            distress_level="LOW",
            trajectory_score=-0.70,
            trajectory_label="IMPROVING",
            valid_observation_count=7,
            history_length=5,
        )
        future_c = EscalationInputRecord(
            case_id="CASE-LEAK-SHUFFLE",
            interaction_id="INT-05",
            timestamp="2026-01-15T10:00:00Z",
            distress_score=0.88,
            distress_level="HIGH",
            trajectory_score=0.75,
            trajectory_label="RAPIDLY_WORSENING",
            valid_observation_count=8,
            history_length=6,
        )
        future_interactions = [future_a, future_b, future_c]

        # Shuffle future interactions multiple times and test invariance
        rng = copy.copy(random.Random(self.seed))
        for _ in range(5):
            shuffled_future = list(future_interactions)
            rng.shuffle(shuffled_future)
            all_interactions = historical + shuffled_future

            valid_filtered = filter_interactions_by_cutoff(all_interactions, cutoff_timestamp=cutoff_t)
            self.assertEqual(len(valid_filtered), 3)
            self.assertEqual([r.interaction_id for r in valid_filtered], ["INT-00", "INT-01", "INT-02"])

            pred_2 = model.predict_escalation(valid_filtered[-1])

            self.assertEqual(pred_1["escalation_probability"], pred_2["escalation_probability"])
            self.assertEqual(pred_1["risk_level"], pred_2["risk_level"])
            self.assertEqual(pred_1["confidence"], pred_2["confidence"])
            self.assertEqual(pred_1["explanation"], pred_2["explanation"])

    def test_raw_feature_contributions_table(self) -> None:
        """Verifies raw feature contribution table is preserved, complete, and mathematically exact."""
        model = EscalationAssessmentModel(seed=self.seed)
        rec = build_synthetic_escalation_records(case_count=1, seed=self.seed)[0]

        res = model.predict_escalation(rec)
        table = model.get_last_feature_contributions()

        self.assertIsInstance(table, list)
        self.assertEqual(len(table), len(model.feature_names))

        for entry in table:
            self.assertIn("feature", entry)
            self.assertIn("value", entry)
            self.assertIn("coefficient", entry)
            self.assertIn("contribution", entry)
            expected_contrib = round(entry["value"] * entry["coefficient"], 4)
            self.assertAlmostEqual(entry["contribution"], expected_contrib, places=3)

    def test_explainability_deep_validation(self) -> None:
        """Verifies:
        - Every explanation factor corresponds to an actual input feature
        - Every explanation factor originates from computed contribution table
        - Prohibited clinical terminology never appears
        - No explanation references unavailable modalities
        - Explanations remain deterministic for identical inputs
        """
        model = EscalationAssessmentModel(seed=self.seed)

        # 1. Prohibited clinical terms check
        prohibited_clinical_terms = [
            "depression",
            "depressive",
            "anxiety",
            "ptsd",
            "suicide",
            "suicidal",
            "phq",
            "gad",
            "diagnosis",
            "diagnostic",
            "treatment",
            "medication",
            "therapy",
            "antidepressant",
            "psychiatric",
            "prescription",
        ]

        records = build_synthetic_escalation_records(case_count=10, seed=self.seed)
        for r in records:
            res = model.predict_escalation(r)
            factors = res["explanation"]["factors"]
            table = model.get_last_feature_contributions()
            positive_table_features = {
                e["feature"] for e in table if e["contribution"] > 0.05 and not e["feature"].endswith("_missing")
            }

            for factor in factors:
                factor_lower = factor.lower()
                # Check prohibited terms
                for bad_term in prohibited_clinical_terms:
                    self.assertNotIn(bad_term, factor_lower, f"Prohibited term '{bad_term}' found in factor: '{factor}'")

                # If factor is a non-default positive driver factor, check it originated from table
                if "worsening distress trajectory" in factor_lower:
                    self.assertTrue(
                        any(f in positive_table_features for f in ("trajectory_is_rapidly_worsening", "trajectory_is_worsening", "trajectory_score"))
                    )
                elif "acute distress state" in factor_lower:
                    self.assertTrue(
                        any(f in positive_table_features for f in ("distress_is_high_or_critical", "distress_score"))
                    )

        # 2. Unavailable modalities: ensure no factor references unavailable modalities
        rec_no_modalities = EscalationInputRecord(
            case_id="CASE-NO-MOD",
            interaction_id="INT-NO-MOD",
            timestamp="2026-01-05T10:00:00Z",
            distress_score=0.85,
            distress_level="HIGH",
            trajectory_score=0.60,
            trajectory_label="WORSENING",
            text_available=False,
            audio_available=False,
            valid_observation_count=4,
            history_length=3,
        )
        res_no_mod = model.predict_escalation(rec_no_modalities)
        if res_no_mod["status"] != ProcessingStatus.INSUFFICIENT_DATA.value:
            for f in res_no_mod["explanation"]["factors"]:
                self.assertNotIn("audio", f.lower())
                self.assertNotIn("speech", f.lower())
                self.assertNotIn("voice", f.lower())
                self.assertNotIn("acoustic", f.lower())

        # 3. Determinism check: repeated calls with identical input produce identical outputs
        rec_det = records[0]
        ref_res = model.predict_escalation(rec_det, prediction_date="2026-01-05")
        for _ in range(10):
            rep_res = model.predict_escalation(rec_det, prediction_date="2026-01-05")
            self.assertEqual(ref_res["escalation_probability"], rep_res["escalation_probability"])
            self.assertEqual(ref_res["confidence"], rep_res["confidence"])
            self.assertEqual(ref_res["risk_level"], rep_res["risk_level"])
            self.assertEqual(ref_res["explanation"]["factors"], rep_res["explanation"]["factors"])

    def test_versioned_confidence_policy_and_calibration_metadata(self) -> None:
        """Verifies ConfidencePolicyConfig versioning and metadata lineage."""
        custom_policy = ConfidencePolicyConfig(
            version="1.5",
            observation_weight=0.35,
            text_weight=0.20,
            audio_weight=0.15,
            missingness_weight=0.15,
            uncertainty_weight=0.15,
            minimum_history=2,
            minimum_modalities=1,
            minimum_confidence=0.25,
        )
        config = EscalationConfig(confidence_policy=custom_policy, target_horizon_days=7)
        model = EscalationAssessmentModel(config=config, seed=self.seed)

        export_dir = Path(self.temp_dir) / "exported_model"
        model.export(export_dir)

        # Check config.json
        with open(export_dir / "config.json", "r", encoding="utf-8") as f:
            cfg_json = json.load(f)
        self.assertIn("confidence_policy", cfg_json)
        self.assertEqual(cfg_json["confidence_policy"]["version"], "1.5")
        self.assertIn("calibration", cfg_json)
        self.assertEqual(cfg_json["calibration"]["method"], "logistic_sigmoid")
        self.assertEqual(cfg_json["calibration"]["version"], "1.0")

        # Check metadata.json
        with open(export_dir / "metadata.json", "r", encoding="utf-8") as f:
            meta_json = json.load(f)
        self.assertIn("confidence_policy", meta_json)
        self.assertEqual(meta_json["confidence_policy"]["version"], "1.5")
        self.assertIn("calibration", meta_json)
        self.assertEqual(meta_json["calibration"]["method"], "logistic_sigmoid")
        self.assertEqual(meta_json["calibration"]["version"], "1.0")
        self.assertIn("upstream_models", meta_json)
        self.assertEqual(meta_json["upstream_models"]["fusion"], "aaroh-fusion-v1")
        self.assertEqual(meta_json["upstream_models"]["distress"], "aaroh-distress-v1")
        self.assertEqual(meta_json["upstream_models"]["trajectory"], "aaroh-trajectory-v1")
        self.assertEqual(meta_json["feature_schema_version"], "1.0")
        self.assertEqual(meta_json["dataset_version"], "3.8.0")
        self.assertIn("training_date", meta_json)


if __name__ == "__main__":
    unittest.main()
