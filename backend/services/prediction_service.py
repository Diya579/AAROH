from sqlalchemy.orm import Session
from typing import List

from backend.models import Prediction
from backend.schemas.prediction import PredictionCreate


def create_prediction(db: Session, payload: PredictionCreate) -> Prediction:
    db_obj = Prediction(**payload.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_predictions_by_case(db: Session, case_id: int, skip: int = 0, limit: int = 100) -> List[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.case_id == case_id)
        .order_by(Prediction.prediction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
