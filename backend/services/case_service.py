"""
AAROH — Case Service

Database operations for the cases table.
Business logic lives here, not in route handlers.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models import (
    Case,
    CaseEvent,
    Interaction,
    Prediction,
    Intervention,
    Outcome,
)
from backend.core.security import apply_scope_filter
from backend.schemas.case import CaseCreate, CaseUpdate

logger = logging.getLogger(__name__)


def create_case(db: Session, payload: CaseCreate) -> Case:
    """Insert a new case row. Raises ValueError on duplicate case_id."""
    row = Case(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Case with case_id '{payload.case_id}' already exists.")
    return row


def get_case(db: Session, case_id: int) -> Optional[Case]:
    """Fetch a single case by its DB primary key."""
    return db.query(Case).filter(Case.id == case_id).first()


def list_cases(
    db: Session,
    user,
    skip: int = 0,
    limit: int = 50,
    district: Optional[str] = None,
    state: Optional[str] = None,
) -> list[Case]:
    """Return a paginated, optionally-filtered list of cases."""
    q = db.query(Case)
    
    # Apply RBAC scope filter
    q = apply_scope_filter(q, Case, user)
    
    if district:
        q = q.filter(Case.district == district)
    if state:
        q = q.filter(Case.state == state)
    return q.offset(skip).limit(limit).all()


def update_case(db: Session, case_id: int, payload: CaseUpdate) -> Optional[Case]:
    """Update fields on an existing case. Returns None if not found."""
    row = db.query(Case).filter(Case.id == case_id).first()
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


def delete_case(db: Session, case_id: int) -> bool:
    """Delete a case by DB id. Returns True if deleted, False if not found."""
    row = db.query(Case).filter(Case.id == case_id).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def get_case_timeline(db: Session, case_id: int) -> list[dict]:
    """
    Aggregate all timeline-relevant records for a case, sorted chronologically.

    Each entry is tagged with a `type` string and a `timestamp` for sorting.
    The caller (the route handler) already verified the case exists and that
    the requesting user has access — this function only queries and formats.

    Timeline entry types:
        "case_event"    — CaseEvent rows (stage transitions, admin notes)
        "interaction"   — Interaction rows (voice/text check-ins)
        "prediction"    — Prediction rows (ML model outputs)
        "intervention"  — Intervention rows (assigned actions)
        "outcome"       — Outcome rows (intervention results)
    """
    entries: list[dict] = []

    # Case events
    events = (
        db.query(CaseEvent)
        .filter(CaseEvent.case_id == case_id)
        .order_by(CaseEvent.event_date)
        .all()
    )
    for e in events:
        entries.append({
            "type": "case_event",
            "timestamp": e.event_date.isoformat() if e.event_date else None,
            "event_type": e.event_type,
            "case_stage": e.case_stage,
            "description": e.description,
        })

    # Interactions
    interactions = (
        db.query(Interaction)
        .filter(Interaction.case_id == case_id)
        .order_by(Interaction.interaction_date)
        .all()
    )
    for i in interactions:
        entries.append({
            "type": "interaction",
            "timestamp": i.interaction_date.isoformat() if i.interaction_date else None,
            "channel": i.channel,
            "language": i.language,
            "voice_available": i.voice_available,
            "response_completed": i.response_completed,
        })

    # Predictions
    predictions = (
        db.query(Prediction)
        .filter(Prediction.case_id == case_id)
        .order_by(Prediction.prediction_date)
        .all()
    )
    for p in predictions:
        entries.append({
            "type": "prediction",
            "timestamp": p.prediction_date.isoformat() if p.prediction_date else None,
            "escalation_probability": p.escalation_probability,
            "risk_level": p.risk_level,
            "confidence": p.confidence,
            "target_horizon_days": p.target_horizon_days,
        })

    # Interventions
    interventions = (
        db.query(Intervention)
        .filter(Intervention.case_id == case_id)
        .order_by(Intervention.created_at)
        .all()
    )
    for iv in interventions:
        entries.append({
            "type": "intervention",
            "timestamp": iv.created_at.isoformat() if iv.created_at else None,
            "intervention_type": iv.intervention_type,
            "status": iv.status,
            "assigned_to": iv.assigned_to,
        })

    # Outcomes
    # Outcome.case_id references Case.id (integer FK)
    outcomes = (
        db.query(Outcome)
        .filter(Outcome.case_id == case_id)
        .order_by(Outcome.recorded_at)
        .all()
    )
    for o in outcomes:
        entries.append({
            "type": "outcome",
            "timestamp": o.recorded_at.isoformat() if o.recorded_at else None,
            "outcome_type": o.outcome_type,
            "completed": o.completed,
        })

    # Sort by timestamp — entries with no timestamp (interventions) go last
    entries.sort(key=lambda x: (x["timestamp"] is None, x["timestamp"] or ""))

    return entries
