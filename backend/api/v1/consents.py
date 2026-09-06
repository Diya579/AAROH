"""
AAROH — Consent API Endpoints

Endpoints for the consents table (upsert pattern).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role, verify_case_id_access
from backend.schemas.consent import ConsentUpsert, ConsentResponse
from backend.services import consent_service
from backend.schemas.error import common_responses
from backend.core.errors import raise_unprocessable, raise_not_found

router = APIRouter(tags=["Consents"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put(
    "/consents/{case_id}", responses=common_responses,
    response_model=ConsentResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "USER", "ADMIN"))],
)
def upsert_consent(
    case_id: int,
    payload: ConsentUpsert,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    verify_case_id_access(case_id, user, db)
    try:
        return consent_service.upsert_consent(db, case_id, payload)
    except Exception as e:
        db.rollback()
        # Do not leak DB integrity errors to the client
        raise_unprocessable("DB_ERROR", "Failed to upsert consent. Ensure case_id is valid.")


@router.get(
    "/consents/{case_id}", responses=common_responses,
    response_model=ConsentResponse,
    dependencies=[Depends(require_role("COUNSELLOR", "ADMIN", "DISTRICT_OFFICIAL", "STATE_OFFICIAL", "NATIONAL_OFFICIAL", "USER"))],
)
def get_consent(
    case_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetch consent for a specific case."""
    verify_case_id_access(case_id, user, db)
    row = consent_service.get_consent(db, case_id)
    if row is None:
        raise_not_found("Consent record for case", case_id)
    return row
