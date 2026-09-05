"""Distress indicator extraction (Slice 2.2).

Detects observable distress language signals deterministically using centralized lexicons.
Returns structured DistressIndicators and matched terms for explainability.
"""

from __future__ import annotations

from typing import Mapping

from backend.ml.features.lexicons import DISTRESS_LEXICONS, find_matched_terms
from backend.ml.features.types import DistressIndicators


def calculate_category_score(matched_count: int, saturation_count: float = 2.0) -> float:
    """Calculates a bounded indicator score in [0.0, 1.0]."""
    if matched_count <= 0:
        return 0.0
    return min(1.0, round(matched_count / saturation_count, 3))


def extract_distress_indicators(
    clean_text: str,
) -> tuple[DistressIndicators, dict[str, tuple[str, ...]]]:
    """Extracts distress indicators from cleaned text.

    Returns:
    - DistressIndicators: numeric features bounded in [0.0, 1.0]
    - Matched evidence dictionary: category -> tuple of matched phrases
    """
    if not clean_text or not clean_text.strip():
        empty_indicators = DistressIndicators(
            fear=0.0,
            hopelessness=0.0,
            isolation=0.0,
            helplessness=0.0,
            intimidation=0.0,
            sadness=0.0,
            anxiety=0.0,
        )
        return empty_indicators, {}

    evidence: dict[str, tuple[str, ...]] = {}
    scores: dict[str, float] = {}

    for category, patterns in DISTRESS_LEXICONS.items():
        matches = find_matched_terms(clean_text, patterns)
        scores[category] = calculate_category_score(len(matches))
        if matches:
            evidence[category] = matches

    indicators = DistressIndicators(
        fear=scores.get("fear", 0.0),
        hopelessness=scores.get("hopelessness", 0.0),
        isolation=scores.get("isolation", 0.0),
        helplessness=scores.get("helplessness", 0.0),
        intimidation=scores.get("intimidation", 0.0),
        sadness=scores.get("sadness", 0.0),
        anxiety=scores.get("anxiety", 0.0),
    )

    return indicators, evidence
