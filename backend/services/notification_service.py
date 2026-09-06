"""
AAROH — Notification Service

Provides:
  list_notifications  — RBAC-scoped list for the calling user
  mark_as_read        — flip is_read / set read_at for a notification the
                        caller owns

Deliberately contains NO notification-creation logic.
When and why a notification is generated is Preet's / business-layer concern.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import Notification
from backend.core.errors import raise_not_found, raise_forbidden


def list_notifications(
    db: Session,
    recipient_user_id: str,
    *,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> List[Notification]:
    """
    Return notifications addressed to `recipient_user_id`, ordered newest-first.

    The caller MUST pass their own authenticated user_id — the service does not
    accept an arbitrary user_id parameter; that is enforced at the API layer.

    Query parameters may narrow results (unread_only) but can never expand
    scope to another user's notifications.
    """
    q = (
        db.query(Notification)
        .filter(Notification.recipient_user_id == recipient_user_id)
    )

    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712

    return (
        q.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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
        raise_not_found("Notification", notification_id)
    if notif.recipient_user_id != recipient_user_id:
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
    notif = get_notification(db, notification_id, recipient_user_id)

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notif)

    return notif
