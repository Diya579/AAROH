"""Explainability and Evidence Generation for Dynamic Distress Model (Slice 3.6).

Produces structured, machine-readable evidence explaining distress score predictions
grounded strictly in observable model inputs:
- Emotion probability drivers (high distress vs. protective factors)
- Lexicon-derived distress indicator matches
- Behavioural disruptions (sleep, safety, withdrawal)
- Engagement level shifts and check-in regularity
- Modality contribution balance (text vs. tabular vs. audio)

Strict Clinical Invariant:
- Machine-readable evidence provides decision support reasoning only.
- It NEVER states or implies a psychiatric diagnosis, escalation, or clinical prognosis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union

from backend.ml.features.distress import extract_distress_indicators
from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    ENGAGEMENT_COUNT,
    LABEL_DISCLAIMER,
    DistressInputRecord,
)

# Canonical emotion categories impacting distress
HIGH_DISTRESS_EMOTIONS = {
    "fear": 0.25,
    "grief": 0.25,
    "sadness": 0.20,
    "nervousness": 0.15,
    "anger": 0.12,
    "disappointment": 0.10,
    "remorse": 0.10,
    "annoyance": 0.08,
    "embarrassment": 0.08,
    "disgust": 0.08,
}

PROTECTIVE_EMOTIONS = {
    "joy": -0.20,
    "optimism": -0.20,
    "relief": -0.15,
    "gratitude": -0.15,
    "love": -0.15,
    "admiration": -0.10,
    "caring": -0.10,
    "approval": -0.08,
    "amusement": -0.08,
}


@dataclass
class DistressEvidence:
    """Structured machine-readable evidence for a distress prediction."""

    distress_score: float
    distress_level: str
    confidence: float
    main_contributors: List[str]
    top_emotion_drivers: List[Dict[str, Any]]
    protective_factors: List[Dict[str, Any]]
    lexicon_matches: Dict[str, List[str]]
    modality_weights: Dict[str, float]
    model_version: str
    label_disclaimer: str = LABEL_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        """Serializes evidence into a clean dictionary."""
        return asdict(self)


def calculate_distress_confidence(
    score: float,
    thresholds: Dict[str, float],
    modality_weights: Optional[Dict[str, float]] = None,
) -> float:
    """Calculates a heuristic model confidence score in [0.50, 0.99] based on decision margin.

    Predictions further from threshold boundaries have higher decision confidence.
    """
    low = thresholds.get("low", 0.25)
    mod = thresholds.get("moderate", 0.55)
    high = thresholds.get("high", 0.80)

    # Calculate distance to nearest threshold boundary
    dists = [abs(score - low), abs(score - mod), abs(score - high)]
    min_dist = min(dists)

    # Base confidence: 0.70 + margin bonus
    margin_bonus = min(0.25, min_dist * 1.5)
    conf = 0.70 + margin_bonus

    # Slight penalty if all active modalities have zero weight
    if modality_weights:
        active_sum = sum(modality_weights.values())
        if active_sum <= 0.01:
            conf -= 0.15

    return round(float(max(0.50, min(0.99, conf))), 3)


def generate_distress_evidence(
    distress_score: float,
    distress_level: str,
    thresholds: Dict[str, float],
    model_version: str = "aaroh-distress-v1",
    raw_text: Optional[str] = None,
    emotion_probabilities: Optional[Dict[str, float]] = None,
    previous_emotion_probabilities: Optional[Dict[str, float]] = None,
    behavioural_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
    engagement_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
    modality_weights: Optional[Dict[str, float]] = None,
) -> DistressEvidence:
    """Computes transparent, machine-readable explanation evidence grounded in actual inputs."""
    main_contributors: List[str] = []
    top_emotion_drivers: List[Dict[str, Any]] = []
    protective_factors: List[Dict[str, Any]] = []
    lexicon_matches: Dict[str, List[str]] = {}

    # 1. Analyze Emotion Probabilities
    if emotion_probabilities:
        # High distress emotion drivers
        for emo, weight in HIGH_DISTRESS_EMOTIONS.items():
            prob = float(emotion_probabilities.get(emo, 0.0))
            if prob >= 0.20:
                impact = round(prob * weight, 3)
                top_emotion_drivers.append({
                    "emotion": emo,
                    "probability": round(prob, 4),
                    "impact": impact,
                })
                if prob >= 0.40:
                    main_contributors.append(f"High {emo} (probability={prob:.2f})")

        # Sort drivers by descending impact
        top_emotion_drivers.sort(key=lambda x: x["impact"], reverse=True)

        # Protective emotions
        for emo, weight in PROTECTIVE_EMOTIONS.items():
            prob = float(emotion_probabilities.get(emo, 0.0))
            if prob >= 0.20:
                protective_factors.append({
                    "emotion": emo,
                    "probability": round(prob, 4),
                    "mitigation": round(abs(prob * weight), 3),
                })
        protective_factors.sort(key=lambda x: x["mitigation"], reverse=True)

        # Check for rapid increase in negative emotions if previous emotions provided
        if previous_emotion_probabilities:
            curr_neg = sum(emotion_probabilities.get(e, 0.0) for e in ("fear", "sadness", "grief", "anger"))
            prev_neg = sum(previous_emotion_probabilities.get(e, 0.0) for e in ("fear", "sadness", "grief", "anger"))
            delta = curr_neg - prev_neg
            if delta >= 0.20:
                main_contributors.append(f"Rapid increase in negative emotions (delta=+{delta:.2f})")

    # 2. Analyze Lexicon Distress Language Signals in Text
    if raw_text and raw_text.strip():
        indicators, matched_phrases = extract_distress_indicators(raw_text)
        for cat, phrases in matched_phrases.items():
            if phrases:
                lexicon_matches[cat] = list(phrases)
        if lexicon_matches:
            matched_cats = list(lexicon_matches.keys())[:3]
            sample_terms = [t for phrases in lexicon_matches.values() for t in phrases][:3]
            terms_str = ", ".join(f"'{t}'" for t in sample_terms)
            main_contributors.append(f"Distress language detected ({', '.join(matched_cats)}: {terms_str})")

    # 3. Analyze Behavioural Features
    if behavioural_features:
        if isinstance(behavioural_features, (list, tuple)):
            # Index 0: safety distress, Index 1: sleep disturbance, Index 2: fear intensity
            if len(behavioural_features) > 0 and behavioural_features[0] is not None:
                val = float(behavioural_features[0])
                if val >= 0.50:
                    main_contributors.append(f"Elevated behavioural safety distress signal (score={val:.2f})")
            if len(behavioural_features) > 1 and behavioural_features[1] is not None:
                val = float(behavioural_features[1])
                if val >= 0.60:
                    main_contributors.append("Observable sleep disturbance reported")
            if len(behavioural_features) > 2 and behavioural_features[2] is not None:
                val = float(behavioural_features[2])
                if val >= 0.60:
                    main_contributors.append(f"Severe fear intensity reported (intensity={val:.2f})")
        elif isinstance(behavioural_features, dict):
            for k, v in behavioural_features.items():
                if v is not None and float(v) >= 0.60:
                    main_contributors.append(f"Elevated {k} (value={float(v):.2f})")

    # 4. Analyze Engagement Features
    if engagement_features:
        if isinstance(engagement_features, (list, tuple)):
            # Index 7: engagement drop (registry idx 33), Index 0: missed checkins
            if len(engagement_features) > 7 and engagement_features[7] is not None:
                val = float(engagement_features[7])
                if val >= 0.50:
                    main_contributors.append("Low engagement / engagement drop detected")
            if len(engagement_features) > 0 and engagement_features[0] is not None:
                val = float(engagement_features[0])
                if val >= 2.0:
                    main_contributors.append(f"Multiple missed check-in events (count={int(val)})")
        elif isinstance(engagement_features, dict):
            for k, v in engagement_features.items():
                if v is not None and float(v) >= 0.60:
                    main_contributors.append(f"Observed engagement shift: {k} (value={float(v):.2f})")

    # If no specific high-amplitude contributors, note baseline state
    if not main_contributors:
        if distress_score < thresholds.get("low", 0.25):
            main_contributors.append("Stable emotional baseline with absence of acute distress indicators")
        else:
            main_contributors.append("Moderate aggregate distress across multiple low-amplitude signals")

    # Calculate confidence
    confidence = calculate_distress_confidence(distress_score, thresholds, modality_weights)

    return DistressEvidence(
        distress_score=round(distress_score, 4),
        distress_level=distress_level,
        confidence=confidence,
        main_contributors=main_contributors,
        top_emotion_drivers=top_emotion_drivers,
        protective_factors=protective_factors,
        lexicon_matches=lexicon_matches,
        modality_weights=modality_weights or {"tabular": 0.33, "text": 0.33, "audio": 0.34},
        model_version=model_version,
    )
