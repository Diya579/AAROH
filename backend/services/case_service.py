"""
AAROH — Case Service

Database operations for the cases table.
Business logic lives here, not in route handlers.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models import Case
from backend.schemas.case import CaseCreate, CaseUpdate

logger = logging.getLogger(__name__)


def create_case(db: Session, payload: CaseCreate) -> Case:
    """Insert a new case row. Raises ValueError on duplicate case_id."""
    row = Case(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Case with case_id '{payload.case_id}' already exists.")
    return row


def get_case(db: Session, case_id: int) -> Optional[Case]:
    """Fetch a single case by its DB primary key."""
    return db.query(Case).filter(Case.id == case_id).first()


def list_cases(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Case]:
    """Return a paginated list of cases."""
    return db.query(Case).offset(skip).limit(limit).all()


def update_case(db: Session, case_id: int, payload: CaseUpdate) -> Optional[Case]:
    """Update fields on an existing case. Returns None if not found."""
    row = db.query(Case).filter(Case.id == case_id).first()
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


def delete_case(db: Session, case_id: int) -> bool:
    """Delete a case by DB id. Returns True if deleted, False if not found."""
    row = db.query(Case).filter(Case.id == case_id).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
