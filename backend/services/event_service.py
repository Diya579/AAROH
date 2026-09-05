"""
AAROH — Event Service

Database operations for the case_events table.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import CaseEvent
from backend.core.security import apply_scope_filter
from backend.schemas.event import EventCreate


def create_event(db: Session, payload: EventCreate) -> CaseEvent:
    """Insert a new case event row."""
    row = CaseEvent(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_event(db: Session, event_id: int) -> Optional[CaseEvent]:
    """Fetch a single event by its DB primary key."""
    return db.query(CaseEvent).filter(CaseEvent.id == event_id).first()


def list_events(
    db: Session,
    user,
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[CaseEvent]:
    """Return a paginated list of case events, optionally filtered by case_id."""
    query = db.query(CaseEvent)
    
    # Apply RBAC scope filter
    query = apply_scope_filter(query, CaseEvent, user)
    
    if case_id is not None:
        query = query.filter(CaseEvent.case_id == case_id)
    return query.offset(skip).limit(limit).all()
