"""Input validation utilities for ML interactions.

Validates raw payloads to prevent garbage-in / garbage-out, while safely preserving
missing values (None) and unknown languages (with a warning).
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Mapping, Optional

from backend.ml.preprocessing.types import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)

# Canonical mapping for recognized Indian and international languages
KNOWN_LANGUAGES: dict[str, str] = {
    "en": "en",
    "english": "en",
    "hi": "hi",
    "hindi": "hi",
    "gu": "gu",
    "gujarati": "gu",
    "mr": "mr",
    "marathi": "mr",
    "bn": "bn",
    "bengali": "bn",
    "bangla": "bn",
    "ta": "ta",
    "tamil": "ta",
    "te": "te",
    "telugu": "te",
    "kn": "kn",
    "kannada": "kn",
    "ml": "ml",
    "malayalam": "ml",
    "pa": "pa",
    "punjabi": "pa",
    "or": "or",
    "odia": "or",
    "oriya": "or",
    "as": "as",
    "assamese": "as",
    "ur": "ur",
    "urdu": "ur",
    "hi-en": "hi-en",
    "hindi-english": "hi-en",
    "hinglish": "hi-en",
    "gu-en": "gu-en",
    "gujarati-english": "gu-en",
}

# Standard recognized schema fields for Interaction
KNOWN_INTERACTION_FIELDS = frozenset(
    {
        "case_id",
        "interaction_id",
        "interaction_date",
        "channel",
        "language",
        "text_response",
        "transcription",
        "voice_available",
        "response_completed",
        "safety_response",
        "sleep_disruption",
        "fear_level",
        "social_support",
        "help_requested",
        "data_quality",
        "asr_confidence",
        "speech_rate",
        "pause_ratio",
        "response_latency",
        "pitch_variability",
        "energy_variation",
        "audio_quality",
        "baseline_deviation",
    }
)


def validate_case_id(value: Any) -> tuple[Optional[str], Optional[ValidationIssue]]:
    """Validates the case identifier."""
    if value is None:
        return None, ValidationIssue(
            field="case_id",
            code="MISSING_CASE_ID",
            message="case_id is required and cannot be null",
            severity=ValidationSeverity.ERROR,
        )

    if not isinstance(value, str):
        return None, ValidationIssue(
            field="case_id",
            code="INVALID_CASE_ID_TYPE",
            message=f"case_id must be a string, got {type(value).__name__}",
            severity=ValidationSeverity.ERROR,
        )

    clean = value.strip()
    if not clean:
        return None, ValidationIssue(
            field="case_id",
            code="EMPTY_CASE_ID",
            message="case_id cannot be an empty or whitespace-only string",
            severity=ValidationSeverity.ERROR,
        )

    return clean, None


def validate_date(
    value: Any, field_name: str = "interaction_date"
) -> tuple[Optional[str], Optional[ValidationIssue]]:
    """Validates and standardizes a date/datetime input into ISO 8601 YYYY-MM-DD."""
    if value is None:
        return None, ValidationIssue(
            field=field_name,
            code="MISSING_DATE",
            message=f"{field_name} is required",
            severity=ValidationSeverity.ERROR,
        )

    if isinstance(value, datetime):
        return value.date().isoformat(), None

    if isinstance(value, date):
        return value.isoformat(), None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None, ValidationIssue(
                field=field_name,
                code="EMPTY_DATE",
                message=f"{field_name} cannot be empty",
                severity=ValidationSeverity.ERROR,
            )
        try:
            parsed = date.fromisoformat(raw[:10])
            return parsed.isoformat(), None
        except ValueError:
            return None, ValidationIssue(
                field=field_name,
                code="INVALID_DATE_FORMAT",
                message=f"{field_name} '{value}' is not a valid ISO date",
                severity=ValidationSeverity.ERROR,
            )

    return None, ValidationIssue(
        field=field_name,
        code="INVALID_DATE_TYPE",
        message=f"{field_name} must be a date, datetime, or ISO string; got {type(value).__name__}",
        severity=ValidationSeverity.ERROR,
    )


def validate_language(value: Any) -> tuple[str, Optional[ValidationIssue]]:
    """Validates language specification.

    Recognized languages are mapped to canonical codes.
    Unknown languages are preserved verbatim with a WARNING, never failing preprocessing.
    """
    if value is None:
        return "unknown", ValidationIssue(
            field="language",
            code="MISSING_LANGUAGE",
            message="Language not specified; preserving as 'unknown'",
            severity=ValidationSeverity.WARNING,
        )

    if not isinstance(value, str):
        return "unknown", ValidationIssue(
            field="language",
            code="INVALID_LANGUAGE_TYPE",
            message=f"Language must be a string, got {type(value).__name__}; defaulting to 'unknown'",
            severity=ValidationSeverity.WARNING,
        )

    clean = value.strip().lower()
    if not clean:
        return "unknown", ValidationIssue(
            field="language",
            code="EMPTY_LANGUAGE",
            message="Empty language string provided; preserved as 'unknown'",
            severity=ValidationSeverity.WARNING,
        )

    if clean in KNOWN_LANGUAGES:
        return KNOWN_LANGUAGES[clean], None

    # Preserved verbatim with a warning as requested
    return clean, ValidationIssue(
        field="language",
        code="UNKNOWN_LANGUAGE",
        message=f"Unknown language '{value}'; preserved verbatim",
        severity=ValidationSeverity.WARNING,
    )


def validate_scale_rating(
    value: Any, min_val: int = 1, max_val: int = 5, field_name: str = "rating"
) -> tuple[Optional[int], Optional[ValidationIssue]]:
    """Validates an integer rating (e.g. Likert 1-5).

    Safely preserves None as valid missingness.
    Rejects booleans, non-numeric values, or values outside [min_val, max_val].
    """
    if value is None:
        return None, None

    if isinstance(value, bool):
        return None, ValidationIssue(
            field=field_name,
            code="INVALID_TYPE",
            message=f"{field_name} must be an integer, got bool",
            severity=ValidationSeverity.ERROR,
        )

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None, None
        if not value.is_integer():
            return None, ValidationIssue(
                field=field_name,
                code="INVALID_TYPE",
                message=f"{field_name} must be an integer, got non-integral float {value}",
                severity=ValidationSeverity.ERROR,
            )
        value = int(value)

    if isinstance(value, int):
        if min_val <= value <= max_val:
            return value, None
        return None, ValidationIssue(
            field=field_name,
            code="OUT_OF_RANGE",
            message=f"{field_name} must be between {min_val} and {max_val}, got {value}",
            severity=ValidationSeverity.ERROR,
        )

    return None, ValidationIssue(
        field=field_name,
        code="INVALID_TYPE",
        message=f"{field_name} must be an integer in [{min_val}, {max_val}], got {type(value).__name__}",
        severity=ValidationSeverity.ERROR,
    )


def validate_text_field(
    value: Any, field_name: str = "text"
) -> tuple[Optional[str], Optional[ValidationIssue]]:
    """Validates text input. Preserves None as valid missingness."""
    if value is None:
        return None, None

    if isinstance(value, str):
        return value, None

    return None, ValidationIssue(
        field=field_name,
        code="INVALID_TEXT_TYPE",
        message=f"{field_name} must be a string or None, got {type(value).__name__}",
        severity=ValidationSeverity.ERROR,
    )


def validate_boolean_field(
    value: Any, field_name: str = "flag", default: Optional[bool] = None
) -> tuple[Optional[bool], Optional[ValidationIssue]]:
    """Validates a boolean field."""
    if value is None:
        return default, None

    if isinstance(value, bool):
        return value, None

    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value), None

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "t"):
            return True, None
        if lowered in ("false", "0", "no", "f"):
            return False, None

    return default, ValidationIssue(
        field=field_name,
        code="INVALID_BOOLEAN",
        message=f"{field_name} could not be parsed as boolean from {value!r}",
        severity=ValidationSeverity.WARNING,
    )


def validate_numeric_metric(
    value: Any,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    field_name: str = "metric",
) -> tuple[Optional[float], Optional[ValidationIssue]]:
    """Validates a continuous numerical measurement. Preserves None safely."""
    if value is None:
        return None, None

    if isinstance(value, bool):
        return None, ValidationIssue(
            field=field_name,
            code="INVALID_NUMERIC_TYPE",
            message=f"{field_name} must be a number, got bool",
            severity=ValidationSeverity.ERROR,
        )

    try:
        fval = float(value)
    except (ValueError, TypeError):
        return None, ValidationIssue(
            field=field_name,
            code="INVALID_NUMERIC_TYPE",
            message=f"{field_name} must be numeric, got {value!r}",
            severity=ValidationSeverity.ERROR,
        )

    if math.isnan(fval) or math.isinf(fval):
        return None, None

    if min_val is not None and fval < min_val:
        return None, ValidationIssue(
            field=field_name,
            code="NUMERIC_OUT_OF_BOUNDS",
            message=f"{field_name} is below minimum {min_val}: {fval}",
            severity=ValidationSeverity.ERROR,
        )

    if max_val is not None and fval > max_val:
        return None, ValidationIssue(
            field=field_name,
            code="NUMERIC_OUT_OF_BOUNDS",
            message=f"{field_name} exceeds maximum {max_val}: {fval}",
            severity=ValidationSeverity.ERROR,
        )

    return fval, None


def validate_interaction_payload(payload: Mapping[str, Any]) -> ValidationResult:
    """Validates an interaction mapping and returns a ValidationResult.

    Collects all errors and warnings rather than halting at the first failure.
    """
    issues: list[ValidationIssue] = []
    cleaned: dict[str, Any] = {}

    # 1. case_id
    case_id, issue = validate_case_id(payload.get("case_id"))
    if issue:
        issues.append(issue)
    if case_id is not None:
        cleaned["case_id"] = case_id

    # 2. interaction_date
    int_date, issue = validate_date(payload.get("interaction_date"))
    if issue:
        issues.append(issue)
    if int_date is not None:
        cleaned["interaction_date"] = int_date

    # 3. language
    language, issue = validate_language(payload.get("language"))
    if issue:
        issues.append(issue)
    cleaned["language"] = language

    # 4. text_response / transcription
    raw_text = payload.get("text_response")
    if raw_text is None and "transcription" in payload:
        raw_text = payload.get("transcription")
    text_val, issue = validate_text_field(raw_text, field_name="text_response")
    if issue:
        issues.append(issue)
    cleaned["text_response"] = text_val

    # 5. behavioural 1-5 ratings
    for rating_field in ("safety_response", "sleep_disruption", "fear_level", "social_support"):
        r_val, issue = validate_scale_rating(payload.get(rating_field), field_name=rating_field)
        if issue:
            issues.append(issue)
        cleaned[rating_field] = r_val

    # 6. engagement and quality flags
    resp_comp, issue = validate_boolean_field(
        payload.get("response_completed"), field_name="response_completed", default=True
    )
    if issue:
        issues.append(issue)
    cleaned["response_completed"] = resp_comp

    voice_avail, issue = validate_boolean_field(
        payload.get("voice_available"), field_name="voice_available", default=False
    )
    if issue:
        issues.append(issue)
    cleaned["voice_available"] = voice_avail

    help_req, issue = validate_boolean_field(
        payload.get("help_requested"), field_name="help_requested", default=False
    )
    if issue:
        issues.append(issue)
    cleaned["help_requested"] = help_req

    dq = payload.get("data_quality", "good")
    if isinstance(dq, str):
        cleaned["data_quality"] = dq.strip().lower()
    else:
        cleaned["data_quality"] = "good"

    # 7. voice metrics
    voice_metrics = (
        "speech_rate",
        "pause_ratio",
        "response_latency",
        "pitch_variability",
        "energy_variation",
        "audio_quality",
        "asr_confidence",
    )
    for vm in voice_metrics:
        vm_val, issue = validate_numeric_metric(payload.get(vm), min_val=0.0, field_name=vm)
        if issue:
            issues.append(issue)
        cleaned[vm] = vm_val

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(
        is_valid=not has_errors,
        issues=tuple(issues),
        cleaned_data=cleaned,
    )
