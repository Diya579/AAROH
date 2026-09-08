"""
AAROH — Interaction Service

Database operations for the interactions table.
"""

from typing import List, Optional
import logging

from sqlalchemy.orm import Session

from backend.models import Interaction
from backend.core.security import apply_scope_filter
from backend.schemas.interaction import InteractionCreate

from backend.ml.inference.config import PipelineConfig
from backend.ml.inference.pipeline import MLInferencePipeline
from backend.ml.inference.registry import ModelRegistry
from backend.ml.preprocessing.pipeline import InteractionPreprocessingPipeline
from backend.ml.features.assembly import MLInputAssembler
from backend.ml.contract import ProcessingStatus
from backend.services.prediction_service import create_prediction, create_distress_state
from backend.schemas.prediction import PredictionCreate
from backend.schemas.distress import DistressStateCreate

logger = logging.getLogger(__name__)

# Global ML Pipeline Instances
_ml_config = PipelineConfig()
_ml_registry = ModelRegistry()
_ml_pipeline = MLInferencePipeline(config=_ml_config, registry=_ml_registry)
_ml_pipeline.load_models()
_ml_pipeline.warmup()
_prep_pipeline = InteractionPreprocessingPipeline()

def create_interaction(db: Session, payload: InteractionCreate) -> Interaction:
    """Insert a new interaction row and run synchronous ML pipeline."""
    row = Interaction(**payload.model_dump())
    db.add(row)
    db.flush()
    db.refresh(row)
    
    # Run ML pipeline synchronously
    try:
        # Fetch case history up to this point
        historical_interactions = db.query(Interaction).filter(
            Interaction.case_id == payload.case_id
        ).order_by(Interaction.interaction_date.asc()).all()
        
        # Build history sequence
        case_history = []
        assembler = MLInputAssembler()
        for hist_row in historical_interactions:
            row_dict = {
                "case_id": str(hist_row.case_id),
                "interaction_date": hist_row.interaction_date.isoformat() if hist_row.interaction_date else None,
                "language": hist_row.language,
                "text_response": hist_row.text_response,
                "safety_response": hist_row.safety_response,
                "sleep_disruption": hist_row.sleep_disruption,
                "fear_level": hist_row.fear_level,
                "social_support": hist_row.social_support,
                "response_completed": hist_row.response_completed,
                "voice_available": hist_row.voice_available,
                "help_requested": hist_row.help_requested,
                "data_quality": hist_row.data_quality,
            }
            preprocessed = _prep_pipeline.transform(row_dict)
            ml_input = assembler.assemble_from_preprocessed(
                preprocessed,
                metadata={"raw_text": hist_row.text_response}
            )
            case_history.append(ml_input)
            
        ml_result = _ml_pipeline.run_case(case_history)
        
        if ml_result.status == ProcessingStatus.SUCCESS:
            # Persist prediction
            if ml_result.prediction:
                pred_payload = PredictionCreate(
                    case_id=payload.case_id,
                    prediction_date=row.interaction_date,
                    escalation_probability=ml_result.prediction.escalation_probability,
                    target_horizon_days=ml_result.prediction.target_horizon_days or 7,
                    confidence=ml_result.prediction.confidence,
                    risk_level=ml_result.prediction.risk_level.value if hasattr(ml_result.prediction.risk_level, 'value') else ml_result.prediction.risk_level,
                    explanation=ml_result.explanation.to_dict() if hasattr(ml_result.explanation, 'to_dict') else (ml_result.explanation.model_dump() if hasattr(ml_result.explanation, 'model_dump') else ml_result.explanation)
                )
                create_prediction(db, pred_payload)
            
            # Persist distress state
            if ml_result.distress:
                distress_payload = DistressStateCreate(
                    case_id=payload.case_id,
                    observation_date=row.interaction_date,
                    distress_score=ml_result.distress.score,
                    trajectory=ml_result.distress.trajectory.value if hasattr(ml_result.distress.trajectory, 'value') else ml_result.distress.trajectory,
                    confidence=ml_result.distress.confidence
                )
                create_distress_state(db, distress_payload)
        else:
            logger.warning(f"ML Pipeline did not return SUCCESS. Status: {ml_result.status}")

    except Exception as e:
        # ML pipeline failed, persist an error-state Prediction row so it's not a silent failure
        logger.error(f"ML Pipeline failed during interaction creation: {e}")
        pred_payload = PredictionCreate(
            case_id=payload.case_id,
            prediction_date=row.interaction_date,
            escalation_probability=None,
            target_horizon_days=7,
            confidence=0.0,
            risk_level="SYSTEM_ERROR",
            explanation={"error": str(e), "message": "ML pipeline failed during execution"}
        )
        try:
            create_prediction(db, pred_payload)
        except Exception as pred_e:
            logger.error(f"Failed to log error-state Prediction row: {pred_e}")

    return row

def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    """Fetch a single interaction by its DB primary key."""
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(
    db: Session,
    user,
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Interaction]:
    """Return a paginated list of interactions, optionally filtered by case_id."""
    query = db.query(Interaction)
    
    # Apply RBAC scope filter
    query = apply_scope_filter(query, Interaction, user)
    
    if case_id is not None:
        query = query.filter(Interaction.case_id == case_id)
    return query.offset(skip).limit(limit).all()
