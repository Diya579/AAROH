"""
AAROH — Intervention API Endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.schemas.intervention import (
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    OutcomeCreate,
    OutcomeResponse,
)
from backend.services import intervention_service

router = APIRouter(tags=["Interventions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/interventions",
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("SYSTEM_SERVICE", "ADMIN", "COUNSELLOR"))],
)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        return intervention_service.create_intervention(db, payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create intervention."
        )


@router.get(
    "/interventions",
    response_model=List[InterventionResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_interventions(
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return intervention_service.get_interventions(db, case_id=case_id, skip=skip, limit=limit)


@router.patch(
    "/interventions/{intervention_id}",
    response_model=InterventionResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN"))],
)
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = intervention_service.update_intervention(db, intervention_id, payload)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    return row


@router.post(
    "/outcomes",
    response_model=OutcomeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("SYSTEM_SERVICE", "ADMIN", "COUNSELLOR"))],
)
def create_outcome(
    payload: OutcomeCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        return intervention_service.create_outcome(db, payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create outcome."
        )


@router.get(
    "/outcomes",
    response_model=List[OutcomeResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_outcomes(
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return intervention_service.get_outcomes(db, case_id=case_id, skip=skip, limit=limit)
