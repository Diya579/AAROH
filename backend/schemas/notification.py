"""
AAROH — Notification Pydantic Schemas

Field names and types match backend/models.py → Notification exactly.
notification_type is validated at the Pydantic layer (Literal) rather than
as a DB-level Enum, consistent with this codebase's existing String columns.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Allowed notification type values (enforced here, not in the DB)
# ---------------------------------------------------------------------------

NotificationTypeValue = Literal[
    "HIGH_PRIORITY_CASE",
    "ESCALATION_ALERT",
    "INTERVENTION_ASSIGNED",
    "INTERVENTION_OVERDUE",
    "FOLLOW_UP_REQUIRED",
    "OUTCOME_RECORDED",
    "SYSTEM_NOTIFICATION",
]


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class NotificationResponse(BaseModel):
    """Serialisation of a Notification row returned to the caller."""

    id:                 int
    recipient_user_id:  str
    recipient_role:     str
    notification_type:  str
    title:              str
    message:            str
    case_id:            Optional[int]
    intervention_id:    Optional[int]
    outcome_id:         Optional[int]
    is_read:            bool
    created_at:         datetime
    read_at:            Optional[datetime]

    model_config = {"from_attributes": True}
