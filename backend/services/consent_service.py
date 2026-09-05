"""
AAROH — Consent Service

Database operations for the consents table.
Enforces the 1:1 relationship with cases via an upsert pattern.
"""

from typing import Optional

from sqlalchemy.orm import Session

from backend.models import Consent
from backend.schemas.consent import ConsentUpsert


def upsert_consent(db: Session, case_id: int, payload: ConsentUpsert) -> Consent:
    """Create or update a consent record for a case."""
    row = db.query(Consent).filter(Consent.case_id == case_id).first()
    
    if row is None:
        # Create new
        row = Consent(case_id=case_id, **payload.model_dump())
        db.add(row)
    else:
        # Update existing
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
            
    db.commit()
    db.refresh(row)
    return row


def get_consent(db: Session, case_id: int) -> Optional[Consent]:
    """Fetch consent by case_id (not by the consent row's own ID)."""
    return db.query(Consent).filter(Consent.case_id == case_id).first()
