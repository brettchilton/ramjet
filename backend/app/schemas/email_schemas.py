from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# ── Monitor status ─────────────────────────────────────────────────────

class EmailMonitorStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_running: bool
    last_poll_at: Optional[datetime] = None
    last_error: Optional[str] = None
    emails_processed_total: int = 0


class EmailMonitorActionResponse(BaseModel):
    success: bool
    message: str
    is_running: bool


class PollNowResponse(BaseModel):
    success: bool
    new_emails: int
    message: str


# ── Email summaries / details ──────────────────────────────────────────

class EmailAttachmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size_bytes: Optional[int] = None


class IncomingEmailSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[datetime] = None
    processed: bool = False
    attachment_count: int = 0


class IncomingEmailDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: Optional[datetime] = None
    processed: bool = False
    attachments: list[EmailAttachmentSummary] = []
