"""Comprehensive unit tests for Text Feature Extraction (Slice 2.2).

Tests:
1. English text feature extraction.
2. Hindi (Devanagari) text feature extraction.
3. Hinglish (Romanized Hindi) text feature extraction.
4. Empty, whitespace, and None text inputs.
5. Missing value handling (preserves None != 0, no fabricated features).
6. Explainability evidence metadata (User Modification 1).
7. Centralized lexicons access and correctness (User Modification 2).
8. Determinism (repeated execution returns identical features).
9. Batch processing.
10. Strict type safety: rejects un-preprocessed inputs.
"""

from __future__ import annotations

import unittest

from backend.ml.features import (
    DISTRESS_LEXICONS,
    HELP_SEEKING_LEXICONS,
    SAFETY_LEXICONS,
    TextFeatureExtractor,
    TextFeatures,
    extract_distress_indicators,
    extract_help_seeking_indicators,
    extract_lexical_metrics,
    extract_safety_indicators,
    extract_text_features,
    extract_text_features_batch,
    find_matched_terms,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


class TestTextFeatureExtraction(unittest.TestCase):
    """Unit test suite for Slice 2.2 Text Feature Extraction."""

    def setUp(self):
        self.extractor = TextFeatureExtractor()

    def test_english_text_features(self):
        raw = {
            "case_id": "CASE-EN-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": (
                "I feel very afraid and hopeless. "
                "I am completely alone and need someone to help me immediately."
            ),
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.text_available)
        self.assertIsNotNone(features.lexical)
        self.assertIsNotNone(features.distress)
        self.assertIsNotNone(features.help_seeking)
        self.assertIsNotNone(features.safety)
        self.assertIsNotNone(features.quality)
        self.assertIsNotNone(features.evidence)

        # Lexical metrics
        self.assertEqual(features.lexical.sentence_count, 2)
        self.assertGreater(features.lexical.word_count, 10)
        self.assertGreater(features.lexical.character_count, 50)

        # Distress indicators
        self.assertGreater(features.distress.fear, 0.0)
        self.assertGreater(features.distress.hopelessness, 0.0)
        self.assertGreater(features.distress.isolation, 0.0)

        # Help-seeking indicators
        self.assertGreater(features.help_seeking.asking_for_help, 0.0)
        self.assertGreater(features.help_seeking.requesting_support, 0.0)

        # Safety & urgency
        self.assertGreater(features.safety.urgency, 0.0)

        # Explainability evidence (User Modification 1)
        evidence = features.evidence
        self.assertIn("afraid", evidence.all_matched_terms)
        self.assertIn("hopeless", evidence.all_matched_terms)
        self.assertIn("alone", evidence.all_matched_terms)
        self.assertIn("help", evidence.all_matched_terms)
        self.assertIn("immediately", evidence.all_matched_terms)

    def test_hindi_devanagari_text_features(self):
        raw = {
            "case_id": "CASE-HI-01",
            "interaction_date": "2026-09-03",
            "language": "Hindi",
            "text_response": "मुझे बहुत डर लग रहा है और मैं अकेला हूँ। कृपया मदद चाहिए, तुरंत पुलिस बुलाओ।",
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.text_available)
        self.assertEqual(features.quality.language, "hi")
        self.assertIn("Devanagari", features.quality.detected_scripts)
        self.assertTrue(features.quality.has_multilingual_chars)

        # Distress indicators from Hindi lexicons
        self.assertGreater(features.distress.fear, 0.0)
        self.assertGreater(features.distress.isolation, 0.0)

        # Help-seeking & Emergency in Hindi
        self.assertGreater(features.help_seeking.asking_for_help, 0.0)
        self.assertGreater(features.help_seeking.emergency_language, 0.0)

        # Safety & Urgency in Hindi
        self.assertGreater(features.safety.urgency, 0.0)

        # Explainability evidence (Devanagari terms preserved)
        self.assertIn("डर", features.evidence.all_matched_terms)
        self.assertIn("अकेला", features.evidence.all_matched_terms)
        self.assertIn("मदद चाहिए", features.evidence.all_matched_terms)
        self.assertIn("पुलिस बुलाओ", features.evidence.all_matched_terms)
        self.assertIn("तुरंत", features.evidence.all_matched_terms)

    def test_hinglish_code_mixed_text_features(self):
        raw = {
            "case_id": "CASE-HINGLISH-01",
            "interaction_date": "2026-09-03",
            "language": "Hinglish",
            "text_response": "Mujhe bahut darr lag raha hai, koi umeed nahi bachi hai. Please madad karo.",
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertTrue(features.text_available)
        self.assertGreater(features.distress.fear, 0.0)
        self.assertGreater(features.distress.hopelessness, 0.0)
        self.assertGreater(features.help_seeking.asking_for_help, 0.0)

        # Explainability matches
        self.assertIn("darr", features.evidence.all_matched_terms)
        self.assertIn("koi umeed nahi", features.evidence.all_matched_terms)
        self.assertIn("madad", features.evidence.all_matched_terms)

    def test_missing_text_preserves_none_invariant(self):
        """Preserves Slice 2.1 invariant: None != 0.

        When text is None, features must NOT fabricate 0.0 scores.
        text_available must be False and indicator categories must be None.
        """
        raw = {
            "case_id": "CASE-MISSING-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": None,
        }
        interaction = preprocess_interaction(raw)
        features = self.extractor.extract(interaction)

        self.assertFalse(features.text_available)
        self.assertIsNone(features.lexical)
        self.assertIsNone(features.distress)
        self.assertIsNone(features.help_seeking)
        self.assertIsNone(features.safety)
        self.assertIsNone(features.evidence)
        self.assertTrue(features.quality.is_empty)

        # Flattened feature dictionary must reflect text_available=0 without fake zeros
        feat_dict = features.to_feature_dict()
        self.assertEqual(feat_dict["text_available"], 0)
        self.assertNotIn("distress_fear", feat_dict)
        self.assertNotIn("help_seeking_asking_for_help", feat_dict)

    def test_empty_and_whitespace_text_handling(self):
        # Empty string
        raw_empty = {
            "case_id": "CASE-EMPTY-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "",
        }
        feat_empty = self.extractor.extract(preprocess_interaction(raw_empty))
        self.assertFalse(feat_empty.text_available)
        self.assertIsNone(feat_empty.distress)

        # Whitespace-only string
        raw_ws = {
            "case_id": "CASE-WS-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "    \t \n  ",
        }
        feat_ws = self.extractor.extract(preprocess_interaction(raw_ws))
        self.assertFalse(feat_ws.text_available)
        self.assertIsNone(feat_ws.distress)

    def test_explainability_evidence_metadata(self):
        """User Modification 1: Matched keywords stored in metadata for explainability."""
        raw = {
            "case_id": "CASE-EXP-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "I am depressed and having severe anxiety. Please help me find shelter.",
        }
        features = self.extractor.extract(preprocess_interaction(raw))

        self.assertIsNotNone(features.evidence)
        ev = features.evidence
        # Check category mappings
        self.assertIn("sadness", ev.matched_terms_by_category)
        self.assertIn("anxiety", ev.matched_terms_by_category)
        self.assertIn("asking_for_help", ev.matched_terms_by_category)
        self.assertIn("requesting_support", ev.matched_terms_by_category)

        self.assertIn("depressed", ev.matched_terms_by_category["sadness"])
        self.assertIn("anxiety", ev.matched_terms_by_category["anxiety"])
        self.assertIn("help", ev.matched_terms_by_category["asking_for_help"])
        self.assertIn("shelter", ev.matched_terms_by_category["requesting_support"])

        # Check serialization
        ev_dict = ev.to_dict()
        self.assertIn("matched_terms_by_category", ev_dict)
        self.assertIn("all_matched_terms", ev_dict)

    def test_centralized_lexicons_source_of_truth(self):
        """User Modification 2: Centralized lexicons are single source of truth."""
        self.assertIn("fear", DISTRESS_LEXICONS)
        self.assertIn("hopelessness", DISTRESS_LEXICONS)
        self.assertIn("asking_for_help", HELP_SEEKING_LEXICONS)
        self.assertIn("urgency", SAFETY_LEXICONS)

        # find_matched_terms utility
        found = find_matched_terms("I feel scared and terrified", DISTRESS_LEXICONS["fear"])
        self.assertIn("scared", found)
        self.assertIn("terrified", found)

    def test_deterministic_feature_extraction(self):
        raw = {
            "case_id": "CASE-DET-01",
            "interaction_date": "2026-09-03",
            "language": "Hindi",
            "text_response": "मुझे बहुत डर लग रहा है।",
        }
        interaction = preprocess_interaction(raw)
        res1 = self.extractor.extract(interaction)
        res2 = self.extractor.extract(interaction)

        self.assertEqual(res1, res2)
        self.assertEqual(res1.to_dict(), res2.to_dict())
        self.assertEqual(res1.to_feature_dict(), res2.to_feature_dict())

    def test_batch_feature_extraction(self):
        batch = [
            preprocess_interaction({"case_id": "C1", "interaction_date": "2026-09-01", "language": "en", "text_response": "I am fine."}),
            preprocess_interaction({"case_id": "C2", "interaction_date": "2026-09-02", "language": "hi", "text_response": "मुझे डर लग रहा है।"}),
            preprocess_interaction({"case_id": "C3", "interaction_date": "2026-09-03", "language": "en", "text_response": None}),
        ]
        results = self.extractor.extract_batch(batch)
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].text_available)
        self.assertTrue(results[1].text_available)
        self.assertFalse(results[2].text_available)

    def test_extract_from_raw_convenience(self):
        raw = {
            "case_id": "CASE-RAW-01",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "Need assistance and legal aid.",
        }
        features = self.extractor.extract_from_raw(raw)
        self.assertTrue(features.text_available)
        self.assertGreater(features.help_seeking.requesting_support, 0.0)

    def test_rejects_unpreprocessed_direct_inputs(self):
        """Enforces architectural invariant: extract() rejects un-preprocessed inputs."""
        with self.assertRaises(TypeError):
            self.extractor.extract("raw text string")  # type: ignore

        with self.assertRaises(TypeError):
            self.extractor.extract({"case_id": "C1", "text_response": "raw dict"})  # type: ignore


if __name__ == "__main__":
    unittest.main()
