"""
Gmail inbox poller — connects via OAuth2, fetches unread emails + attachments,
stores them in PostgreSQL, and marks them as read in Gmail.

Runs as an asyncio background task; all synchronous Gmail API calls are wrapped
in run_in_executor to keep the event loop free.
"""

import asyncio
import base64
import logging
import os
import traceback
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.database import SessionLocal
from app.core.models import IncomingEmail, EmailAttachment, EmailMonitorStatus
from app.services.extraction_service import process_unprocessed_emails

logger = logging.getLogger(__name__)

# Gmail API scopes needed for reading mail and marking as read
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# Default poll interval (seconds) — overridable via env var
DEFAULT_POLL_INTERVAL = 60


class GmailPoller:
    """Singleton that manages Gmail polling in a background asyncio task."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._poll_interval: int = int(
            os.environ.get("GMAIL_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL)
        )

    # ── Credential helpers ───────────────────────────────────────────

    def _build_credentials(self) -> Optional[Credentials]:
        """Build OAuth2 credentials from environment variables."""
        client_id = os.environ.get("GMAIL_CLIENT_ID")
        client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
        refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")

        if not all([client_id, client_secret, refresh_token]):
            logger.warning("Gmail credentials not configured — poller disabled")
            return None

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        # Force an initial token refresh
        creds.refresh(Request())
        return creds

    def _get_service(self, creds: Credentials):
        """Build the Gmail API service object."""
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    # ── Email parsing helpers ────────────────────────────────────────

    @staticmethod
    def _get_header(headers: list[dict], name: str) -> str:
        """Extract a header value by name from Gmail message headers."""
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value", "")
        return ""

    @staticmethod
    def _extract_body(payload: dict) -> tuple[str, str]:
        """
        Recursively walk MIME parts to extract text/plain and text/html bodies.
        Returns (body_text, body_html).
        """
        body_text = ""
        body_html = ""

        def _walk(part):
            nonlocal body_text, body_html
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data")

            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                if mime_type == "text/plain" and not body_text:
                    body_text = decoded
                elif mime_type == "text/html" and not body_html:
                    body_html = decoded

            for sub_part in part.get("parts", []):
                _walk(sub_part)

        _walk(payload)
        return body_text, body_html

    @staticmethod
    def _find_attachments(payload: dict) -> list[dict]:
        """
        Recursively find all attachment parts.
        Returns list of dicts with keys: filename, mimeType, attachmentId, size.
        """
        attachments = []

        def _walk(part):
            filename = part.get("filename", "")
            attachment_id = part.get("body", {}).get("attachmentId")
            if filename and attachment_id:
                attachments.append({
                    "filename": filename,
                    "mimeType": part.get("mimeType", "application/octet-stream"),
                    "attachmentId": attachment_id,
                    "size": part.get("body", {}).get("size", 0),
                })
            for sub_part in part.get("parts", []):
                _walk(sub_part)

        _walk(payload)
        return attachments

    # ── Core poll logic (runs in thread executor) ────────────────────

    def _poll_sync(self) -> int:
        """
        Synchronous poll: list unread → fetch → parse → store → mark read.
        Returns count of newly stored emails.
        """
        creds = self._build_credentials()
        if not creds:
            return 0

        service = self._get_service(creds)
        db = SessionLocal()
        new_count = 0

        try:
            # List unread messages
            results = service.users().messages().list(
                userId="me", q="is:unread", maxResults=50
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                logger.info("No unread messages found")
                return 0

            logger.info(f"Found {len(messages)} unread messages")

            for msg_stub in messages:
                gmail_id = msg_stub["id"]

                try:
                    # Skip duplicates
                    existing = db.query(IncomingEmail).filter(
                        IncomingEmail.gmail_message_id == gmail_id
                    ).first()
                    if existing:
                        logger.debug(f"Skipping duplicate message {gmail_id}")
                        continue

                    # Fetch full message
                    msg = service.users().messages().get(
                        userId="me", id=gmail_id, format="full"
                    ).execute()

                    payload = msg.get("payload", {})
                    headers = payload.get("headers", [])

                    # Parse headers
                    sender = self._get_header(headers, "From")
                    subject = self._get_header(headers, "Subject")
                    date_str = self._get_header(headers, "Date")

                    received_at = None
                    if date_str:
                        try:
                            received_at = parsedate_to_datetime(date_str)
                        except Exception:
                            received_at = datetime.now(timezone.utc)

                    # Parse body
                    body_text, body_html = self._extract_body(payload)

                    # Create email record
                    email_record = IncomingEmail(
                        gmail_message_id=gmail_id,
                        sender=sender,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                        received_at=received_at,
                        processed=False,
                    )
                    db.add(email_record)
                    db.flush()  # Get the email ID for attachment FKs

                    # Process attachments
                    attachment_parts = self._find_attachments(payload)
                    for att_info in attachment_parts:
                        att_data = service.users().messages().attachments().get(
                            userId="me", messageId=gmail_id, id=att_info["attachmentId"]
                        ).execute()
                        file_bytes = base64.urlsafe_b64decode(att_data["data"])

                        attachment = EmailAttachment(
                            email_id=email_record.id,
                            filename=att_info["filename"],
                            content_type=att_info["mimeType"],
                            file_data=file_bytes,
                            file_size_bytes=len(file_bytes),
                        )
                        db.add(attachment)

                    db.commit()
                    new_count += 1

                    # Mark as read in Gmail
                    service.users().messages().modify(
                        userId="me", id=gmail_id,
                        body={"removeLabelIds": ["UNREAD"]}
                    ).execute()

                    logger.info(
                        f"Stored email {gmail_id}: '{subject}' "
                        f"({len(attachment_parts)} attachments)"
                    )

                except Exception as e:
                    db.rollback()
                    logger.error(f"Error processing message {gmail_id}: {e}")
                    logger.debug(traceback.format_exc())
                    continue

            # Auto-process new emails through LLM extraction
            if new_count > 0:
                logger.info(f"Auto-processing {new_count} new emails...")
                try:
                    result = process_unprocessed_emails(db)
                    logger.info(f"Auto-processing result: {result['message']}")
                except Exception as e:
                    logger.error(f"Auto-processing failed: {e}")

            # Update monitor status
            status = db.query(EmailMonitorStatus).filter(
                EmailMonitorStatus.id == 1
            ).first()
            if status:
                status.last_poll_at = datetime.now(timezone.utc)
                status.last_error = None
                status.emails_processed_total = (
                    status.emails_processed_total or 0
                ) + new_count
                db.commit()

        except Exception as e:
            logger.error(f"Poll cycle error: {e}")
            logger.debug(traceback.format_exc())
            # Record error in status
            try:
                status = db.query(EmailMonitorStatus).filter(
                    EmailMonitorStatus.id == 1
                ).first()
                if status:
                    status.last_poll_at = datetime.now(timezone.utc)
                    status.last_error = str(e)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

        return new_count

    # ── Async wrappers ───────────────────────────────────────────────

    async def poll_once(self) -> int:
        """Run a single poll cycle (non-blocking)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._poll_sync)

    async def _background_loop(self):
        """Continuous polling loop with exponential backoff on errors."""
        backoff = self._poll_interval
        max_backoff = 300  # 5 minutes

        logger.info(f"Email poller started (interval={self._poll_interval}s)")

        while not self._stop_event.is_set():
            try:
                new_count = await self.poll_once()
                if new_count > 0:
                    logger.info(f"Poll cycle complete: {new_count} new emails")
                backoff = self._poll_interval  # Reset backoff on success
            except Exception as e:
                logger.error(f"Background poll error: {e}")
                backoff = min(backoff * 2, max_backoff)
                logger.info(f"Backing off to {backoff}s")

            # Wait for stop event or poll interval
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=backoff
                )
                break  # Stop event was set
            except asyncio.TimeoutError:
                pass  # Timeout — time to poll again

        logger.info("Email poller stopped")

    # ── Start / Stop ─────────────────────────────────────────────────

    async def start(self):
        """Start the background polling task."""
        if self._task and not self._task.done():
            logger.warning("Poller already running")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._background_loop())

        # Update DB status
        db = SessionLocal()
        try:
            status = db.query(EmailMonitorStatus).filter(
                EmailMonitorStatus.id == 1
            ).first()
            if status:
                status.is_running = True
                db.commit()
        finally:
            db.close()

        logger.info("Gmail poller started")

    async def stop(self):
        """Gracefully stop the background polling task."""
        if not self._task or self._task.done():
            logger.warning("Poller not running")
            return

        self._stop_event.set()
        await self._task
        self._task = None

        # Update DB status
        db = SessionLocal()
        try:
            status = db.query(EmailMonitorStatus).filter(
                EmailMonitorStatus.id == 1
            ).first()
            if status:
                status.is_running = False
                db.commit()
        finally:
            db.close()

        logger.info("Gmail poller stopped")

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()


# Module-level singleton
gmail_poller = GmailPoller()
