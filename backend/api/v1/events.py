"""
AAROH — CaseEvent API Endpoints

Endpoints for the case_events table.
"""

from typing import List, Optional

from backend.schemas.error import common_responses
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role, verify_case_id_access
from backend.core.errors import raise_not_found
from backend.schemas.event import EventCreate, EventResponse
from backend.services import event_service

router = APIRouter(tags=["Events"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/events", responses=common_responses,
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("COUNSELLOR", "SYSTEM_SERVICE", "ADMIN"))],
)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new case event."""
    try:
        return event_service.create_event(db, payload)
    except Exception as e:
        db.rollback()
        # Prevent leaking raw DB errors.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create event. Ensure case_id is valid."
        )


@router.get(
    "/events", responses=common_responses,
    response_model=List[EventResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def list_events(
    case_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List events with pagination and optional case filtering."""
    return event_service.list_events(db, user=user, case_id=case_id, skip=skip, limit=limit)


@router.get(
    "/events/{event_id}", responses=common_responses,
    response_model=EventResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch a specific event by its DB ID."""
    row = event_service.get_event(db, event_id)
    if row is None:
        raise_not_found("Event", event_id)
    verify_case_id_access(row.case_id, user, db)
    return row
