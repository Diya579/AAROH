"""
AAROH — Interaction API Endpoints

Endpoints for the interactions table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.schemas.interaction import InteractionCreate, InteractionResponse
from backend.services import interaction_service, voice_service
from backend.models import Interaction, Consent

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
    dependencies=[Depends(require_role("COUNSELLOR", "SYSTEM_SERVICE", "ADMIN"))],
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
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
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
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
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


@router.post(
    "/interactions/{interaction_id}/voice",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_role("COUNSELLOR", "USER"))],
)
def upload_interaction_voice(
    interaction_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Ingest voice for an interaction and pass it to the ML voice pipeline.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
        
    # Verify interaction exists
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction with id {interaction_id} not found."
        )
        
    # Verify voice consent
    consent = db.query(Consent).filter(Consent.case_id == interaction.case_id).first()
    if not consent or not consent.voice_analysis_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voice analysis consent is not granted for this case."
        )
        
    # Process the audio file (this writes to a temporary location and passes it downstream)
    try:
        processing_state = voice_service.delegate_voice_processing(interaction_id, file)
        return {
            "message": "Audio accepted for processing",
            "interaction_id": interaction_id,
            "status": processing_state
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process audio file"
        )
