"""Missing value handling and missingness assessment utilities.

Follows the core AAROH ML requirement:
    "Missing features must remain explicitly missing.
     NULL/missing must never automatically become zero."
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Optional

from backend.ml.preprocessing.types import MissingnessReport

# Default set of fields evaluated for an interaction's completeness
EXPECTED_INTERACTION_FIELDS: tuple[str, ...] = (
    "text_response",
    "safety_response",
    "sleep_disruption",
    "fear_level",
    "social_support",
    "response_completed",
    "voice_available",
)

BEHAVIOURAL_FIELDS: tuple[str, ...] = (
    "safety_response",
    "sleep_disruption",
    "fear_level",
    "social_support",
)


def is_missing(value: Any, *, treat_empty_str_as_missing: bool = True) -> bool:
    """Checks if a value is genuinely missing.

    Critical invariant: 0, 0.0, and False are NOT missing.
    None and float('nan') ARE missing.
    """
    if value is None:
        return True

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True

    if treat_empty_str_as_missing and isinstance(value, str):
        return len(value.strip()) == 0

    return False


def assess_missingness(
    payload: Mapping[str, Any],
    expected_fields: Optional[Iterable[str]] = None,
) -> MissingnessReport:
    """Analyzes missingness in an interaction payload.

    Never imputes or coerces missing fields to zero. Records exact available
    and missing fields alongside completeness metrics.
    """
    fields_to_check = tuple(expected_fields) if expected_fields is not None else EXPECTED_INTERACTION_FIELDS

    missing: list[str] = []
    available: list[str] = []

    for f in fields_to_check:
        val = payload.get(f)
        if is_missing(val):
            missing.append(f)
        else:
            available.append(f)

    total = len(fields_to_check)
    missing_count = len(missing)
    completeness = round(len(available) / total, 3) if total > 0 else 1.0

    # Domain-specific missingness indicators
    text_val = payload.get("text_response")
    if text_val is None and "transcription" in payload:
        text_val = payload.get("transcription")
    is_text_missing = is_missing(text_val)

    # Voice is missing if voice_available is false/missing OR all voice metrics are missing
    voice_flag = payload.get("voice_available")
    is_voice_missing = not bool(voice_flag)

    # Behavioural ratings are considered missing if ALL behavioural fields are missing
    is_behavioural_missing = all(is_missing(payload.get(bf)) for bf in BEHAVIOURAL_FIELDS)

    return MissingnessReport(
        total_expected_fields=total,
        missing_fields=tuple(missing),
        available_fields=tuple(available),
        missing_count=missing_count,
        completeness_ratio=completeness,
        is_text_missing=is_text_missing,
        is_voice_missing=is_voice_missing,
        is_behavioural_missing=is_behavioural_missing,
    )


def filter_available_features(data: Mapping[str, Any]) -> dict[str, Any]:
    """Returns a dictionary containing only present, non-missing values.

    Preserves original types and values without zero-filling.
    """
    return {k: v for k, v in data.items() if not is_missing(v)}
