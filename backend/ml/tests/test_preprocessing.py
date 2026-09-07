"""Comprehensive unit tests for the ML Preprocessing Pipeline (Slice 2.1).

Tests:
1. Input validation (valid, missing, out of range, malformed types).
2. Unknown language preservation with warning (Modification 1).
3. Text normalization and multilingual Unicode preservation (Indic scripts, ZWJ/ZWNJ, NFKC).
4. Empty, short, and noisy text handling.
5. Missing value safety (ensuring None is NEVER coerced to 0).
6. Forward-compatible metadata preservation for unrecognized fields (Modification 2).
7. Deterministic pipeline execution.
8. Batch preprocessing.
"""

from __future__ import annotations

import unittest
from datetime import date, datetime

from backend.ml.preprocessing import (
    InteractionPreprocessingPipeline,
    PreprocessedInteraction,
    ValidationSeverity,
    assess_missingness,
    clean_invisible_characters,
    detect_scripts,
    evaluate_text_quality,
    filter_available_features,
    is_missing,
    normalize_casing,
    normalize_unicode,
    normalize_whitespace,
    preprocess_interaction,
    preprocess_interaction_batch,
    preprocess_text,
    validate_boolean_field,
    validate_case_id,
    validate_date,
    validate_interaction_payload,
    validate_language,
    validate_numeric_metric,
    validate_scale_rating,
    validate_text_field,
)


class TestValidationUtilities(unittest.TestCase):
    """Test suite for individual validation helper functions."""

    def test_validate_case_id_valid(self):
        val, issue = validate_case_id("CASE-001")
        self.assertEqual(val, "CASE-001")
        self.assertIsNone(issue)

    def test_validate_case_id_rejects_none_empty_or_bad_type(self):
        # None
        val, issue = validate_case_id(None)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "MISSING_CASE_ID")

        # Whitespace
        val, issue = validate_case_id("   ")
        self.assertIsNone(val)
        self.assertEqual(issue.code, "EMPTY_CASE_ID")

        # Non-string
        val, issue = validate_case_id(12345)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "INVALID_CASE_ID_TYPE")

    def test_validate_date_formats(self):
        # datetime object
        val, issue = validate_date(datetime(2026, 9, 3, 14, 30))
        self.assertEqual(val, "2026-09-03")
        self.assertIsNone(issue)

        # date object
        val, issue = validate_date(date(2026, 9, 3))
        self.assertEqual(val, "2026-09-03")
        self.assertIsNone(issue)

        # ISO string
        val, issue = validate_date("2026-09-03")
        self.assertEqual(val, "2026-09-03")
        self.assertIsNone(issue)

        # Invalid format
        val, issue = validate_date("not-a-date")
        self.assertIsNone(val)
        self.assertEqual(issue.code, "INVALID_DATE_FORMAT")

        # None
        val, issue = validate_date(None)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "MISSING_DATE")

    def test_validate_language_known_mappings(self):
        # Standard code
        val, issue = validate_language("hi")
        self.assertEqual(val, "hi")
        self.assertIsNone(issue)

        # Full English name
        val, issue = validate_language("Hindi")
        self.assertEqual(val, "hi")
        self.assertIsNone(issue)

        # Hinglish / Hindi-English
        val, issue = validate_language("Hindi-English")
        self.assertEqual(val, "hi-en")
        self.assertIsNone(issue)

        # Gujarati
        val, issue = validate_language("Gujarati")
        self.assertEqual(val, "gu")
        self.assertIsNone(issue)

    def test_validate_language_preserves_unknown_with_warning(self):
        """Requirement 1: validate_language must preserve unknown languages and emit a warning."""
        val, issue = validate_language("bhojpuri")
        self.assertEqual(val, "bhojpuri")
        self.assertIsNotNone(issue)
        self.assertEqual(issue.severity, ValidationSeverity.WARNING)
        self.assertEqual(issue.code, "UNKNOWN_LANGUAGE")
        self.assertIn("preserved verbatim", issue.message)

    def test_validate_language_handles_missing_with_warning(self):
        val, issue = validate_language(None)
        self.assertEqual(val, "unknown")
        self.assertIsNotNone(issue)
        self.assertEqual(issue.severity, ValidationSeverity.WARNING)

    def test_validate_scale_rating_1_to_5(self):
        # Valid bounds
        for score in (1, 2, 3, 4, 5):
            val, issue = validate_scale_rating(score, 1, 5)
            self.assertEqual(val, score)
            self.assertIsNone(issue)

        # Float representation of integer
        val, issue = validate_scale_rating(4.0, 1, 5)
        self.assertEqual(val, 4)
        self.assertIsNone(issue)

        # None must be safely preserved
        val, issue = validate_scale_rating(None, 1, 5)
        self.assertIsNone(val)
        self.assertIsNone(issue)

        # Out of bounds
        val, issue = validate_scale_rating(0, 1, 5)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "OUT_OF_RANGE")

        val, issue = validate_scale_rating(6, 1, 5)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "OUT_OF_RANGE")

        # Boolean must be rejected (not treated as int 0 or 1)
        val, issue = validate_scale_rating(True, 1, 5)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "INVALID_TYPE")

        # Non-integral float rejected
        val, issue = validate_scale_rating(3.7, 1, 5)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "INVALID_TYPE")

    def test_validate_text_field(self):
        # Valid string
        val, issue = validate_text_field("Hello world")
        self.assertEqual(val, "Hello world")
        self.assertIsNone(issue)

        # None is valid missingness
        val, issue = validate_text_field(None)
        self.assertIsNone(val)
        self.assertIsNone(issue)

        # Wrong type
        val, issue = validate_text_field(12345)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "INVALID_TEXT_TYPE")

    def test_validate_boolean_and_numeric_helpers(self):
        # Boolean helper
        val, _ = validate_boolean_field(True)
        self.assertTrue(val)
        val, _ = validate_boolean_field(0)
        self.assertFalse(val)
        val, _ = validate_boolean_field("yes")
        self.assertTrue(val)

        # Numeric metric
        val, issue = validate_numeric_metric(0.85, min_val=0.0, max_val=1.0)
        self.assertEqual(val, 0.85)
        self.assertIsNone(issue)

        val, issue = validate_numeric_metric(1.5, min_val=0.0, max_val=1.0)
        self.assertIsNone(val)
        self.assertEqual(issue.code, "NUMERIC_OUT_OF_BOUNDS")

        # None preserved
        val, issue = validate_numeric_metric(None)
        self.assertIsNone(val)
        self.assertIsNone(issue)


