"""
AAROH — Interaction API Endpoints

Endpoints for the interactions table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.schemas.interaction import InteractionCreate, InteractionResponse
from backend.services import interaction_service

router = APIRouter(tags=["Interactions"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("caseworker"))],
)
def create_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new interaction."""
    # We might want to catch IntegrityError if case_id doesn't exist,
    # but for now we'll let it bubble up as a 500 or we could handle it.
    try:
        return interaction_service.create_interaction(db, payload)
    except Exception as e:
        # Prevent leaking raw DB errors.
        # In a real app we'd catch sqlalchemy.exc.IntegrityError specifically.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create interaction. Ensure case_id is valid."
        )


@router.get(
    "/interactions",
    response_model=List[InteractionResponse],
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def list_interactions(
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all interactions with pagination and optional case filtering."""
    return interaction_service.list_interactions(db, case_id=case_id, skip=skip, limit=limit)


@router.get(
    "/interactions/{interaction_id}",
    response_model=InteractionResponse,
    dependencies=[Depends(require_role("caseworker", "admin"))],
)
def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch a specific interaction by its DB ID."""
    row = interaction_service.get_interaction(db, interaction_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction with id {interaction_id} not found."
        )
    return row
