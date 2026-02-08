"""
Settings API — manage system-wide configuration like notification emails.
"""

import re
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import SystemSettings
from app.schemas.settings_schemas import (
    NotificationEmailsResponse,
    NotificationEmailsUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_emails(raw: str) -> list[str]:
    """Parse and validate comma-separated email addresses. Returns cleaned list."""
    if not raw.strip():
        return []
    addresses = [e.strip() for e in raw.split(",") if e.strip()]
    for addr in addresses:
        if not EMAIL_RE.match(addr):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid email address: {addr}",
            )
    return addresses


@router.get("/notification-emails", response_model=NotificationEmailsResponse)
def get_notification_emails(db: Session = Depends(get_db)):
    """Return the current notification email configuration."""
    setting = db.query(SystemSettings).filter(
        SystemSettings.key == "notification_emails"
    ).first()

    raw = setting.value if setting else ""
    email_list = [e.strip() for e in raw.split(",") if e.strip()] if raw else []

    return NotificationEmailsResponse(
        emails=raw or "",
        email_list=email_list,
        updated_at=setting.updated_at if setting else None,
    )


@router.put("/notification-emails", response_model=NotificationEmailsResponse)
def update_notification_emails(
    body: NotificationEmailsUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update the notification email addresses (comma-separated)."""
    email_list = _validate_emails(body.emails)
    cleaned = ", ".join(email_list)

    setting = db.query(SystemSettings).filter(
        SystemSettings.key == "notification_emails"
    ).first()

    if setting:
        setting.value = cleaned
    else:
        setting = SystemSettings(
            key="notification_emails",
            value=cleaned,
            description="Comma-separated email addresses for order approval notifications",
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)

    logger.info(f"Notification emails updated: {cleaned or '(none)'}")

    return NotificationEmailsResponse(
        emails=setting.value or "",
        email_list=email_list,
        updated_at=setting.updated_at,
    )
