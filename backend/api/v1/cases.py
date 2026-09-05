"""
AAROH — Case API Endpoints

CRUD operations for the cases table.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
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
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caseworker"))],
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
        # e.g., duplicate case_id
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/cases",
    response_model=List[CaseResponse],
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def list_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all cases with pagination."""
    return case_service.list_cases(db, skip=skip, limit=limit)


@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch a specific case by its DB ID."""
    row = case_service.get_case(db, case_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {case_id} not found."
        )
    return row


@router.put(
    "/cases/{case_id}",
    response_model=CaseResponse,
    dependencies=[Depends(require_role("caseworker"))],
)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update fields on an existing case."""
    row = case_service.update_case(db, case_id, payload)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {case_id} not found."
        )
    return row


@router.delete(
    "/cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a case by its DB ID."""
    deleted = case_service.delete_case(db, case_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {case_id} not found."
        )
