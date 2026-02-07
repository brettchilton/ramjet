"""
System API — email monitor status and control endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import EmailMonitorStatus, IncomingEmail
from app.schemas.email_schemas import (
    EmailMonitorStatusResponse,
    EmailMonitorActionResponse,
    PollNowResponse,
    IncomingEmailDetail,
)
from app.services.gmail_service import gmail_poller

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/email-monitor/status", response_model=EmailMonitorStatusResponse)
def get_email_monitor_status(db: Session = Depends(get_db)):
    """Get current email monitor status."""
    status = db.query(EmailMonitorStatus).filter(EmailMonitorStatus.id == 1).first()
    if not status:
        return EmailMonitorStatusResponse(
            is_running=False, emails_processed_total=0
        )
    return EmailMonitorStatusResponse.model_validate(status)


@router.post("/email-monitor/start", response_model=EmailMonitorActionResponse)
async def start_email_monitor(db: Session = Depends(get_db)):
    """Start the Gmail polling background task."""
    if gmail_poller.is_running:
        return EmailMonitorActionResponse(
            success=False, message="Poller is already running", is_running=True
        )

    await gmail_poller.start()
    return EmailMonitorActionResponse(
        success=True, message="Email monitor started", is_running=True
    )


@router.post("/email-monitor/stop", response_model=EmailMonitorActionResponse)
async def stop_email_monitor(db: Session = Depends(get_db)):
    """Stop the Gmail polling background task."""
    if not gmail_poller.is_running:
        return EmailMonitorActionResponse(
            success=False, message="Poller is not running", is_running=False
        )

    await gmail_poller.stop()
    return EmailMonitorActionResponse(
        success=True, message="Email monitor stopped", is_running=False
    )


@router.get("/emails/{email_id}", response_model=IncomingEmailDetail)
def get_email_detail(email_id: int, db: Session = Depends(get_db)):
    """Get full email detail including body and attachments list."""
    email = db.query(IncomingEmail).filter(IncomingEmail.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return IncomingEmailDetail.model_validate(email)


@router.post("/email-monitor/poll-now", response_model=PollNowResponse)
async def poll_now():
    """Trigger a single poll cycle on demand."""
    try:
        new_count = await gmail_poller.poll_once()
        return PollNowResponse(
            success=True,
            new_emails=new_count,
            message=f"Poll complete: {new_count} new email(s) fetched",
        )
    except Exception as e:
        return PollNowResponse(
            success=False,
            new_emails=0,
            message=f"Poll failed: {str(e)}",
        )
