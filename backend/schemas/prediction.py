"""
AAROH — Prediction Pydantic Schemas

Field names and types match backend/models.py → Prediction exactly.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class PredictionCreate(BaseModel):
    """Fields required to create a new prediction."""

    case_id: int = Field(..., description="FK → cases.id")
    prediction_date: datetime
    escalation_probability: Optional[float] = None
    target_horizon_days: Optional[int] = 7
    confidence: Optional[float] = None
    risk_level: Optional[str] = Field(None, max_length=50)
    explanation: Optional[Dict[str, Any]] = None


# --- Response schema -------------------------------------------------------

class PredictionResponse(BaseModel):
    """Serialisation of a Prediction row."""

    id: int
    case_id: int
    prediction_date: datetime
    escalation_probability: Optional[float]
    target_horizon_days: Optional[int]
    confidence: Optional[float]
    risk_level: Optional[str]
    explanation: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}
