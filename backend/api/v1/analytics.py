"""
AAROH — Analytics API

Pre-computed aggregate counts from the DB.
Does NOT perform complex statistical analysis (that belongs to Preet's ML layer).

Endpoints:
    GET /analytics/cases              — aggregate counts by district/state (ADMIN/STATE/NATIONAL)
    GET /analytics/cases/{case_id}   — per-case summary (COUNSELLOR+)
    GET /analytics/district/{district} — district aggregate (DISTRICT_OFFICIAL+)
    GET /analytics/state/{state}     — state aggregate (STATE_OFFICIAL+)
    GET /analytics/national          — national aggregate (NATIONAL_OFFICIAL/ADMIN)
"""

from backend.schemas.error import common_responses
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.core.errors import raise_not_found
from backend.models import Case, Interaction, Prediction, Intervention, Outcome, CaseEvent

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _case_counts(db: Session, user=None) -> dict:
    """Base count queries shared across several aggregate endpoints."""
    q_cases = db.query(func.count(Case.id))
    q_interactions = db.query(func.count(Interaction.id))
    q_predictions = db.query(func.count(Prediction.id))
    q_interventions = db.query(func.count(Intervention.id))
    q_outcomes = db.query(func.count(Outcome.id))

    if user:
        from backend.core.security import apply_scope_filter
        q_cases = apply_scope_filter(q_cases, Case, user)
        q_interactions = apply_scope_filter(q_interactions, Interaction, user)
        q_predictions = apply_scope_filter(q_predictions, Prediction, user)
        q_interventions = apply_scope_filter(q_interventions, Intervention, user)
        q_outcomes = apply_scope_filter(q_outcomes, Outcome, user)

    return {
        "total_cases": q_cases.scalar() or 0,
        "total_interactions": q_interactions.scalar() or 0,
        "total_predictions": q_predictions.scalar() or 0,
        "total_interventions": q_interventions.scalar() or 0,
        "total_outcomes": q_outcomes.scalar() or 0,
    }


# ---------------------------------------------------------------------------
# GET /analytics/cases — summary breakdown by district + state
# ---------------------------------------------------------------------------

@router.get(
    "/cases", responses=common_responses,
    dependencies=[Depends(require_role("ADMIN", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def analytics_cases_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Aggregate case counts grouped by district and state.
    Accessible by ADMIN, STATE_OFFICIAL, NATIONAL_OFFICIAL.
    """
    from backend.core.security import apply_scope_filter

    # Group by district
    query_district = db.query(Case.district, func.count(Case.id).label("count"))
    query_district = apply_scope_filter(query_district, Case, user)
    by_district = query_district.group_by(Case.district).all()

    # Group by state
    query_state = db.query(Case.state, func.count(Case.id).label("count"))
    query_state = apply_scope_filter(query_state, Case, user)
    by_state = query_state.group_by(Case.state).all()

    return {
        "totals": _case_counts(db, user),
        "by_district": [{"district": r.district, "count": r.count} for r in by_district],
        "by_state": [{"state": r.state, "count": r.count} for r in by_state],
    }


# ---------------------------------------------------------------------------
# GET /analytics/cases/{case_id} — per-case summary
# ---------------------------------------------------------------------------

@router.get(
    "/cases/{case_id}", responses=common_responses,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def analytics_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Per-case record counts: interactions, events, predictions, interventions, outcomes."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise_not_found("Case", case_id)
        
    from backend.core.security import verify_case_access
    verify_case_access(case, user, db)

    return {
        "case_id": case_id,
        "case_string_id": case.case_id,
        "district": case.district,
        "state": case.state,
        "counts": {
            "events": db.query(func.count(CaseEvent.id)).filter(CaseEvent.case_id == case_id).scalar() or 0,
            "interactions": db.query(func.count(Interaction.id)).filter(Interaction.case_id == case_id).scalar() or 0,
            "predictions": db.query(func.count(Prediction.id)).filter(Prediction.case_id == case_id).scalar() or 0,
            "interventions": db.query(func.count(Intervention.id)).filter(Intervention.case_id == case_id).scalar() or 0,
            "outcomes": db.query(func.count(Outcome.id)).filter(Outcome.case_id == case_id).scalar() or 0,
        },
    }


# ---------------------------------------------------------------------------
# GET /analytics/district/{district}
# ---------------------------------------------------------------------------

@router.get(
    "/district/{district}", responses=common_responses,
    dependencies=[Depends(require_role("DISTRICT_OFFICIAL", "ADMIN", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def analytics_district(
    district: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Aggregate counts for a specific district."""
    if user.role == "DISTRICT_OFFICIAL" and user.district != district:
        from backend.core.errors import raise_forbidden
        raise_forbidden("OUT_OF_SCOPE", "Cannot access analytics for a different district.")
    case_ids = [
        r.id for r in db.query(Case.id).filter(Case.district == district).all()
    ]
    total_cases = len(case_ids)

    if total_cases == 0:
        return {"district": district, "total_cases": 0, "counts": {}}

    return {
        "district": district,
        "total_cases": total_cases,
        "counts": {
            "interactions": db.query(func.count(Interaction.id)).filter(Interaction.case_id.in_(case_ids)).scalar() or 0,
            "predictions": db.query(func.count(Prediction.id)).filter(Prediction.case_id.in_(case_ids)).scalar() or 0,
            "interventions": db.query(func.count(Intervention.id)).filter(Intervention.case_id.in_(case_ids)).scalar() or 0,
            "outcomes": db.query(func.count(Outcome.id)).filter(Outcome.case_id.in_(case_ids)).scalar() or 0,
        },
    }


# ---------------------------------------------------------------------------
# GET /analytics/state/{state}
# ---------------------------------------------------------------------------

@router.get(
    "/state/{state}", responses=common_responses,
    dependencies=[Depends(require_role("STATE_OFFICIAL", "ADMIN", "NATIONAL_OFFICIAL"))],
)
def analytics_state(
    state: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Aggregate counts for a specific state."""
    if user.role == "STATE_OFFICIAL" and user.state != state:
        from backend.core.errors import raise_forbidden
        raise_forbidden("OUT_OF_SCOPE", "Cannot access analytics for a different state.")
    case_ids = [
        r.id for r in db.query(Case.id).filter(Case.state == state).all()
    ]
    total_cases = len(case_ids)

    if total_cases == 0:
        return {"state": state, "total_cases": 0, "counts": {}}

    return {
        "state": state,
        "total_cases": total_cases,
        "counts": {
            "interactions": db.query(func.count(Interaction.id)).filter(Interaction.case_id.in_(case_ids)).scalar() or 0,
            "predictions": db.query(func.count(Prediction.id)).filter(Prediction.case_id.in_(case_ids)).scalar() or 0,
            "interventions": db.query(func.count(Intervention.id)).filter(Intervention.case_id.in_(case_ids)).scalar() or 0,
            "outcomes": db.query(func.count(Outcome.id)).filter(Outcome.case_id.in_(case_ids)).scalar() or 0,
        },
    }


# ---------------------------------------------------------------------------
# GET /analytics/national
# ---------------------------------------------------------------------------

@router.get(
    "/national", responses=common_responses,
    dependencies=[Depends(require_role("NATIONAL_OFFICIAL", "ADMIN"))],
)
def analytics_national(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """National aggregate: total counts across all states."""
    return {
        "scope": "national",
        "totals": _case_counts(db, user),
    }
