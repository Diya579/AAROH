"""
AAROH — Prediction API Endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.schemas.prediction import PredictionCreate, PredictionResponse
from backend.services import prediction_service

router = APIRouter(tags=["Predictions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("SYSTEM_SERVICE", "ADMIN"))],
)
def create_prediction(
    payload: PredictionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new prediction from the ML service."""
    try:
        return prediction_service.create_prediction(db, payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create prediction. Ensure case_id is valid."
        )


@router.get(
    "/predictions/{case_id}",
    response_model=List[PredictionResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_predictions_for_case(
    case_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch predictions for a specific case."""
    return prediction_service.get_predictions_by_case(db, case_id=case_id, skip=skip, limit=limit)
