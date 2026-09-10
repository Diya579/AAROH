"""
AAROH — Notification Service

Provides:
  create_notification — Persists a notification to the PostgreSQL notifications table
  list_notifications  — RBAC-scoped list for the calling user
  get_notification    — Fetch a single notification owned by recipient_user_id
  mark_as_read        — Flip is_read / set read_at for a notification
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import Notification
from backend.core.errors import raise_not_found, raise_forbidden


def create_notification(
    db: Session,
    recipient_user_id: str,
    recipient_role: str,
    notification_type: str,
    title: str,
    message: str,
    case_id: Optional[int] = None,
    intervention_id: Optional[int] = None,
    outcome_id: Optional[int] = None,
    auto_commit: bool = True,
) -> Notification:
    """
    Persists a new Notification record into PostgreSQL.
    """
    notif = Notification(
        recipient_user_id=str(recipient_user_id),
        recipient_role=str(recipient_role),
        notification_type=str(notification_type),
        title=str(title)[:255],
        message=str(message),
        case_id=case_id,
        intervention_id=intervention_id,
        outcome_id=outcome_id,
        is_read=False,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(notif)
    if auto_commit:
        db.commit()
        db.refresh(notif)
    else:
        db.flush()
    return notif


def list_notifications(
    db: Session,
    recipient_user_id: str,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> List[Notification]:
    """
    Return notifications addressed to `recipient_user_id`, ordered newest-first.
    """
    q = db.query(Notification).filter(Notification.recipient_user_id == str(recipient_user_id))

    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712

    return q.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(skip).limit(limit).all()


def get_notification(
    db: Session,
    notification_id: int,
    recipient_user_id: str,
) -> Notification:
    """
    Fetch a single notification, asserting it belongs to `recipient_user_id`.
    Raises 404 if not found, 403 if owned by a different user.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise_not_found(f"Notification {notification_id} not found.")
    
    if notif.recipient_user_id != str(recipient_user_id):
        raise_forbidden(
            "NOTIFICATION_ACCESS_DENIED",
            "You do not have access to this notification.",
        )
    return notif


def mark_as_read(
    db: Session,
    notification_id: int,
    recipient_user_id: str,
) -> Notification:
    """
    Mark a notification as read.  Only the addressed recipient may do this.
    Sets read_at to now if transitioning from unread → read.
    """
    notif = get_notification(db, notification_id, str(recipient_user_id))
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(notif)

    return notif
