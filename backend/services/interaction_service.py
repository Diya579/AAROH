"""
AAROH — Interaction Service

Database operations for the interactions table.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import Interaction
from backend.schemas.interaction import InteractionCreate


def create_interaction(db: Session, payload: InteractionCreate) -> Interaction:
    """Insert a new interaction row."""
    row = Interaction(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    """Fetch a single interaction by its DB primary key."""
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(
    db: Session,
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Interaction]:
    """Return a paginated list of interactions, optionally filtered by case_id."""
    query = db.query(Interaction)
    if case_id is not None:
        query = query.filter(Interaction.case_id == case_id)
    return query.offset(skip).limit(limit).all()
