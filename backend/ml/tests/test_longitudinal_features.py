"""Comprehensive unit tests for Longitudinal Feature Extraction (Slice 2.5).

Verifies:
- Centralized definitions, enums, configurable config (User Modification 1)
- Rich explainability evidence metadata (User Modification 2)
- Strict preservation of the invariant None != 0 and UNKNOWN trend for insufficient history (User Modification 3)
- Rate of change (velocity), acceleration, and volatility
- Sustained distress tracking
- Determinism, type checking, batch processing, and raw input helpers
"""

import unittest

from backend.ml.features.longitudinal import (
    LongitudinalFeatureExtractor,
    compute_interaction_distress,
    extract_longitudinal_features,
    extract_longitudinal_features_batch,
)
from backend.ml.features.longitudinal_definitions import (
    LongitudinalConfig,
    LongitudinalMetric,
    LongitudinalTrend,
    classify_longitudinal_trend,
)
from backend.ml.features.types import (
    LongitudinalEvidence,
    LongitudinalFeatures,
)
from backend.ml.preprocessing import preprocess_interaction


class TestLongitudinalFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = LongitudinalFeatureExtractor()

    def test_centralized_definitions_and_config(self) -> None:
        """Verifies centralized single source of truth for definitions, enums, and config (User Modification 1)."""
        # Verify enum contents
        self.assertEqual(LongitudinalTrend.UNKNOWN.value, "UNKNOWN")
        self.assertEqual(LongitudinalTrend.STABLE.value, "STABLE")
        self.assertEqual(LongitudinalTrend.IMPROVING.value, "IMPROVING")
        self.assertEqual(LongitudinalTrend.WORSENING.value, "WORSENING")
        self.assertEqual(LongitudinalTrend.RAPIDLY_IMPROVING.value, "RAPIDLY_IMPROVING")
        self.assertEqual(LongitudinalTrend.RAPIDLY_WORSENING.value, "RAPIDLY_WORSENING")

        # Verify config validation
        default_cfg = LongitudinalConfig()
        self.assertEqual(default_cfg.min_observations_for_trend, 2)
        self.assertEqual(default_cfg.rapid_shift_threshold, 0.35)
        self.assertEqual(default_cfg.notable_shift_threshold, 0.20)
        self.assertEqual(default_cfg.high_distress_threshold, 0.65)

        # Invalid bounds raise ValueError
        with self.assertRaises(ValueError):
            LongitudinalConfig(min_observations_for_trend=0)
        with self.assertRaises(ValueError):
            LongitudinalConfig(rapid_shift_threshold=-0.1)
        with self.assertRaises(ValueError):
            LongitudinalConfig(notable_shift_threshold=0.50, rapid_shift_threshold=0.30)
        with self.assertRaises(ValueError):
            LongitudinalConfig(rapid_velocity_threshold=-0.01)

        # Test centralized classifier directly
        trend_unknown = classify_longitudinal_trend(
            delta_previous=0.5, delta_baseline=0.5, velocity=0.1, observation_count=1
        )
        self.assertEqual(trend_unknown, LongitudinalTrend.UNKNOWN)

        trend_rapid_worse = classify_longitudinal_trend(
            delta_previous=0.40, delta_baseline=0.40, velocity=0.06, observation_count=2
        )
        self.assertEqual(trend_rapid_worse, LongitudinalTrend.RAPIDLY_WORSENING)

        trend_rapid_impr = classify_longitudinal_trend(
            delta_previous=-0.40, delta_baseline=-0.40, velocity=-0.06, observation_count=2
        )
        self.assertEqual(trend_rapid_impr, LongitudinalTrend.RAPIDLY_IMPROVING)

    def test_single_interaction_insufficient_history(self) -> None:
        """Verifies that single interaction preserves None != 0 and yields UNKNOWN trend (User Modification 3)."""
        raw = {
            "case_id": "CASE-100",
            "interaction_date": "2026-09-01",
            "fear_level": 4,
            "safety_response": 2,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction, history=[])

        self.assertTrue(features.longitudinal_available)
        self.assertEqual(features.observation_count, 1)
        self.assertEqual(features.history_span_days, 0)
        self.assertIsNotNone(features.current_distress)

        # Missing baseline or history must strictly be None, NEVER 0.0 (User Modification 3)
        self.assertIsNone(features.baseline_distress)
        self.assertIsNone(features.previous_distress)
        self.assertIsNone(features.delta_from_baseline)
        self.assertIsNone(features.delta_from_previous)
        self.assertIsNone(features.distress_velocity)
        self.assertIsNone(features.distress_acceleration)
        self.assertIsNone(features.distress_volatility)

        # Trend must explicitly be UNKNOWN (User Modification 3)
        self.assertEqual(features.longitudinal_trend, "UNKNOWN")
        self.assertIsNotNone(features.evidence)
        self.assertEqual(features.evidence.trend, "UNKNOWN")

    def test_two_interactions_trajectory(self) -> None:
        """Verifies longitudinal feature extraction across two interactions."""
        h1 = preprocess_interaction({
            "case_id": "CASE-101",
            "interaction_date": "2026-08-25",
            "fear_level": 1,
            "safety_response": 5,
            "sleep_disruption": 1,
            "social_support": 5,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-101",
            "interaction_date": "2026-09-01",
            "fear_level": 3,
            "safety_response": 3,
            "sleep_disruption": 3,
            "social_support": 3,
        })

        features = self.extractor.extract(cur, history=[h1])

        self.assertTrue(features.longitudinal_available)
        self.assertEqual(features.observation_count, 2)
        self.assertEqual(features.history_span_days, 7)
        self.assertAlmostEqual(features.baseline_distress, 0.0, places=2)
        self.assertAlmostEqual(features.current_distress, 0.5, places=2)
        self.assertAlmostEqual(features.delta_from_baseline, 0.5, places=2)
        self.assertAlmostEqual(features.delta_from_previous, 0.5, places=2)
        self.assertIsNotNone(features.distress_velocity)
        self.assertGreater(features.distress_velocity, 0)

        # Acceleration requires at least 3 points, so must remain None (None != 0)
        self.assertIsNone(features.distress_acceleration)

        # Delta is >= 0.35, so trend should be RAPIDLY_WORSENING
        self.assertEqual(features.longitudinal_trend, "RAPIDLY_WORSENING")

    def test_rapid_improving_trajectory(self) -> None:
        """Verifies rapid improvement detection when distress drops sharply."""
        h1 = preprocess_interaction({
            "case_id": "CASE-102",
            "interaction_date": "2026-08-25",
            "fear_level": 5,
            "safety_response": 1,
            "sleep_disruption": 5,
            "social_support": 1,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-102",
            "interaction_date": "2026-09-01",
            "fear_level": 1,
            "safety_response": 5,
            "sleep_disruption": 1,
            "social_support": 5,
        })

        features = self.extractor.extract(cur, history=[h1])
        self.assertEqual(features.longitudinal_trend, "RAPIDLY_IMPROVING")
        self.assertLess(features.delta_from_baseline, -0.35)
        self.assertIn("Rapidly improving distress trajectory detected", features.evidence.contributing_factors)

    def test_multi_interaction_velocity_acceleration_volatility(self) -> None:
        """Verifies velocity, acceleration, volatility, and extremes over multiple points."""
        h1 = preprocess_interaction({
            "case_id": "CASE-103",
            "interaction_date": "2026-08-10",
            "fear_level": 1,
            "safety_response": 5,
        })
        h2 = preprocess_interaction({
            "case_id": "CASE-103",
            "interaction_date": "2026-08-17",
            "fear_level": 2,
            "safety_response": 4,
        })
        h3 = preprocess_interaction({
            "case_id": "CASE-103",
            "interaction_date": "2026-08-24",
            "fear_level": 3,
            "safety_response": 3,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-103",
            "interaction_date": "2026-08-31",
            "fear_level": 5,
            "safety_response": 1,
        })

        features = self.extractor.extract(cur, history=[h1, h2, h3])

        self.assertEqual(features.observation_count, 4)
        self.assertEqual(features.history_span_days, 21)
        self.assertIsNotNone(features.distress_velocity)
        self.assertIsNotNone(features.distress_acceleration)
        self.assertIsNotNone(features.distress_volatility)
        self.assertAlmostEqual(features.peak_distress, 1.0, places=2)
        self.assertAlmostEqual(features.trough_distress, 0.0, places=2)

    def test_sustained_high_distress_count(self) -> None:
        """Verifies sustained high distress tracking and explainability factor generation."""
        # 3 consecutive severe distress interactions
        h1 = preprocess_interaction({
            "case_id": "CASE-104",
            "interaction_date": "2026-08-15",
            "fear_level": 5,
            "safety_response": 1,
        })
        h2 = preprocess_interaction({
            "case_id": "CASE-104",
            "interaction_date": "2026-08-22",
            "fear_level": 5,
            "safety_response": 1,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-104",
            "interaction_date": "2026-08-29",
            "fear_level": 4,
            "safety_response": 1,
        })

        features = self.extractor.extract(cur, history=[h1, h2])

        self.assertEqual(features.sustained_distress_count, 3)
        self.assertIn(
            "Sustained high distress across 3 consecutive interactions",
            features.evidence.contributing_factors,
        )

    def test_preserves_none_invariant_for_missing_values(self) -> None:
        """Verifies that completely missing distress information preserves None != 0."""
        cur = preprocess_interaction({
            "case_id": "CASE-105",
            "interaction_date": "2026-09-01",
        })
        features = self.extractor.extract(cur, history=[])

        self.assertFalse(features.longitudinal_available)
        self.assertIsNone(features.current_distress)
        self.assertIsNone(features.baseline_distress)
        self.assertIsNone(features.previous_distress)
        self.assertIsNone(features.delta_from_baseline)
        self.assertIsNone(features.distress_velocity)
        self.assertEqual(features.longitudinal_trend, "UNKNOWN")

    def test_explainability_evidence_metadata(self) -> None:
        """Verifies structured explainability metadata capture (User Modification 2)."""
        h1 = preprocess_interaction({
            "case_id": "CASE-106",
            "interaction_date": "2026-08-20",
            "fear_level": 2,
            "safety_response": 4,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-106",
            "interaction_date": "2026-08-27",
            "fear_level": 4,
            "safety_response": 2,
        })

        features = self.extractor.extract(cur, history=[h1])
        evidence = features.evidence

        self.assertIsInstance(evidence, LongitudinalEvidence)
        self.assertEqual(evidence.observation_count, 2)
        self.assertEqual(evidence.timestamps, ("2026-08-20", "2026-08-27"))
        self.assertEqual(len(evidence.distress_scores), 2)
        self.assertIsNotNone(evidence.baseline_distress)
        self.assertIsNotNone(evidence.delta_from_baseline)
        self.assertTrue(len(evidence.contributing_factors) > 0)

        # Verify serialization
        ev_dict = evidence.to_dict()
        self.assertEqual(ev_dict["observation_count"], 2)
        self.assertEqual(ev_dict["trend"], features.longitudinal_trend)

        feat_dict = features.to_feature_dict()
        self.assertEqual(feat_dict["longitudinal_available"], 1)
        self.assertEqual(feat_dict["longitudinal_observation_count"], 2)
        self.assertIn("longitudinal_delta_from_baseline", feat_dict)

    def test_configurable_thresholds_override(self) -> None:
        """Verifies custom LongitudinalConfig alters classifications without code changes (User Modification 1)."""
        h1 = preprocess_interaction({
            "case_id": "CASE-107",
            "interaction_date": "2026-08-20",
            "fear_level": 2,
            "safety_response": 4,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-107",
            "interaction_date": "2026-08-27",
            "fear_level": 3,
            "safety_response": 3,
        })
        # Delta is ~ 0.25

        # With default config (rapid_shift=0.35, notable=0.20): delta 0.25 is WORSENING
        feat_default = self.extractor.extract(cur, history=[h1])
        self.assertEqual(feat_default.longitudinal_trend, "WORSENING")

        # With custom tighter config (rapid_shift=0.20): delta 0.25 becomes RAPIDLY_WORSENING
        custom_cfg = LongitudinalConfig(rapid_shift_threshold=0.20, notable_shift_threshold=0.10)
        feat_custom = self.extractor.extract(cur, history=[h1], config=custom_cfg)
        self.assertEqual(feat_custom.longitudinal_trend, "RAPIDLY_WORSENING")

    def test_deterministic_execution(self) -> None:
        """Verifies extraction produces identical results across repeated calls."""
        h1 = preprocess_interaction({
            "case_id": "CASE-108",
            "interaction_date": "2026-08-20",
            "fear_level": 2,
            "safety_response": 4,
        })
        cur = preprocess_interaction({
            "case_id": "CASE-108",
            "interaction_date": "2026-08-27",
            "fear_level": 4,
            "safety_response": 2,
        })

        f1 = self.extractor.extract(cur, history=[h1])
        f2 = self.extractor.extract(cur, history=[h1])

        self.assertEqual(f1, f2)
        self.assertEqual(f1.to_dict(), f2.to_dict())
        self.assertEqual(f1.to_feature_dict(), f2.to_feature_dict())

    def test_batch_extraction(self) -> None:
        """Verifies batch processing."""
        p1 = preprocess_interaction({"case_id": "C1", "interaction_date": "2026-09-01", "fear_level": 3})
        p2 = preprocess_interaction({"case_id": "C2", "interaction_date": "2026-09-01", "fear_level": 5})

        batch_results = extract_longitudinal_features_batch([(p1, None), (p2, None)])
        self.assertEqual(len(batch_results), 2)
        self.assertEqual(batch_results[0].observation_count, 1)
        self.assertEqual(batch_results[1].observation_count, 1)

    def test_extract_from_raw_convenience(self) -> None:
        """Verifies convenience method with raw dictionaries."""
        features = self.extractor.extract_from_raw(
            current_raw={"case_id": "CASE-RAW", "interaction_date": "2026-09-02", "fear_level": 4},
            history_raw=[{"case_id": "CASE-RAW", "interaction_date": "2026-08-25", "fear_level": 2}],
        )
        self.assertEqual(features.observation_count, 2)
        self.assertEqual(features.longitudinal_trend, "RAPIDLY_WORSENING")

    def test_rejects_unpreprocessed_direct_inputs(self) -> None:
        """Verifies that direct invocation with un-preprocessed payloads raises TypeError."""
        with self.assertRaises(TypeError):
            self.extractor.extract({"case_id": "RAW-DICT"})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
