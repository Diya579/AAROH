"""
AAROH — Consent Pydantic Schemas

Field names and types match backend/models.py → Consent exactly.
One consent record per case (uq_consents_case_id).
"""

from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas -------------------------------------------------------

class ConsentUpsert(BaseModel):
    """Fields for creating or updating a consent record (1:1 with case)."""

    monitoring_consent: Optional[bool] = False
    text_analysis_consent: Optional[bool] = False
    voice_analysis_consent: Optional[bool] = False
    case_linkage_consent: Optional[bool] = False
    safe_channel: Optional[str] = Field(None, max_length=30)
    safe_time: Optional[str] = Field(None, max_length=50)


# --- Response schema -------------------------------------------------------

class ConsentResponse(BaseModel):
    """Serialisation of a Consent row."""

    id: int
    case_id: int
    monitoring_consent: Optional[bool]
    text_analysis_consent: Optional[bool]
    voice_analysis_consent: Optional[bool]
    case_linkage_consent: Optional[bool]
    safe_channel: Optional[str]
    safe_time: Optional[str]

    model_config = {"from_attributes": True}
