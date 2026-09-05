"""
AAROH — Interaction Pydantic Schemas

Field names and types match backend/models.py → Interaction exactly.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class InteractionCreate(BaseModel):
    """Fields required to create a new interaction."""

    case_id: int = Field(..., description="FK → cases.id")
    interaction_date: datetime
    channel: str = Field(..., max_length=30)
    language: str = Field(..., max_length=20)
    text_response: Optional[str] = None
    voice_available: Optional[bool] = False
    response_completed: Optional[bool] = True
    safety_response: Optional[int] = None
    sleep_disruption: Optional[int] = None
    fear_level: Optional[int] = None
    social_support: Optional[int] = None
    help_requested: Optional[bool] = False
    data_quality: Optional[str] = Field("good", max_length=30)


# --- Response schema -------------------------------------------------------

class InteractionResponse(BaseModel):
    """Serialisation of an Interaction row."""

    id: int
    case_id: int
    interaction_date: datetime
    channel: str
    language: str
    text_response: Optional[str]
    voice_available: Optional[bool]
    response_completed: Optional[bool]
    safety_response: Optional[int]
    sleep_disruption: Optional[int]
    fear_level: Optional[int]
    social_support: Optional[int]
    help_requested: Optional[bool]
    data_quality: Optional[str]

    model_config = {"from_attributes": True}
