"""
AAROH — Legacy Intervention Engine Adapter
Author: Preet

Adapts existing callers to the frozen operational subsystem
(backend.interventions.engine and backend.interventions.db_service).
Preserves consent, confidence, and district-aware routing without recalculating ML probabilities.
"""

from typing import Any, Optional, cast
from backend.database import SessionLocal
from backend.interventions.engine import InterventionEngine, InterventionType, PriorityLevel
from backend.interventions.db_service import db_operational_service


def determine_intervention(
    risk_level: str,
    escalation_probability: float,
    trajectory: str,
    monitoring_consent: bool = True,
    confidence: float = 1.0,
    ml_status: str = "SUCCESS",
) -> dict[str, Any]:
    """
    Determines recommended operational intervention by delegating to InterventionEngine.
    Enforces consent gating and uncertainty safety (LOW_CONFIDENCE/ABSTAINED -> PRIORITY_HUMAN_REVIEW).
    """
    engine = InterventionEngine()
    decision = engine.evaluate(
        case_id="TEMP-CASE",
        risk_level=risk_level,
        escalation_probability=escalation_probability,
        trajectory=trajectory,
        confidence=confidence,
        monitoring_consent=monitoring_consent,
        ml_status=ml_status,
    )
    return {
        "intervention_type": decision.intervention_type.value,
        "priority": decision.priority.value,
        "reason": (
            decision.reason.abstention_reason
            if decision.reason.abstention_reason
            else f"Risk Level: {risk_level}, Trajectory: {trajectory}, Escalation Probability: {escalation_probability:.2f}"
        ),
        "suggested_categories": [c.value for c in decision.suggested_categories],
    }


def create_intervention(case_id: int | str) -> dict[str, Any]:
    """
    Generates and persists the recommended intervention in PostgreSQL
    using the full operational workflow.
    """
    db = SessionLocal()
    try:
        res = db_operational_service.process_case_intervention(db, case_id)
        # Adapt keys for backward compatibility with legacy scripts
        res["existing"] = res.get("is_duplicate", False)
        return res
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()