class TestTextNormalization(unittest.TestCase):
    """Test suite for text preprocessing and multilingual Unicode preservation."""

    def test_unicode_nfkc_normalization(self):
        # Decomposed vs precomposed characters
        decomposed = "e\u0301"  # 'e' + combining acute
        precomposed = "\u00e9"  # 'é'
        self.assertEqual(normalize_unicode(decomposed, form="NFKC"), precomposed)

    def test_indic_unicode_scripts_preserved(self):
        # Hindi / Devanagari
        hindi_text = "मुझे बहुत डर लग रहा है और कोई मदद नहीं मिल रही है।"
        processed_hi = preprocess_text(hindi_text, language="hi")
        self.assertIsNotNone(processed_hi)
        self.assertEqual(processed_hi.clean, hindi_text)
        self.assertIn("Devanagari", processed_hi.quality.detected_scripts)
        self.assertTrue(processed_hi.quality.has_multilingual_chars)

        # Bengali
        bengali_text = "আমি খুব একা বোধ করছি এবং পরিস্থিতি খারাপ।"
        processed_bn = preprocess_text(bengali_text, language="bn")
        self.assertIsNotNone(processed_bn)
        self.assertEqual(processed_bn.clean, bengali_text)
        self.assertIn("Bengali", processed_bn.quality.detected_scripts)

        # Tamil
        tamil_text = "நான் மிகவும் பயப்படுகிறேன்."
        processed_ta = preprocess_text(tamil_text, language="ta")
        self.assertIsNotNone(processed_ta)
        self.assertEqual(processed_ta.clean, tamil_text)
        self.assertIn("Tamil", processed_ta.quality.detected_scripts)

        # Gujarati
        gujarati_text = "મને ચિંતા થઈ રહી છે."
        processed_gu = preprocess_text(gujarati_text, language="gu")
        self.assertIsNotNone(processed_gu)
        self.assertEqual(processed_gu.clean, gujarati_text)
        self.assertIn("Gujarati", processed_gu.quality.detected_scripts)

    def test_zwj_and_zwnj_preserved_for_indic_ligatures(self):
        # Zero-width joiner (\u200d) and non-joiner (\u200c) must NOT be stripped
        # as they are essential for Indic conjuncts
        text_with_zwnj = "क्\u200cष"
        text_with_zwj = "र्\u200dय"
        self.assertIn("\u200c", clean_invisible_characters(text_with_zwnj))
        self.assertIn("\u200d", clean_invisible_characters(text_with_zwj))

    def test_invisible_noise_and_bom_cleaned(self):
        # BOM, zero-width space, and bidi control characters should be removed
        noisy = "\ufeffHello\u200b \u202aworld\u202c!"
        cleaned = clean_invisible_characters(noisy)
        self.assertEqual(cleaned, "Hello world!")

    def test_whitespace_and_casing_normalization(self):
        raw = "  This   is \t a \n\n sentence   with \u00a0 non-breaking   spaces.  "
        normalized = normalize_whitespace(raw)
        self.assertEqual(normalized, "This is a sentence with non-breaking spaces.")

        cased = normalize_casing(normalized, lowercase=True)
        self.assertEqual(cased, "this is a sentence with non-breaking spaces.")

    def test_empty_and_short_text_handling(self):
        # None text
        self.assertIsNone(preprocess_text(None))

        # Empty string
        empty = preprocess_text("")
        self.assertIsNotNone(empty)
        self.assertEqual(empty.clean, "")
        self.assertTrue(empty.quality.is_empty)

        # Whitespace-only string
        ws_only = preprocess_text("    \t \n ")
        self.assertIsNotNone(ws_only)
        self.assertEqual(ws_only.clean, "")
        self.assertTrue(ws_only.quality.is_empty)

        # Very short text (< 3 words or < 10 chars)
        short = preprocess_text("Help me")
        self.assertIsNotNone(short)
        self.assertEqual(short.clean, "help me")
        self.assertTrue(short.quality.is_very_short)
        self.assertFalse(short.quality.is_empty)


