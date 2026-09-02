from database import SessionLocal
from models import (
    Case,
    Prediction,
    Consent,
    Intervention,
    DistressState
)


def determine_intervention(
    risk_level,
    escalation_probability,
    trajectory,
    monitoring_consent=True
):
    """
    Determine the appropriate AAROH response
    from the current risk state.

    This is an operational decision layer,
    not a clinical diagnosis.
    """

    if not monitoring_consent:
        return {
            "intervention_type": "NO_AUTOMATED_INTERVENTION",
            "priority": "NONE",
            "reason": "Monitoring consent is not available."
        }

    # -----------------------------------------
    # HIGH ESCALATION
    # -----------------------------------------

    if (
        risk_level == "HIGH"
        or escalation_probability >= 0.75
        or trajectory == "RAPIDLY_WORSENING"
    ):
        return {
            "intervention_type": "PRIORITY_HUMAN_REVIEW",
            "priority": "URGENT",
            "reason": (
                "High-risk or rapidly worsening indicators "
                "require priority human review."
            )
        }

    # -----------------------------------------
    # MODERATE ESCALATION
    # -----------------------------------------

    if (
        risk_level == "MODERATE"
        or escalation_probability >= 0.40
        or trajectory == "WORSENING"
    ):
        return {
            "intervention_type": "HUMAN_FOLLOW_UP",
            "priority": "HIGH",
            "reason": (
                "Elevated distress or worsening trajectory "
                "requires human follow-up."
            )
        }

    # -----------------------------------------
    # IMPROVING
    # -----------------------------------------

    if trajectory in (
        "IMPROVING",
        "RAPIDLY_IMPROVING"
    ):
        return {
            "intervention_type": "CONTINUE_MONITORING",
            "priority": "LOW",
            "reason": (
                "Distress trajectory is improving; "
                "continue monitoring."
            )
        }

    # -----------------------------------------
    # LOW / STABLE
    # -----------------------------------------

    return {
        "intervention_type": "ROUTINE_MONITORING",
        "priority": "ROUTINE",
        "reason": (
            "No significant escalation signal detected; "
            "continue routine monitoring."
        )
    }


def create_intervention(case_id):
    """
    Generate and persist the recommended intervention
    for a case using its latest prediction and distress state.
    """

    db = SessionLocal()

    try:

        # -----------------------------------------
        # GET CASE
        # -----------------------------------------

        case = (
            db.query(Case)
            .filter(Case.id == case_id)
            .first()
        )

        if not case:
            raise ValueError(
                f"Case {case_id} not found."
            )

        # -----------------------------------------
        # GET LATEST PREDICTION
        # -----------------------------------------

        prediction = (
            db.query(Prediction)
            .filter(
                Prediction.case_id == case_id
            )
            .order_by(
                Prediction.prediction_date.desc()
            )
            .first()
        )

        if not prediction:
            raise ValueError(
                f"No prediction available for case {case_id}."
            )

        # -----------------------------------------
        # GET LATEST CONSENT
        # -----------------------------------------

        consent = (
            db.query(Consent)
            .filter(
                Consent.case_id == case_id
            )
            .order_by(
                Consent.id.desc()
            )
            .first()
        )

        monitoring_consent = (
            case.monitoring_consent
            if consent is None
            else consent.monitoring_consent
        )

        # -----------------------------------------
        # GET CURRENT TRAJECTORY
        # -----------------------------------------

        distress_state = (
            db.query(DistressState)
            .filter(
                DistressState.case_id == case_id
            )
            .order_by(
                DistressState.observation_date.desc()
            )
            .first()
        )

        trajectory = (
            distress_state.trajectory
            if distress_state
            else "STABLE"
        )

        # -----------------------------------------
        # DETERMINE RISK LEVEL
        # -----------------------------------------

        probability = (
            prediction.escalation_probability or 0.0
        )

        if probability >= 0.75:
            risk_level = "HIGH"

        elif probability >= 0.40:
            risk_level = "MODERATE"

        else:
            risk_level = "LOW"

        # -----------------------------------------
        # DETERMINE INTERVENTION
        # -----------------------------------------

        decision = determine_intervention(
            risk_level=risk_level,
            escalation_probability=probability,
            trajectory=trajectory,
            monitoring_consent=monitoring_consent
        )

        # -----------------------------------------
        # PREVENT DUPLICATE PENDING INTERVENTIONS
        # -----------------------------------------

        existing_intervention = (
            db.query(Intervention)
            .filter(
                Intervention.case_id == case_id,
                Intervention.status == "PENDING",
                Intervention.intervention_type
                == decision["intervention_type"]
            )
            .order_by(
                Intervention.id.desc()
            )
            .first()
        )

        if existing_intervention:

            return {
                "intervention_id": existing_intervention.id,
                "case_id": case_id,
                "intervention_type": (
                    existing_intervention.intervention_type
                ),
                "priority": decision["priority"],
                "status": existing_intervention.status,
                "reason": decision["reason"],
                "trajectory": trajectory,
                "escalation_probability": probability,
                "existing": True
            }

        # -----------------------------------------
        # CREATE NEW INTERVENTION
        # -----------------------------------------

        intervention = Intervention(
            case_id=case_id,
            intervention_type=decision[
                "intervention_type"
            ],
            status="PENDING",
            assigned_to=None
        )

        db.add(intervention)
        db.commit()
        db.refresh(intervention)

        return {
            "intervention_id": intervention.id,
            "case_id": case_id,
            "intervention_type": (
                decision["intervention_type"]
            ),
            "priority": decision["priority"],
            "status": intervention.status,
            "reason": decision["reason"],
            "trajectory": trajectory,
            "escalation_probability": probability,
            "existing": False
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()