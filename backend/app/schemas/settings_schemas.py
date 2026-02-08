from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationEmailsResponse(BaseModel):
    emails: str
    email_list: list[str]
    updated_at: Optional[datetime] = None


class NotificationEmailsUpdateRequest(BaseModel):
    emails: str
