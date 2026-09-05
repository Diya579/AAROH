"""
AAROH — Case Pydantic Schemas

Field names and types match backend/models.py → Case exactly.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class CaseCreate(BaseModel):
    """Fields required to create a new case."""

    case_id: str = Field(..., max_length=50, description="External case identifier")
    language: str = Field(..., max_length=20)
    district_type: str = Field(..., max_length=20)
    district: str = Field(..., max_length=100)
    priority_use_case: str = Field(..., max_length=100)
    current_stage: str = Field(..., max_length=50)
    voice_opted_in: Optional[bool] = False
    monitoring_consent: Optional[bool] = True


class CaseUpdate(BaseModel):
    """Fields that may be updated on an existing case (all optional)."""

    language: Optional[str] = Field(None, max_length=20)
    district_type: Optional[str] = Field(None, max_length=20)
    district: Optional[str] = Field(None, max_length=100)
    priority_use_case: Optional[str] = Field(None, max_length=100)
    current_stage: Optional[str] = Field(None, max_length=50)
    voice_opted_in: Optional[bool] = None
    monitoring_consent: Optional[bool] = None


# --- Response schema -------------------------------------------------------

class CaseResponse(BaseModel):
    """Serialisation of a Case row."""

    id: int
    case_id: str
    language: str
    district_type: str
    district: str
    priority_use_case: str
    current_stage: str
    voice_opted_in: Optional[bool]
    monitoring_consent: Optional[bool]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
