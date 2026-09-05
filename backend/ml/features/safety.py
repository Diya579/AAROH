"""Safety and urgency indicator extraction (Slice 2.2).

Detects observable danger-related wording and temporal urgency signals.
Returns structured SafetyIndicators and matched terms for explainability.
"""

from __future__ import annotations

from backend.ml.features.distress import calculate_category_score
from backend.ml.features.lexicons import SAFETY_LEXICONS, find_matched_terms
from backend.ml.features.types import SafetyIndicators


def extract_safety_indicators(
    clean_text: str,
) -> tuple[SafetyIndicators, dict[str, tuple[str, ...]]]:
    """Extracts safety indicators from cleaned text.

    Returns:
    - SafetyIndicators: numeric features bounded in [0.0, 1.0]
    - Matched evidence dictionary: category -> tuple of matched phrases
    """
    if not clean_text or not clean_text.strip():
        empty_indicators = SafetyIndicators(
            urgency=0.0,
            danger_related_wording=0.0,
        )
        return empty_indicators, {}

    evidence: dict[str, tuple[str, ...]] = {}
    scores: dict[str, float] = {}

    for category, patterns in SAFETY_LEXICONS.items():
        matches = find_matched_terms(clean_text, patterns)
        scores[category] = calculate_category_score(len(matches))
        if matches:
            evidence[category] = matches

    indicators = SafetyIndicators(
        urgency=scores.get("urgency", 0.0),
        danger_related_wording=scores.get("danger_related_wording", 0.0),
    )

    return indicators, evidence
