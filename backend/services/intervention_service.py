"""
AAROH — Centralized Intervention & Outcome Service
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Provides high-level service functions for FastAPI endpoints and internal callers,
bridging API payloads directly with DatabaseOperationalService.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models import Intervention, Outcome, Case
from backend.interventions.db_service import db_operational_service
from backend.interventions.scheduler import overdue_scanner


def create_intervention(db: Session, payload: Any) -> Intervention:
    """Creates an intervention record directly or processes via operational engine."""
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
    db_obj = Intervention(**data)
    db.add(db_obj)
    db.flush()
    db.refresh(db_obj)
    return db_obj


def get_intervention(db: Session, intervention_id: int) -> Optional[Intervention]:
    """Retrieves an intervention by primary key."""
    return db.query(Intervention).filter(Intervention.id == intervention_id).first()


def get_interventions(
    db: Session,
    user: Optional[Any] = None,
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Intervention]:
    """Retrieves interventions with optional case and user scope filtering."""
    query = db.query(Intervention)
    if user and hasattr(user, "role"):
        role = str(user.role).upper()
        if role in ("CASE_OFFICER", "COUNSELLOR", "DISTRICT_OFFICIAL") and hasattr(user, "district") and user.district:
            query = query.join(Case, Intervention.case_id == Case.id).filter(Case.district == user.district)
    if case_id:
        query = query.filter(Intervention.case_id == case_id)
    return query.order_by(Intervention.id.desc()).offset(skip).limit(limit).all()


def update_intervention(db: Session, intervention_id: int, payload: Any) -> Optional[Intervention]:
    """Updates an existing intervention record."""
    db_obj = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not db_obj:
        return None
    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else dict(payload)
    for k, v in data.items():
        if hasattr(db_obj, k):
            setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_outcome(db: Session, payload: Any) -> Outcome:
    """Creates and persists an outcome record using operational rules."""
    data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
    outcome = Outcome(**data)
    db.add(outcome)
    db.flush()
    db.refresh(outcome)
    return outcome


def get_outcomes(
    db: Session,
    user: Optional[Any] = None,
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Outcome]:
    """Retrieves outcomes with optional case and user scope filtering."""
    query = db.query(Outcome)
    if user and hasattr(user, "role"):
        role = str(user.role).upper()
        if role in ("CASE_OFFICER", "COUNSELLOR", "DISTRICT_OFFICIAL") and hasattr(user, "district") and user.district:
            query = query.join(Case, Outcome.case_id == Case.id).filter(Case.district == user.district)
    if case_id:
        query = query.filter(Outcome.case_id == case_id)
    return query.order_by(Outcome.recorded_at.desc()).offset(skip).limit(limit).all()


def check_overdue(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """Triggers an immediate SLA overdue scan cycle."""
    return overdue_scanner.scan_once(db=db)
