"""
AAROH — CaseEvent Pydantic Schemas

Field names and types match backend/models.py → CaseEvent exactly.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class EventCreate(BaseModel):
    """Fields required to create a new case event."""

    case_id: int = Field(..., description="FK → cases.id")
    event_date: datetime
    event_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    case_stage: str = Field(..., max_length=50)


# --- Response schema -------------------------------------------------------

class EventResponse(BaseModel):
    """Serialisation of a CaseEvent row."""

    id: int
    case_id: int
    event_date: datetime
    event_type: str
    description: Optional[str]
    case_stage: str

    model_config = {"from_attributes": True}
