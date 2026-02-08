"""
Gmail sender — sends emails with attachments via the Gmail API using
the same OAuth2 credentials as the poller.

All synchronous Gmail API / MIME work runs in run_in_executor to keep
the event loop free.
"""

import asyncio
import base64
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.services.gmail_service import gmail_poller

logger = logging.getLogger(__name__)


class GmailSender:
    """Sends emails via the Gmail API reusing the poller's OAuth2 creds."""

    def _send_sync(
        self,
        to_addresses: list[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
    ) -> None:
        """
        Synchronous send.

        Parameters
        ----------
        to_addresses : list of recipient email addresses
        subject      : email subject line
        body_text    : plain-text body
        body_html    : optional HTML body
        attachments  : list of dicts with keys ``filename`` (str) and ``data`` (bytes)
        """
        creds = gmail_poller._build_credentials()
        if not creds:
            raise RuntimeError("Gmail credentials not configured — cannot send email")

        service = gmail_poller._get_service(creds)

        # Build MIME message
        msg = MIMEMultipart("mixed")
        msg["To"] = ", ".join(to_addresses)
        msg["Subject"] = subject

        # Body: alternative part for text + html
        body_part = MIMEMultipart("alternative")
        body_part.attach(MIMEText(body_text, "plain"))
        if body_html:
            body_part.attach(MIMEText(body_html, "html"))
        msg.attach(body_part)

        # Attachments
        for att in (attachments or []):
            part = MIMEApplication(att["data"])
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=att["filename"],
            )
            msg.attach(part)

        # Encode and send
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        logger.info(f"Email sent to {to_addresses}: {subject}")

    async def send(
        self,
        to_addresses: list[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
    ) -> None:
        """Async wrapper — runs the sync send in an executor."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._send_sync,
            to_addresses,
            subject,
            body_text,
            body_html,
            attachments,
        )


# Module-level singleton
gmail_sender = GmailSender()
