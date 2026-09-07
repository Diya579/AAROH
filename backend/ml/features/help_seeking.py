"""Help-seeking indicator extraction (Slice 2.2).

Detects observable help-seeking, support request, and emergency language.
Returns structured HelpSeekingIndicators and matched terms for explainability.
"""

from __future__ import annotations

from backend.ml.features.distress import calculate_category_score
from backend.ml.features.lexicons import HELP_SEEKING_LEXICONS, find_matched_terms
from backend.ml.features.types import HelpSeekingIndicators


def extract_help_seeking_indicators(
    clean_text: str,
) -> tuple[HelpSeekingIndicators, dict[str, tuple[str, ...]]]:
    """Extracts help-seeking indicators from cleaned text.

    Returns:
    - HelpSeekingIndicators: numeric features bounded in [0.0, 1.0]
    - Matched evidence dictionary: category -> tuple of matched phrases
    """
    if not clean_text or not clean_text.strip():
        empty_indicators = HelpSeekingIndicators(
            asking_for_help=0.0,
            requesting_support=0.0,
            emergency_language=0.0,
        )
        return empty_indicators, {}

    evidence: dict[str, tuple[str, ...]] = {}
    scores: dict[str, float] = {}

    for category, patterns in HELP_SEEKING_LEXICONS.items():
        matches = find_matched_terms(clean_text, patterns)
        scores[category] = calculate_category_score(len(matches))
        if matches:
            evidence[category] = matches

    indicators = HelpSeekingIndicators(
        asking_for_help=scores.get("asking_for_help", 0.0),
        requesting_support=scores.get("requesting_support", 0.0),
        emergency_language=scores.get("emergency_language", 0.0),
    )

    return indicators, evidence
