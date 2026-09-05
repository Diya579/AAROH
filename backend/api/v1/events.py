"""
AAROH — CaseEvent API Endpoints

Endpoints for the case_events table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
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
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caseworker"))],
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
        # Prevent leaking raw DB errors.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create event. Ensure case_id is valid."
        )


@router.get(
    "/events",
    response_model=List[EventResponse],
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def list_events(
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all events with pagination and optional case filtering."""
    return event_service.list_events(db, case_id=case_id, skip=skip, limit=limit)


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch a specific event by its DB ID."""
    row = event_service.get_event(db, event_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found."
        )
    return row