class TestMissingValueHandling(unittest.TestCase):
    """Test suite for explicit and safe missing value handling."""

    def test_is_missing_preserves_zero_and_false(self):
        # Invariants: 0 and False are NOT missing
        self.assertFalse(is_missing(0))
        self.assertFalse(is_missing(0.0))
        self.assertFalse(is_missing(False))
        self.assertFalse(is_missing(True))
        self.assertFalse(is_missing("valid string"))

        # Invariants: None and float('nan') ARE missing
        self.assertTrue(is_missing(None))
        self.assertTrue(is_missing(float("nan")))
        self.assertTrue(is_missing(""))
        self.assertTrue(is_missing("   "))

    def test_assess_missingness_complete_interaction(self):
        payload = {
            "text_response": "I am feeling afraid.",
            "safety_response": 2,
            "sleep_disruption": 4,
            "fear_level": 5,
            "social_support": 1,
            "response_completed": True,
            "voice_available": True,
        }
        report = assess_missingness(payload)
        self.assertEqual(report.missing_count, 0)
        self.assertEqual(report.completeness_ratio, 1.0)
        self.assertFalse(report.is_text_missing)
        self.assertFalse(report.is_voice_missing)
        self.assertFalse(report.is_behavioural_missing)

    def test_assess_missingness_partial_and_missed_checkin(self):
        # Missed check-in where text and behavioural scores are None
        missed_payload = {
            "text_response": None,
            "safety_response": None,
            "sleep_disruption": None,
            "fear_level": None,
            "social_support": None,
            "response_completed": False,
            "voice_available": False,
        }
        report = assess_missingness(missed_payload)
        self.assertEqual(report.missing_count, 5)
        self.assertTrue(report.is_text_missing)
        self.assertTrue(report.is_voice_missing)
        self.assertTrue(report.is_behavioural_missing)
        self.assertIn("text_response", report.missing_fields)
        self.assertIn("safety_response", report.missing_fields)

    def test_filter_available_features(self):
        raw = {"a": 1, "b": None, "c": 0, "d": float("nan"), "e": False, "f": ""}
        filtered = filter_available_features(raw)
        self.assertEqual(filtered, {"a": 1, "c": 0, "e": False})


