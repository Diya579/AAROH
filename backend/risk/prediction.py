from datetime import datetime

from database import SessionLocal
from models import (
    Interaction,
    DistressState,
    Prediction
)


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def calculate_escalation_probability(
    current_distress,
    trajectory,
    recent_distress_change,
    baseline_deviation
):
    """
    Transparent baseline 7-day escalation model.

    IMPORTANT:
    This is an interpretable prototype prediction model.
    It is NOT a clinical diagnostic model.

    The architecture is intentionally designed so that
    this rule-based baseline can later be replaced by
    a trained ML model without changing the Prediction
    database contract.
    """

    probability = 0.0
    reasons = []

    # -----------------------------------------
    # CURRENT DISTRESS
    # -----------------------------------------

    if current_distress >= 0.75:

        probability += 0.35

        reasons.append(
            "Current distress is very high"
        )

    elif current_distress >= 0.55:

        probability += 0.25

        reasons.append(
            "Current distress is elevated"
        )

    elif current_distress >= 0.40:

        probability += 0.12

        reasons.append(
            "Current distress is moderately elevated"
        )


    # -----------------------------------------
    # TRAJECTORY
    # -----------------------------------------

    if trajectory == "RAPIDLY_WORSENING":

        probability += 0.30

        reasons.append(
            "Distress is rapidly worsening"
        )

    elif trajectory == "WORSENING":

        probability += 0.15

        reasons.append(
            "Distress is worsening"
        )

    elif trajectory == "IMPROVING":

        probability -= 0.10

        reasons.append(
            "Distress is improving"
        )

    elif trajectory == "RAPIDLY_IMPROVING":

        probability -= 0.15

        reasons.append(
            "Distress is rapidly improving"
        )


    # -----------------------------------------
    # RECENT CHANGE
    # -----------------------------------------

    if recent_distress_change is not None:

        if recent_distress_change >= 0.15:

            probability += 0.20

            reasons.append(
                "Recent distress increased sharply"
            )

        elif recent_distress_change >= 0.05:

            probability += 0.10

            reasons.append(
                "Recent distress increased"
            )


    # -----------------------------------------
    # BASELINE DEVIATION
    # -----------------------------------------

    if baseline_deviation is not None:

        if baseline_deviation >= 0.30:

            probability += 0.15

            reasons.append(
                "Distress is substantially above baseline"
            )

        elif baseline_deviation >= 0.15:

            probability += 0.07

            reasons.append(
                "Distress is above baseline"
            )


    # -----------------------------------------
    # CLAMP
    # -----------------------------------------

    probability = clamp(probability)


    # -----------------------------------------
    # CONFIDENCE
    # -----------------------------------------

    # Confidence is intentionally conservative.
    #
    # It represents how much longitudinal evidence
    # is available, NOT prediction accuracy.

    confidence = 0.50

    if current_distress is not None:
        confidence += 0.10

    if trajectory != "STABLE":
        confidence += 0.10

    if recent_distress_change is not None:
        confidence += 0.10

    if baseline_deviation is not None:
        confidence += 0.10

    confidence = clamp(
        confidence,
        0.0,
        1.0
    )


    return {
        "escalation_probability": round(
            probability,
            3
        ),

        "confidence": round(
            confidence,
            3
        ),

        "reasons": reasons
    }


def generate_prediction(case_id):
    """
    Generate a 7-day escalation prediction
    using the latest available distress state.
    """

    db = SessionLocal()

    try:

        # -----------------------------------------
        # GET LATEST DISTRESS STATE
        # -----------------------------------------

        latest_state = (
            db.query(DistressState)
            .filter(
                DistressState.case_id == case_id
            )
            .order_by(
                DistressState.observation_date.desc()
            )
            .first()
        )

        if latest_state is None:

            raise ValueError(
                f"No distress state found for case {case_id}"
            )


        # -----------------------------------------
        # GET PREVIOUS DISTRESS STATE
        # -----------------------------------------

        previous_state = (
            db.query(DistressState)
            .filter(
                DistressState.case_id == case_id,
                DistressState.observation_date
                < latest_state.observation_date
            )
            .order_by(
                DistressState.observation_date.desc()
            )
            .first()
        )


        # -----------------------------------------
        # RECENT CHANGE
        # -----------------------------------------

        if previous_state is not None:

            recent_change = (
                latest_state.distress_score
                - previous_state.distress_score
            )

        else:

            recent_change = None


        # -----------------------------------------
        # BASELINE
        # -----------------------------------------

        all_states = (
            db.query(DistressState)
            .filter(
                DistressState.case_id == case_id
            )
            .order_by(
                DistressState.observation_date.asc()
            )
            .all()
        )

        baseline = (
            all_states[0].distress_score
            if all_states
            else latest_state.distress_score
        )


        baseline_deviation = (
            latest_state.distress_score
            - baseline
        )


        # -----------------------------------------
        # CALCULATE PREDICTION
        # -----------------------------------------

        result = calculate_escalation_probability(

            current_distress=(
                latest_state.distress_score
            ),

            trajectory=(
                latest_state.trajectory
            ),

            recent_distress_change=(
                recent_change
            ),

            baseline_deviation=(
                baseline_deviation
            )
        )


        # -----------------------------------------
        # SAVE PREDICTION
        # -----------------------------------------

        prediction = Prediction(

            case_id=case_id,

            prediction_date=datetime.utcnow(),

            escalation_probability=(
                result["escalation_probability"]
            ),

            target_horizon_days=7,

            confidence=result["confidence"]
        )

        db.add(prediction)

        db.commit()

        db.refresh(prediction)


        return {
            "prediction_id": prediction.id,
            "case_id": case_id,
            "escalation_probability": (
                result["escalation_probability"]
            ),
            "target_horizon_days": 7,
            "confidence": result["confidence"],
            "reasons": result["reasons"]
        }

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()