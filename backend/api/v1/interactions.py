"""
AAROH — Interaction API Endpoints

Endpoints for the interactions table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role
from backend.core.audio_validation import validate_audio, AudioValidationError
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
    user=Depends(get_current_user),
):
    """Create a new interaction."""
    try:
        return interaction_service.create_interaction(db, payload)
    except Exception:
        # Prevent leaking raw DB errors (e.g. FK violation on case_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create interaction. Ensure case_id is valid.",
        )


@router.get(
    "/interactions",
    response_model=List[InteractionResponse],
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def list_interactions(
    case_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List interactions with pagination and optional case filtering."""
    return interaction_service.list_interactions(db, case_id=case_id, skip=skip, limit=limit)


@router.get(
    "/interactions/{interaction_id}",
    response_model=InteractionResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL"))],
)
def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Fetch a specific interaction by its DB ID."""
    row = interaction_service.get_interaction(db, interaction_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction with id {interaction_id} not found.",
        )
    return row


@router.post(
    "/interactions/{interaction_id}/voice",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_role("COUNSELLOR", "USER", "ADMIN"))],
)
def upload_interaction_voice(
    interaction_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Ingest voice audio for an interaction.

    Flow:
        Authenticate → Authorise → Validate audio → Verify interaction
        → Verify case access → Verify voice consent → Secure temp storage
        → Delegate to voice pipeline → Return processing state

    Returns HTTP 202 Accepted with processing state RECEIVED.
    """
    # ------------------------------------------------------------------
    # 1. Validate audio BEFORE touching the database.
    #    Raises AudioValidationError (HTTPException) on failure.
    #    Returns raw bytes on success; file stream is consumed here.
    # ------------------------------------------------------------------
    audio_bytes = validate_audio(file)

    # ------------------------------------------------------------------
    # 2. Verify the interaction exists
    # ------------------------------------------------------------------
    interaction = (
        db.query(Interaction)
        .filter(Interaction.id == interaction_id)
        .first()
    )
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction with id {interaction_id} not found.",
        )

    # ------------------------------------------------------------------
    # 3. Verify voice_analysis_consent from the Consent table.
    #    voice_opted_in on Case is NOT sufficient — the consent record
    #    is the authoritative source.
    # ------------------------------------------------------------------
    consent = (
        db.query(Consent)
        .filter(Consent.case_id == interaction.case_id)
        .first()
    )
    if not consent or not consent.voice_analysis_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voice analysis consent has not been granted for this case.",
        )

    # ------------------------------------------------------------------
    # 4. Delegate to voice pipeline.
    #    Temp file is created, used, and deleted inside delegate_voice_processing.
    #    We never leave audio on disk after this call returns.
    # ------------------------------------------------------------------
    processing_state = voice_service.delegate_voice_processing(
        interaction_id=interaction_id,
        case_id=interaction.case_id,
        language=interaction.language,
        audio_bytes=audio_bytes,
    )

    return {
        "message": "Audio accepted for processing.",
        "interaction_id": interaction_id,
        "status": processing_state,
    }
