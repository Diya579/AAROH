from sqlalchemy.orm import Session
from typing import List, Optional

from backend.models import Intervention
from backend.core.security import apply_scope_filter
from backend.schemas.intervention import InterventionCreate, InterventionUpdate


def create_intervention(db: Session, payload: InterventionCreate) -> Intervention:
    db_obj = Intervention(**payload.model_dump())
    db.add(db_obj)
    db.flush()
    db.refresh(db_obj)
    return db_obj


def get_intervention(db: Session, intervention_id: int) -> Optional[Intervention]:
    return db.query(Intervention).filter(Intervention.id == intervention_id).first()


def get_interventions(db: Session, user, case_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Intervention]:
    query = db.query(Intervention)
    query = apply_scope_filter(query, Intervention, user)
    if case_id:
        query = query.filter(Intervention.case_id == case_id)
    return query.offset(skip).limit(limit).all()


def update_intervention(db: Session, intervention_id: int, payload: InterventionUpdate) -> Optional[Intervention]:
    db_obj = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not db_obj:
        return None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_obj, k, v)
    db.commit()
    db.refresh(db_obj)
    return db_obj



