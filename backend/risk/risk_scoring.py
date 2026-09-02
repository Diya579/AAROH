def calculate_risk(features, longitudinal):
    """
    Explainable AAROH risk scoring engine.

    Produces:
        - risk_score: normalized 0-1 score
        - risk_level: LOW / MODERATE / HIGH
        - reasons: human-readable contributing factors
    """

    score = 0.0
    reasons = []

    # =========================================================
    # 1. CURRENT DISTRESS
    # =========================================================

    current_distress = longitudinal.get("current_distress")

    if current_distress is not None:

        if current_distress >= 0.75:
            score += 0.30
            reasons.append("Current distress is high")

        elif current_distress >= 0.50:
            score += 0.20
            reasons.append("Current distress is elevated")

        elif current_distress >= 0.25:
            score += 0.10
            reasons.append("Current distress is present")

    # =========================================================
    # 2. CHANGE FROM BASELINE
    # =========================================================

    baseline_change = longitudinal.get(
        "distress_from_baseline"
    )

    if baseline_change is not None:

        if baseline_change >= 0.50:
            score += 0.25
            reasons.append(
                "Distress is substantially above baseline"
            )

        elif baseline_change >= 0.25:
            score += 0.15
            reasons.append(
                "Distress is above baseline"
            )

    # =========================================================
    # 3. RECENT DISTRESS CHANGE
    # =========================================================

    distress_change = longitudinal.get(
        "distress_change"
    )

    if distress_change is not None:

        if distress_change >= 0.50:
            score += 0.20
            reasons.append(
                "Distress increased sharply"
            )

        elif distress_change >= 0.25:
            score += 0.15
            reasons.append(
                "Distress increased from the previous interaction"
            )

    # =========================================================
    # 4. TEXTUAL RISK INDICATORS
    # =========================================================

    if features.get("fear", 0) > 0:
        score += 0.10
        reasons.append(
            "Fear indicators detected"
        )

    if features.get("intimidation", 0) > 0:
        score += 0.10
        reasons.append(
            "Intimidation indicators detected"
        )

    if features.get("hopelessness", 0) > 0:
        score += 0.10
        reasons.append(
            "Hopelessness indicators detected"
        )

    if features.get("isolation", 0) > 0:
        score += 0.05
        reasons.append(
            "Isolation indicators detected"
        )

    # =========================================================
    # 5. BEHAVIOURAL RISK INDICATORS
    # =========================================================

    if features.get(
        "sleep_disturbance", 0
    ) >= 0.50:

        score += 0.10

        reasons.append(
            "Sleep disturbance detected"
        )

    if features.get(
        "low_social_support", 0
    ) >= 0.50:

        score += 0.10

        reasons.append(
            "Low social support detected"
        )

    # =========================================================
    # 6. ENGAGEMENT / DATA QUALITY
    # =========================================================

    if features.get(
        "data_quality_insufficient", 0
    ) == 1:

        reasons.append(
            "Data quality is insufficient"
        )

    # =========================================================
    # 7. NORMALIZE SCORE
    # =========================================================

    score = max(
        0.0,
        min(score, 1.0)
    )

    score = round(
        score,
        2
    )

    # =========================================================
    # 8. RISK CLASSIFICATION
    # =========================================================

    if score >= 0.70:

        risk_level = "HIGH"

    elif score >= 0.40:

        risk_level = "MODERATE"

    else:

        risk_level = "LOW"

    # =========================================================
    # 9. FALLBACK EXPLANATION
    # =========================================================

    if not reasons:

        reasons.append(
            "No significant risk indicators detected"
        )

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "reasons": reasons
    }