class TestPreprocessingPipeline(unittest.TestCase):
    """Test suite for the end-to-end preprocessing pipeline orchestrator."""

    def test_pipeline_standard_interaction(self):
        raw = {
            "case_id": "AAROH-001",
            "interaction_date": "2026-09-03T10:00:00",
            "language": "Hindi",
            "text_response": "  Mujhe bahut darr lag raha hai.  ",
            "safety_response": 2,
            "sleep_disruption": 4,
            "fear_level": 5,
            "social_support": 2,
            "response_completed": True,
            "voice_available": False,
        }
        preprocessed = preprocess_interaction(raw)

        self.assertTrue(preprocessed.is_usable)
        self.assertEqual(preprocessed.case_id, "AAROH-001")
        self.assertEqual(preprocessed.interaction_date, "2026-09-03")
        self.assertEqual(preprocessed.language, "hi")
        self.assertIsNotNone(preprocessed.text)
        self.assertEqual(preprocessed.text.clean, "mujhe bahut darr lag raha hai.")
        self.assertEqual(preprocessed.behavioural["fear_level"], 5.0)
        self.assertEqual(preprocessed.behavioural["safety_response"], 2.0)
        self.assertFalse(preprocessed.engagement["voice_available"])

    def test_pipeline_preserves_none_behavioural_values(self):
        # Critical rule: Never coerce missing to 0!
        raw = {
            "case_id": "AAROH-002",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "Hello",
            "safety_response": None,
            "sleep_disruption": 3,
            "fear_level": None,
            "social_support": None,
        }
        preprocessed = preprocess_interaction(raw)

        self.assertIsNone(preprocessed.behavioural["safety_response"])
        self.assertIsNone(preprocessed.behavioural["fear_level"])
        self.assertIsNone(preprocessed.behavioural["social_support"])
        self.assertEqual(preprocessed.behavioural["sleep_disruption"], 3.0)

    def test_pipeline_preserves_unknown_fields_in_metadata(self):
        """Requirement 2: Preserve unknown input fields inside metadata dictionary."""
        raw = {
            "case_id": "AAROH-003",
            "interaction_date": "2026-09-03",
            "language": "en",
            "text_response": "Checking in.",
            # Unrecognized / custom fields
            "custom_telemetry_id": 998877,
            "device_hardware": "Android 14 ARM64",
            "network_latency_ms": 120,
        }
        preprocessed = preprocess_interaction(raw)

        self.assertEqual(preprocessed.metadata["custom_telemetry_id"], 998877)
        self.assertEqual(preprocessed.metadata["device_hardware"], "Android 14 ARM64")
        self.assertEqual(preprocessed.metadata["network_latency_ms"], 120)

    def test_pipeline_preserves_unknown_language_with_warning(self):
        """Requirement 1: Preserve unknown language with warning without failing."""
        raw = {
            "case_id": "AAROH-004",
            "interaction_date": "2026-09-03",
            "language": "Maithili",
            "text_response": "हम ठीक छी",
        }
        preprocessed = preprocess_interaction(raw)

        self.assertTrue(preprocessed.is_usable)  # Did NOT fail!
        self.assertEqual(preprocessed.language, "maithili")
        # Check warning exists
        warnings = preprocessed.validation.warnings
        self.assertTrue(any(w.code == "UNKNOWN_LANGUAGE" for w in warnings))

    def test_pipeline_deterministic_execution(self):
        raw = {
            "case_id": "AAROH-005",
            "interaction_date": "2026-09-03",
            "language": "Hindi",
            "text_response": "मुझे बहुत डर लग रहा है।",
            "fear_level": 4,
            "safety_response": 1,
            "sleep_disruption": 5,
            "social_support": 1,
        }
        res1 = preprocess_interaction(raw)
        res2 = preprocess_interaction(raw)

        self.assertEqual(res1, res2)
        self.assertEqual(res1.to_dict(), res2.to_dict())

    def test_batch_preprocessing(self):
        batch = [
            {"case_id": "CASE-1", "interaction_date": "2026-09-01", "language": "en", "text_response": "Fine"},
            {"case_id": "CASE-2", "interaction_date": "2026-09-02", "language": "hi", "text_response": "डर"},
        ]
        results = preprocess_interaction_batch(batch)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].case_id, "CASE-1")
        self.assertEqual(results[1].case_id, "CASE-2")


if __name__ == "__main__":
    unittest.main()
