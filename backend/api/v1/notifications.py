"""
AAROH — Notification API Endpoints

GET  /notifications           — list own notifications (RBAC-scoped)
PATCH /notifications/{id}/read — mark a specific notification as read

Defense-in-depth: if a notification carries a case_id, the endpoint
verifies the caller can access that case via verify_case_id_access,
so a notification can never leak a case the recipient couldn't
otherwise reach through the standard case API.
"""

from typing import List

from backend.schemas.error import common_responses
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.core.security import get_current_user, require_role, verify_case_id_access
from backend.schemas.notification import NotificationResponse
from backend.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /notifications
# ---------------------------------------------------------------------------

@router.get(
    "",
    responses=common_responses,
    response_model=List[NotificationResponse],
    dependencies=[Depends(require_role(
        "VICTIM", "COUNSELLOR", "DISTRICT_OFFICIAL",
        "STATE_OFFICIAL", "NATIONAL_OFFICIAL", "ADMIN",
    ))],
)
def list_notifications(
    unread_only: bool = Query(default=False, description="Return only unread notifications"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    List notifications addressed to the authenticated user.

    Scope is always pinned to the caller's own user_id — the client
    cannot request another user's notifications.  If a notification
    carries a case_id, a defense-in-depth access check is applied
    before that notification is returned.
    """
    notifications = notification_service.list_notifications(
        db,
        recipient_user_id=user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )

    # Defense-in-depth: silently exclude any case-linked notifications for
    # cases the caller can no longer access (e.g. reassignment, scope change).
    # Listing endpoints never 403 mid-response — inaccessible items are filtered
    # out, consistent with apply_scope_filter used elsewhere.
    # The PATCH /{id}/read endpoint still raises hard 403 on direct access.
    result = []
    for notif in notifications:
        if notif.case_id is not None:
            try:
                verify_case_id_access(notif.case_id, user, db)
            except Exception:
                # Out-of-scope case: silently exclude this notification
                continue
        result.append(notif)

    return result


# ---------------------------------------------------------------------------
# PATCH /notifications/{notification_id}/read
# ---------------------------------------------------------------------------

@router.patch(
    "/{notification_id}/read",
    responses=common_responses,
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(
        "VICTIM", "COUNSELLOR", "DISTRICT_OFFICIAL",
        "STATE_OFFICIAL", "NATIONAL_OFFICIAL", "ADMIN",
    ))],
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Mark a notification as read.  Only the addressed recipient may do this.
    """
    notif = notification_service.mark_as_read(db, notification_id, user.id)

    # Defense-in-depth: re-check case access after retrieving the notification
    if notif.case_id is not None:
        verify_case_id_access(notif.case_id, user, db)

    return notif
