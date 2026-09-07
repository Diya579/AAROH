"""Comprehensive unit tests for Behavioural Feature Extraction (Slice 2.3).

Tests:
1. Standard single interaction behavioural feature extraction.
2. Inverted scale correctness (safety and social support).
3. Direct scale correctness (fear and sleep disruption).
4. Longitudinal history processing (deltas from previous and baseline, observation count).
5. Strict None != 0 invariant (missing ratings and absent history remain None).
6. Explainability evidence metadata (User Modification 2).
7. Centralized behavioural definitions (User Modification 1).
8. Determinism (repeated execution returns identical features).
9. Batch processing.
10. Strict type safety: rejects un-preprocessed inputs.
"""

from __future__ import annotations

import unittest

from backend.ml.features import (
    ALL_BEHAVIOURAL_INPUT_FIELDS,
    MAX_LIKERT_RATING,
    MIN_LIKERT_RATING,
    BehaviouralEvidence,
    BehaviouralFeatureExtractor,
    BehaviouralFeatures,
    BehaviouralMetric,
    extract_behavioural_features,
    extract_behavioural_features_batch,
    normalize_likert_rating,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


class TestBehaviouralFeatureExtraction(unittest.TestCase):
    """Unit test suite for Slice 2.3 Behavioural Feature Extraction."""

    def setUp(self):
        self.extractor = BehaviouralFeatureExtractor()

    def test_centralized_definitions(self):
        """User Modification 1: Centralized definitions are the single source of truth."""
        self.assertEqual(MIN_LIKERT_RATING, 1)
        self.assertEqual(MAX_LIKERT_RATING, 5)
        self.assertEqual(BehaviouralMetric.SAFETY_DISTRESS.value, "safety_distress")
        self.assertEqual(BehaviouralMetric.FEAR_INTENSITY.value, "fear_intensity")
        self.assertIn("safety_response", ALL_BEHAVIOURAL_INPUT_FIELDS)

        # Normalization helper
        self.assertEqual(normalize_likert_rating(1, invert=False), 0.0)
        self.assertEqual(normalize_likert_rating(5, invert=False), 1.0)
        self.assertEqual(normalize_likert_rating(3, invert=False), 0.5)

        # Inversion helper (1 -> 1.0, 5 -> 0.0)
        self.assertEqual(normalize_likert_rating(1, invert=True), 1.0)
        self.assertEqual(normalize_likert_rating(5, invert=True), 0.0)
        self.assertEqual(normalize_likert_rating(3, invert=True), 0.5)

        # None preservation
        self.assertIsNone(normalize_likert_rating(None))

    def test_single_interaction_scaling(self):
        raw = {
            "case_id": "CASE-BEH-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "safety_response": 2,  # inverted: (5-2)/4 = 0.75
            "sleep_disruption": 4,  # direct: (4-1)/4 = 0.75
            "fear_level": 5,        # direct: (5-1)/4 = 1.0
            "social_support": 1,    # inverted: (5-1)/4 = 1.0
            "help_requested": True,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.behavioural_available)
        self.assertEqual(features.safety_distress, 0.75)
        self.assertEqual(features.sleep_disturbance, 0.75)
        self.assertEqual(features.fear_intensity, 1.0)
        self.assertEqual(features.low_social_support, 1.0)
        self.assertEqual(features.help_requested, 1.0)
        # Composite distress = (0.75 + 0.75 + 1.0 + 1.0) / 4 = 0.875
        self.assertEqual(features.composite_distress, 0.875)

        # Without history, deltas must strictly be None
        self.assertIsNone(features.change_from_previous)
        self.assertIsNone(features.change_from_baseline)

    def test_longitudinal_history_processing(self):
        # Baseline interaction
        raw_base = {
            "case_id": "CASE-LONG-01",
            "interaction_date": "2026-08-01",
            "language": "en",
            "safety_response": 4,  # safety_distress = 0.25
            "sleep_disruption": 2,  # sleep_disturbance = 0.25
            "fear_level": 2,        # fear_intensity = 0.25
            "social_support": 4,    # low_social_support = 0.25
        }
        # Intermediate interaction
        raw_mid = {
            "case_id": "CASE-LONG-01",
            "interaction_date": "2026-08-15",
            "language": "en",
            "safety_response": 3,  # 0.5
            "sleep_disruption": 3,  # 0.5
            "fear_level": 3,        # 0.5
            "social_support": 3,    # 0.5
        }
        # Current interaction (sharp deterioration)
        raw_curr = {
            "case_id": "CASE-LONG-01",
            "interaction_date": "2026-09-01",
            "language": "en",
            "safety_response": 1,  # 1.0
            "sleep_disruption": 5,  # 1.0
            "fear_level": 5,        # 1.0
            "social_support": 1,    # 1.0
            "help_requested": True,
        }

        history = [preprocess_interaction(raw_base), preprocess_interaction(raw_mid)]
        current = preprocess_interaction(raw_curr)

        features = self.extractor.extract(current, history=history)

        self.assertTrue(features.behavioural_available)
        self.assertEqual(features.composite_distress, 1.0)

        # Baseline composite was 0.25 -> delta from baseline = 1.0 - 0.25 = +0.75
        self.assertEqual(features.change_from_baseline, 0.75)

        # Previous composite was 0.50 -> delta from previous = 1.0 - 0.50 = +0.50
        self.assertEqual(features.change_from_previous, 0.50)

        # Verify evidence metadata (User Modification 2)
        ev = features.evidence
        self.assertIsNotNone(ev)
        self.assertEqual(ev.observation_count, 3)
        self.assertEqual(len(ev.timestamps), 3)
        self.assertIn("Distress increased from previous interaction (+0.50)", ev.notable_shifts)
        self.assertIn("Distress substantially elevated above baseline (+0.75)", ev.notable_shifts)
        self.assertIn("Elevated fear intensity observed", ev.notable_shifts)
        self.assertIn("Explicit assistance requested by participant", ev.notable_shifts)

    def test_preserves_none_invariant_for_missing_values(self):
        """User Modification 3: Preserve None != 0 throughout behavioural layer."""
        # Partial behavioural data: safety and fear are missing
        raw = {
            "case_id": "CASE-MISSING-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "safety_response": None,
            "sleep_disruption": 3,
            "fear_level": None,
            "social_support": 5,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.behavioural_available)
        # Critical assertion: safety and fear remain None, NEVER 0.0
        self.assertIsNone(features.safety_distress)
        self.assertIsNone(features.fear_intensity)
        self.assertEqual(features.sleep_disturbance, 0.5)
        self.assertEqual(features.low_social_support, 0.0)
        # Composite averages available ratings: (0.5 + 0.0) / 2 = 0.25
        self.assertEqual(features.composite_distress, 0.25)

        # to_feature_dict() must not fabricate missing metrics as 0
        feat_dict = features.to_feature_dict()
        self.assertEqual(feat_dict["behavioural_available"], 1)
        self.assertNotIn("behavioural_safety_distress", feat_dict)
        self.assertNotIn("behavioural_fear_intensity", feat_dict)
        self.assertIn("behavioural_sleep_disturbance", feat_dict)

    def test_completely_absent_behavioural_data(self):
        """When interaction has no behavioural data, behavioural_available is False."""
        raw = {
            "case_id": "CASE-NO-BEH",
            "interaction_date": "2026-09-03",
            "language": "en",
            "safety_response": None,
            "sleep_disruption": None,
            "fear_level": None,
            "social_support": None,
            "help_requested": None,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertFalse(features.behavioural_available)
        self.assertIsNone(features.composite_distress)
        self.assertIsNone(features.safety_distress)
        self.assertIsNone(features.evidence)

        feat_dict = features.to_feature_dict()
        self.assertEqual(feat_dict["behavioural_available"], 0)
        self.assertEqual(len(feat_dict), 1)

    def test_explainability_evidence_metadata(self):
        """User Modification 2: Detailed metadata exposed for explainability."""
        raw = {
            "case_id": "CASE-EVID-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "safety_response": 1,
            "sleep_disruption": 5,
            "fear_level": 4,
            "social_support": 2,
        }
        features = self.extractor.extract(preprocess_interaction(raw))

        self.assertIsNotNone(features.evidence)
        ev = features.evidence
        self.assertEqual(ev.observation_count, 1)
        self.assertEqual(ev.raw_scores["safety_response"], 1.0)
        self.assertEqual(ev.raw_scores["sleep_disruption"], 5.0)

        # Serializability
        ev_dict = ev.to_dict()
        self.assertIn("raw_scores", ev_dict)
        self.assertIn("notable_shifts", ev_dict)

    def test_deterministic_execution(self):
        raw = {
            "case_id": "CASE-DET-BEH",
            "interaction_date": "2026-09-03",
            "language": "en",
            "safety_response": 2,
            "sleep_disruption": 3,
            "fear_level": 4,
            "social_support": 2,
        }
        interaction = preprocess_interaction(raw)
        f1 = self.extractor.extract(interaction)
        f2 = self.extractor.extract(interaction)

        self.assertEqual(f1, f2)
        self.assertEqual(f1.to_dict(), f2.to_dict())
        self.assertEqual(f1.to_feature_dict(), f2.to_feature_dict())

    def test_batch_extraction(self):
        batch = [
            preprocess_interaction({"case_id": "B1", "interaction_date": "2026-09-01", "language": "en", "fear_level": 2}),
            preprocess_interaction({"case_id": "B2", "interaction_date": "2026-09-02", "language": "en", "fear_level": 4}),
        ]
        results = self.extractor.extract_batch(batch)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].fear_intensity, 0.25)
        self.assertEqual(results[1].fear_intensity, 0.75)

    def test_extract_from_raw_convenience(self):
        raw = {
            "case_id": "CASE-RAW-BEH",
            "interaction_date": "2026-09-03",
            "language": "en",
            "fear_level": 5,
        }
        features = self.extractor.extract_from_raw(raw)
        self.assertTrue(features.behavioural_available)
        self.assertEqual(features.fear_intensity, 1.0)

    def test_rejects_unpreprocessed_direct_inputs(self):
        """Enforces architectural boundary: extract() rejects un-preprocessed inputs."""
        with self.assertRaises(TypeError):
            self.extractor.extract({"case_id": "C1", "fear_level": 4})  # type: ignore

        with self.assertRaises(TypeError):
            self.extractor.extract("raw input string")  # type: ignore


if __name__ == "__main__":
    unittest.main()
