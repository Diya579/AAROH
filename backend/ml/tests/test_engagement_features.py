"""Comprehensive unit tests for Engagement Feature Extraction (Slice 2.4).

Tests:
1. Complete engagement history (consistent check-ins, punctuality, high score).
2. Partial history (mixed completed and missed check-ins, streak tracking).
3. Missing history / single observation (deltas and delays remain None).
4. Missed check-in interaction (response_completed=False).
5. Delayed response detection and alerts.
6. Inactivity duration and recent activity window.
7. Longitudinal engagement trend (DECLINING vs IMPROVING vs STABLE).
8. Configurable thresholds via EngagementConfig (User Modification 1).
9. Engagement score strictly as adherence summary, not distress (User Modification 2).
10. Strict None != 0 invariant (missing delay is never fabricated as 0.0).
11. Explainability evidence metadata.
12. Determinism (repeated execution returns identical features).
13. Batch processing.
14. Strict type safety: rejects un-preprocessed inputs.
"""

from __future__ import annotations

import unittest

from backend.ml.features import (
    DEFAULT_LONG_RESPONSE_DELAY_DAYS,
    DEFAULT_MISSED_CHECKIN_ALERT_STREAK,
    EngagementConfig,
    EngagementEvidence,
    EngagementFeatureExtractor,
    EngagementFeatures,
    EngagementMetric,
    EngagementTrend,
    extract_engagement_features,
    extract_engagement_features_batch,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


class TestEngagementFeatureExtraction(unittest.TestCase):
    """Unit test suite for Slice 2.4 Engagement Feature Extraction."""

    def setUp(self):
        self.extractor = EngagementFeatureExtractor()

    def test_configurable_definitions(self):
        """User Modification 1: Centralized, configurable thresholds via EngagementConfig."""
        default_cfg = EngagementConfig()
        self.assertEqual(default_cfg.long_response_delay_days, DEFAULT_LONG_RESPONSE_DELAY_DAYS)
        self.assertEqual(default_cfg.missed_checkin_alert_streak, DEFAULT_MISSED_CHECKIN_ALERT_STREAK)

        # Custom configuration
        custom_cfg = EngagementConfig(
            long_response_delay_days=3.0,
            missed_checkin_alert_streak=1,
            low_consistency_threshold=0.75,
        )
        self.assertEqual(custom_cfg.long_response_delay_days, 3.0)
        self.assertEqual(custom_cfg.missed_checkin_alert_streak, 1)

        # Validation of invalid config
        with self.assertRaises(ValueError):
            EngagementConfig(long_response_delay_days=-1.0)
        with self.assertRaises(ValueError):
            EngagementConfig(low_consistency_threshold=1.5)

    def test_single_interaction_missing_history_preserves_none(self):
        """User Modification 3: None != 0. Missing history/delay remains None."""
        raw = {
            "case_id": "CASE-ENG-01",
            "interaction_date": "2026-09-01",
            "language": "en",
            "response_completed": True,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.engagement_available)
        self.assertEqual(features.completed_checkin, 1.0)
        self.assertEqual(features.missed_checkin, 0.0)
        self.assertEqual(features.missed_checkin_streak, 0)
        self.assertEqual(features.checkin_consistency, 1.0)
        self.assertEqual(features.interaction_count, 1)

        # Crucial invariant: delay and deltas must strictly be None (NOT 0.0)
        self.assertIsNone(features.response_delay)
        self.assertIsNone(features.average_response_delay)
        self.assertIsNone(features.change_from_previous)
        self.assertIsNone(features.change_from_baseline)

        # to_feature_dict() must not emit response_delay: 0.0
        feat_dict = features.to_feature_dict()
        self.assertEqual(feat_dict["engagement_available"], 1)
        self.assertEqual(feat_dict["engagement_completed_checkin"], 1.0)
        self.assertNotIn("engagement_response_delay", feat_dict)

    def test_complete_engagement_history(self):
        # 3 punctual, completed interactions 7 days apart
        h1 = preprocess_interaction({
            "case_id": "CASE-ENG-02",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        h2 = preprocess_interaction({
            "case_id": "CASE-ENG-02",
            "interaction_date": "2026-08-08",
            "language": "en",
            "response_completed": True,
        })
        curr = preprocess_interaction({
            "case_id": "CASE-ENG-02",
            "interaction_date": "2026-08-15",
            "language": "en",
            "response_completed": True,
        })

        features = self.extractor.extract(curr, history=[h1, h2])

        self.assertTrue(features.engagement_available)
        self.assertEqual(features.interaction_count, 3)
        self.assertEqual(features.checkin_consistency, 1.0)
        self.assertEqual(features.missed_checkin_streak, 0)
        self.assertEqual(features.response_delay, 7.0)
        self.assertEqual(features.average_response_delay, 7.0)
        self.assertEqual(features.engagement_trend, EngagementTrend.STABLE.value)

        # Evidence
        ev = features.evidence
        self.assertIsNotNone(ev)
        self.assertEqual(ev.completed_count, 3)
        self.assertEqual(ev.missed_count, 0)
        self.assertEqual(len(ev.delays), 2)

    def test_missed_checkin_and_streak_tracking(self):
        h1 = preprocess_interaction({
            "case_id": "CASE-ENG-03",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        h2 = preprocess_interaction({
            "case_id": "CASE-ENG-03",
            "interaction_date": "2026-08-08",
            "language": "en",
            "response_completed": False,  # 1st missed
        })
        curr = preprocess_interaction({
            "case_id": "CASE-ENG-03",
            "interaction_date": "2026-08-15",
            "language": "en",
            "response_completed": False,  # 2nd missed
        })

        features = self.extractor.extract(curr, history=[h1, h2])

        self.assertEqual(features.completed_checkin, 0.0)
        self.assertEqual(features.missed_checkin, 1.0)
        self.assertEqual(features.missed_checkin_streak, 2)
        # 1 completed out of 3 total = 0.333
        self.assertEqual(features.checkin_consistency, 0.333)
        self.assertEqual(features.engagement_trend, EngagementTrend.DECLINING.value)

        # Notable shifts triggered by streak >= 2
        ev = features.evidence
        self.assertIn("Missed 2 consecutive scheduled check-ins", ev.notable_shifts)
        self.assertIn("Low check-in completion consistency (33%)", ev.notable_shifts)

    def test_delayed_response_alert(self):
        # Prior interaction 15 days ago (configured default alert is >= 5 days)
        h1 = preprocess_interaction({
            "case_id": "CASE-ENG-04",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        curr = preprocess_interaction({
            "case_id": "CASE-ENG-04",
            "interaction_date": "2026-08-16",
            "language": "en",
            "response_completed": True,
        })

        features = self.extractor.extract(curr, history=[h1])

        self.assertEqual(features.response_delay, 15.0)
        self.assertEqual(features.inactivity_duration, 15.0)
        self.assertIn("Extended response delay of 15.0 days", features.evidence.notable_shifts)

    def test_custom_config_thresholds(self):
        """User Modification 1: Custom EngagementConfig adjusts alert thresholds."""
        custom_cfg = EngagementConfig(
            long_response_delay_days=10.0,
            missed_checkin_alert_streak=3,
        )
        custom_extractor = EngagementFeatureExtractor(config=custom_cfg)

        h1 = preprocess_interaction({
            "case_id": "CASE-ENG-05",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        curr = preprocess_interaction({
            "case_id": "CASE-ENG-05",
            "interaction_date": "2026-08-08",
            "language": "en",
            "response_completed": True,
        })

        # 7 days delay: triggers default (5.0), but does NOT trigger custom (10.0)
        features = custom_extractor.extract(curr, history=[h1])
        self.assertEqual(features.response_delay, 7.0)
        delay_shifts = [s for s in features.evidence.notable_shifts if "Extended response delay" in s]
        self.assertEqual(len(delay_shifts), 0)

    def test_engagement_score_represents_adherence_not_distress(self):
        """User Modification 2: engagement_score is interaction reliability, NOT distress."""
        # Completed check-in with high consistency = high engagement score
        h1 = preprocess_interaction({
            "case_id": "CASE-ENG-06",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        curr = preprocess_interaction({
            "case_id": "CASE-ENG-06",
            "interaction_date": "2026-08-02",
            "language": "en",
            "response_completed": True,
        })
        features = self.extractor.extract(curr, history=[h1])
        # High adherence: score near 1.0
        self.assertGreaterEqual(features.engagement_score, 0.90)

    def test_deterministic_execution(self):
        h1 = preprocess_interaction({
            "case_id": "CASE-DET",
            "interaction_date": "2026-08-01",
            "language": "en",
            "response_completed": True,
        })
        curr = preprocess_interaction({
            "case_id": "CASE-DET",
            "interaction_date": "2026-08-08",
            "language": "en",
            "response_completed": True,
        })

        f1 = self.extractor.extract(curr, history=[h1])
        f2 = self.extractor.extract(curr, history=[h1])

        self.assertEqual(f1, f2)
        self.assertEqual(f1.to_dict(), f2.to_dict())
        self.assertEqual(f1.to_feature_dict(), f2.to_feature_dict())

    def test_batch_extraction(self):
        batch = [
            preprocess_interaction({"case_id": "B1", "interaction_date": "2026-09-01", "language": "en", "response_completed": True}),
            preprocess_interaction({"case_id": "B2", "interaction_date": "2026-09-02", "language": "en", "response_completed": False}),
        ]
        results = self.extractor.extract_batch(batch)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].completed_checkin, 1.0)
        self.assertEqual(results[1].completed_checkin, 0.0)

    def test_extract_from_raw_convenience(self):
        raw = {
            "case_id": "CASE-RAW-ENG",
            "interaction_date": "2026-09-03",
            "language": "en",
            "response_completed": True,
        }
        features = self.extractor.extract_from_raw(raw)
        self.assertTrue(features.engagement_available)
        self.assertEqual(features.completed_checkin, 1.0)

    def test_rejects_unpreprocessed_direct_inputs(self):
        """Enforces architectural boundary: extract() rejects un-preprocessed inputs."""
        with self.assertRaises(TypeError):
            self.extractor.extract({"case_id": "C1", "response_completed": True})  # type: ignore

        with self.assertRaises(TypeError):
            self.extractor.extract("raw text string")  # type: ignore


if __name__ == "__main__":
    unittest.main()
