"""
AAROH — Intervention Pydantic Schemas

Field names and types match backend/models.py exactly.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class InterventionCreate(BaseModel):
    """Fields required to create a new intervention."""
    case_id: int = Field(..., description="FK → cases.id")
    intervention_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=100)
    backup_assigned_to: Optional[str] = Field(None, max_length=100)
    backup_assignee: Optional[str] = Field(None, max_length=100)


class InterventionUpdate(BaseModel):
    intervention_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=100)
    backup_assigned_to: Optional[str] = Field(None, max_length=100)
    backup_assignee: Optional[str] = Field(None, max_length=100)


class OutcomeCreate(BaseModel):
    """Fields required to create an outcome."""
    case_id: int = Field(..., description="FK → cases.id")
    intervention_id: Optional[int] = Field(None, description="FK → interventions.id")
    outcome_type: Optional[str] = Field(None, max_length=100)
    completed: Optional[bool] = False
    recorded_at: Optional[datetime] = None


# --- Response schemas -------------------------------------------------------

class InterventionResponse(BaseModel):
    id: int
    case_id: int
    intervention_type: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    backup_assigned_to: Optional[str] = None
    backup_assignee: Optional[str] = None
    priority: Optional[str] = None
    sla_due_at: Optional[datetime] = Field(None, validation_alias="due_at")
    reason: Optional[dict] = None
    assigned_role: Optional[str] = None

    model_config = {"from_attributes": True}


class OutcomeResponse(BaseModel):
    id: int
    case_id: int
    intervention_id: Optional[int]
    outcome_type: Optional[str]
    completed: Optional[bool]
    recorded_at: Optional[datetime]

    model_config = {"from_attributes": True}
