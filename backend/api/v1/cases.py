"""
AAROH — Case API Endpoints

CRUD operations for the cases table.
"""

from typing import List, Optional

from backend.schemas.error import common_responses
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role, verify_case_id_access, verify_case_access
from backend.core.errors import raise_not_found, raise_conflict
from backend.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from backend.services import case_service

router = APIRouter(tags=["Cases"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/cases", responses=common_responses,
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "SYSTEM_SERVICE"))],
)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new case."""
    try:
        return case_service.create_case(db, payload)
    except ValueError as e:
        raise_conflict("CASE_DUPLICATE", str(e))


@router.get(
    "/cases", responses=common_responses,
    response_model=List[CaseResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def list_cases(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return (1–200)"),
    district: Optional[str] = Query(default=None, description="Filter by district"),
    state: Optional[str] = Query(default=None, description="Filter by state"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List cases with pagination and optional district/state filters."""
    return case_service.list_cases(db, user=user, skip=skip, limit=limit, district=district, state=state)


@router.get(
    "/cases/{case_id}", responses=common_responses,
    response_model=CaseResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL", "USER", "VICTIM"))],
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch a specific case by its DB ID."""
    row = case_service.get_case(db, case_id)
    if row is None:
        raise_not_found("Case", case_id)
    verify_case_access(row, user, db)
    return row


@router.patch(
    "/cases/{case_id}", responses=common_responses,
    response_model=CaseResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN"))],
)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Partially update fields on an existing case (all fields optional)."""
    row = case_service.get_case(db, case_id)
    if row is None:
        raise_not_found("Case", case_id)
    verify_case_access(row, user, db)

    updated_row = case_service.update_case(db, case_id, payload)
    return updated_row


@router.delete(
    "/cases/{case_id}", responses=common_responses,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("ADMIN"))],
)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a case by its DB ID."""
    row = case_service.get_case(db, case_id)
    if row is None:
        raise_not_found("Case", case_id)
    verify_case_access(row, user, db)

    case_service.delete_case(db, case_id)


@router.get(
    "/cases/{case_id}/timeline", responses=common_responses,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL", "USER", "VICTIM"))],
)
def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Fetch real chronological timeline for a case.

    Aggregates CaseEvent, Interaction, Prediction, Intervention, and Outcome
    records — each tagged with a type and sorted by timestamp ascending.
    """
    row = case_service.get_case(db, case_id)
    if row is None:
        raise_not_found("Case", case_id)
    verify_case_access(row, user, db)

    timeline = case_service.get_case_timeline(db, case_id)
    return {
        "case_id": case_id,
        "case_string_id": row.case_id,
        "count": len(timeline),
        "timeline": timeline,
    }
