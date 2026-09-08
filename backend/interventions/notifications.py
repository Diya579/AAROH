"""
AAROH — Role-Appropriate Notification Subsystem
Author: Preet

Manages operational and citizen notifications across all workflow stages:
- Intervention assignment
- SLA approaching / breach
- Status escalation
- Outcome recording

CRITICAL SAFETY & PRIVACY RULE (Rule 8):
Internal police/caseworker alerts (escalation probabilities, risk scores, threat assessments,
or operational breach warnings) must NEVER be leaked to victims.
Victim-facing notifications are strictly filtered and citizen-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import re

from .sla import ensure_utc


class NotificationRecipientRole(str, Enum):
    VICTIM = "VICTIM"
    CASE_OFFICER = "CASE_OFFICER"
    COUNSELLOR = "COUNSELLOR"
    DESIGNATED_OFFICER = "DESIGNATED_OFFICER"
    DISTRICT_AUTHORITY = "DISTRICT_AUTHORITY"
    DISTRICT_OFFICIAL = "DISTRICT_OFFICIAL"
    STATE_AUTHORITY = "STATE_AUTHORITY"
    STATE_OFFICIAL = "STATE_OFFICIAL"
    NATIONAL_AUTHORITY = "NATIONAL_AUTHORITY"
    NATIONAL_OFFICIAL = "NATIONAL_OFFICIAL"
    ADMIN = "ADMIN"
    SYSTEM_SERVICE = "SYSTEM_SERVICE"


class NotificationType(str, Enum):
    INTERVENTION_ASSIGNED = "INTERVENTION_ASSIGNED"
    SLA_DUE_SOON = "SLA_DUE_SOON"
    SLA_BREACHED = "SLA_BREACHED"
    INTERVENTION_ESCALATED = "INTERVENTION_ESCALATED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"
    SUPPORT_UPDATE = "SUPPORT_UPDATE"


# Disallowed sensitive patterns for victim-facing communication
SENSITIVE_LEAK_PATTERNS = [
    r"risk\s*[:=]\s*\w+",
    r"escalation\s*probability",
    r"distress\s*score",
    r"sla\s*breach",
    r"overdue",
    r"threat\s*level",
    r"high\s*risk",
    r"rapidly\s*worsening",
    r"caseload",
    r"internal\s*alert",
]


@dataclass
class NotificationMessage:
    recipient_role: NotificationRecipientRole
    recipient_id: str
    notification_type: NotificationType
    title: str
    message: str
    case_id: str
    intervention_id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipient_role": self.recipient_role.value,
            "recipient_id": self.recipient_id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "case_id": self.case_id,
            "intervention_id": self.intervention_id,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "metadata": self.metadata,
        }


# Backwards compatibility alias
NotificationRecord = NotificationMessage


class NotificationService:
    """
    Generates and distributes role-appropriate notifications while enforcing
    strict privacy and safety guards.
    """

    def __init__(self) -> None:
        self._notification_log: List[NotificationMessage] = []

    @staticmethod
    def sanitize_for_victim(title: str, message: str) -> tuple[str, str]:
        """
        Strips internal diagnostic, ML risk, and SLA terminology to ensure citizen safety.
        """
        combined = f"{title} {message}".lower()
        contains_leak = any(re.search(pat, combined) for pat in SENSITIVE_LEAK_PATTERNS)

        if contains_leak:
            safe_title = "AAROH Support Services Update"
            safe_msg = (
                "A support officer has been assigned to your case and will follow up with you "
                "through your preferred safe communication channel."
            )
            return safe_title, safe_msg

        return title, message

    def notify(
        self,
        recipient_role: NotificationRecipientRole | str,
        recipient_id: str,
        notification_type: NotificationType | str,
        title: str,
        message: str,
        case_id: Optional[str] = "SYSTEM",
        intervention_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationMessage:
        try:
            role = (
                recipient_role
                if isinstance(recipient_role, NotificationRecipientRole)
                else NotificationRecipientRole(str(recipient_role).upper())
            )
        except ValueError:
            role_str = str(recipient_role).upper()
            if "VICTIM" in role_str or "USER" in role_str:
                role = NotificationRecipientRole.VICTIM
            elif "DISTRICT" in role_str:
                role = NotificationRecipientRole.DISTRICT_AUTHORITY
            elif "STATE" in role_str:
                role = NotificationRecipientRole.STATE_AUTHORITY
            elif "NATIONAL" in role_str:
                role = NotificationRecipientRole.NATIONAL_AUTHORITY
            else:
                role = NotificationRecipientRole.CASE_OFFICER

        try:
            n_type = (
                notification_type
                if isinstance(notification_type, NotificationType)
                else NotificationType(str(notification_type).upper())
            )
        except ValueError:
            n_type = NotificationType.SUPPORT_UPDATE

        clean_metadata = dict(metadata) if metadata else {}

        # Strict Victim Privacy Filter
        if role == NotificationRecipientRole.VICTIM:
            # Strip operational metadata
            clean_metadata.pop("risk_level", None)
            clean_metadata.pop("escalation_probability", None)
            clean_metadata.pop("distress_score", None)
            clean_metadata.pop("sla_status", None)
            clean_metadata.pop("overdue_hours", None)

            clean_title, clean_msg = self.sanitize_for_victim(title, message)
        else:
            clean_title, clean_msg = title, message

        notif = NotificationMessage(
            recipient_role=role,
            recipient_id=recipient_id,
            notification_type=n_type,
            title=clean_title,
            message=clean_msg,
            case_id=case_id,
            intervention_id=intervention_id,
            created_at=datetime.now(timezone.utc),
            metadata=clean_metadata,
        )
        self._notification_log.append(notif)
        return notif

    def get_notifications_for_user(
        self,
        recipient_id: str,
        recipient_role: Optional[NotificationRecipientRole | str] = None,
    ) -> List[Dict[str, Any]]:
        role_filter = (
            NotificationRecipientRole(str(recipient_role))
            if recipient_role
            else None
        )
        results = [
            n.to_dict()
            for n in self._notification_log
            if n.recipient_id == recipient_id
            and (role_filter is None or n.recipient_role == role_filter)
        ]
        return results


# Default singleton instance
notification_service = NotificationService()
