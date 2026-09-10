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
    HIGH_RISK_CASE = "HIGH_RISK_CASE"
    HIGH_PRIORITY_CASE = "HIGH_PRIORITY_CASE"
    INTERVENTION_ASSIGNED = "INTERVENTION_ASSIGNED"
    INTERVENTION_OVERDUE = "INTERVENTION_OVERDUE"
    SLA_DUE_SOON = "SLA_DUE_SOON"
    SLA_BREACHED = "SLA_BREACHED"
    INTERVENTION_ESCALATED = "INTERVENTION_ESCALATED"
    ESCALATION_ALERT = "ESCALATION_ALERT"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"
    SUPPORT_UPDATE = "SUPPORT_UPDATE"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


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
    outcome_id: Optional[int] = None
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
            "outcome_id": self.outcome_id,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "metadata": self.metadata,
        }


# Backwards compatibility alias
NotificationRecord = NotificationMessage


class NotificationService:
    """
    Generates and distributes role-appropriate notifications while enforcing
    strict privacy and safety guards. Persists to PostgreSQL notifications table
    while preserving in-memory logging for audit and resilience.
    """

    def __init__(self) -> None:
        self._notification_log: List[NotificationMessage] = []

    def clear_log(self) -> None:
        """Clears the in-memory notification log (useful for tests and cache flushes)."""
        self._notification_log.clear()

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
        case_id: Optional[str | int] = "SYSTEM",
        intervention_id: Optional[int] = None,
        outcome_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None,
        auto_commit: bool = True,
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

        n_type_str = str(notification_type).upper().replace("-", "_").replace(" ", "_")
        try:
            n_type = (
                notification_type
                if isinstance(notification_type, NotificationType)
                else NotificationType(n_type_str)
            )
        except ValueError:
            if "HIGH" in n_type_str:
                n_type = NotificationType.HIGH_RISK_CASE
            elif "OVERDUE" in n_type_str or "BREACH" in n_type_str:
                n_type = NotificationType.INTERVENTION_OVERDUE
            elif "FOLLOW" in n_type_str:
                n_type = NotificationType.FOLLOW_UP_REQUIRED
            elif "ESCALAT" in n_type_str:
                n_type = NotificationType.INTERVENTION_ESCALATED
            elif "ASSIGN" in n_type_str:
                n_type = NotificationType.INTERVENTION_ASSIGNED
            elif "OUTCOME" in n_type_str:
                n_type = NotificationType.OUTCOME_RECORDED
            else:
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
            # Map recipient user ID to clean case string ID for authenticated victim retrieval
            if str(recipient_id).startswith("VICTIM-"):
                db_user_id = str(recipient_id).replace("VICTIM-", "", 1)
            else:
                db_user_id = str(recipient_id)
        else:
            clean_title, clean_msg = title, message
            db_user_id = str(recipient_id)

        case_id_str = str(case_id) if case_id is not None else "SYSTEM"

        notif = NotificationMessage(
            recipient_role=role,
            recipient_id=recipient_id,
            notification_type=n_type,
            title=clean_title,
            message=clean_msg,
            case_id=case_id_str,
            intervention_id=intervention_id,
            outcome_id=outcome_id,
            created_at=datetime.now(timezone.utc),
            metadata=clean_metadata,
        )
        self._notification_log.append(notif)

        # Persist to PostgreSQL database (notifications table)
        self._persist_to_db(
            db=db,
            recipient_user_id=db_user_id,
            recipient_role=role.value,
            notification_type=n_type.value,
            title=clean_title,
            message=clean_msg,
            case_id=case_id,
            intervention_id=intervention_id,
            outcome_id=outcome_id,
            auto_commit=auto_commit,
        )

        return notif

    def _persist_to_db(
        self,
        db: Optional[Any],
        recipient_user_id: str,
        recipient_role: str,
        notification_type: str,
        title: str,
        message: str,
        case_id: Optional[str | int],
        intervention_id: Optional[int],
        outcome_id: Optional[int],
        auto_commit: bool,
    ) -> None:
        """
        Safely writes notification record to PostgreSQL notifications table.
        Fails open without disrupting workflow if database is offline or unmigrated.
        """
        try:
            from backend.models import Case
            from backend.services.notification_service import create_notification

            close_session = False
            session = db
            if session is None:
                try:
                    from backend.database import SessionLocal, engine
                    if "sqlite" in str(engine.url):
                        from sqlalchemy import create_engine
                        from sqlalchemy.orm import sessionmaker
                        pg_eng = create_engine(
                            "postgresql://postgres:root@localhost:5432/aaroh_db",
                            pool_pre_ping=True,
                        )
                        SessionCls = sessionmaker(bind=pg_eng)
                        session = SessionCls()
                    else:
                        session = SessionLocal()
                    close_session = True
                except Exception:
                    return

            try:
                case_pk: Optional[int] = None
                if case_id is not None and str(case_id).upper() != "SYSTEM":
                    if isinstance(case_id, int):
                        case_pk = case_id
                    elif str(case_id).isdigit():
                        case_pk = int(case_id)
                    else:
                        c_row = session.query(Case.id).filter(Case.case_id == str(case_id)).first()
                        if c_row:
                            case_pk = c_row[0]

                valid_interv_id = (
                    intervention_id
                    if isinstance(intervention_id, int) and intervention_id > 0
                    else None
                )
                valid_outcome_id = (
                    outcome_id
                    if isinstance(outcome_id, int) and outcome_id > 0
                    else None
                )

                create_notification(
                    db=session,
                    recipient_user_id=recipient_user_id,
                    recipient_role=recipient_role,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    case_id=case_pk,
                    intervention_id=valid_interv_id,
                    outcome_id=valid_outcome_id,
                    auto_commit=auto_commit,
                )
            finally:
                if close_session and session:
                    session.close()
        except Exception:
            # Defensive fail-open: in-memory log is preserved
            pass

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
