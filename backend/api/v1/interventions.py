"""
AAROH — Intervention API Endpoints
"""

from typing import List, Optional

from backend.schemas.error import common_responses
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header, Response
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role, verify_case_id_access
from backend.core.idempotency import execute_idempotent
from backend.core.errors import raise_not_found, raise_unprocessable
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
    "/interventions", responses=common_responses,
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("SYSTEM_SERVICE", "ADMIN", "COUNSELLOR"))],
)
def create_intervention(
    payload: InterventionCreate,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Create a new intervention."""
    def _create():
        try:
            return intervention_service.create_intervention(db, payload)
        except Exception:
            db.rollback()
            raise_unprocessable("INTERVENTION_INVALID", "Failed to create intervention.")

    return execute_idempotent(
        db=db,
        actor_user_id=user.id,
        operation="CREATE_INTERVENTION",
        idempotency_key=idempotency_key,
        payload=payload,
        executor=_create,
        response_status=status.HTTP_201_CREATED,
        response_obj=response
    )


@router.get(
    "/interventions", responses=common_responses,
    response_model=List[InterventionResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_interventions(
    case_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return intervention_service.get_interventions(db, user=user, case_id=case_id, skip=skip, limit=limit)


@router.patch(
    "/interventions/{intervention_id}", responses=common_responses,
    response_model=InterventionResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN"))],
)
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdate,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    def _update():
        existing = intervention_service.get_intervention(db, intervention_id)
        if not existing:
            raise_not_found("Intervention", intervention_id)
            
        verify_case_id_access(existing.case_id, user, db)
    
        row = intervention_service.update_intervention(db, intervention_id, payload)
        return row

    return execute_idempotent(
        db=db,
        actor_user_id=user.id,
        operation="UPDATE_INTERVENTION",
        idempotency_key=idempotency_key,
        payload=payload,
        executor=_update,
        response_status=status.HTTP_200_OK,
        response_obj=response
    )


@router.post(
    "/outcomes", responses=common_responses,
    response_model=OutcomeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("SYSTEM_SERVICE", "ADMIN", "COUNSELLOR"))],
)
def create_outcome(
    payload: OutcomeCreate,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Record an outcome for an intervention."""
    def _create():
        try:
            return intervention_service.create_outcome(db, payload)
        except Exception:
            db.rollback()
            raise_unprocessable("OUTCOME_INVALID", "Failed to create outcome.")

    return execute_idempotent(
        db=db,
        actor_user_id=user.id,
        operation="CREATE_OUTCOME",
        idempotency_key=idempotency_key,
        payload=payload,
        executor=_create,
        response_status=status.HTTP_201_CREATED,
        response_obj=response
    )


@router.get(
    "/outcomes", responses=common_responses,
    response_model=List[OutcomeResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_outcomes(
    case_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return intervention_service.get_outcomes(db, user=user, case_id=case_id, skip=skip, limit=limit)
