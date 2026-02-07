"""
Integration tests for Phase 2: Gmail OAuth2 email monitoring.

Run inside Docker:
    docker exec eezy_peezy_backend python -m pytest tests/test_email_monitor.py -v
"""

import base64
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.models import IncomingEmail, EmailAttachment, EmailMonitorStatus
from app.services.gmail_service import GmailPoller

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Model Tests ────────────────────────────────────────────────────────

class TestEmailModels:
    def test_email_monitor_status_singleton(self, db):
        """Verify the singleton status row exists after migration."""
        status = db.query(EmailMonitorStatus).filter(
            EmailMonitorStatus.id == 1
        ).first()
        assert status is not None
        assert status.is_running is False
        assert status.emails_processed_total == 0

    def test_create_incoming_email(self, db):
        """Test creating and querying an email record."""
        email = IncomingEmail(
            gmail_message_id="test_msg_001",
            sender="test@example.com",
            subject="Test Subject",
            body_text="Hello world",
            body_html="<p>Hello world</p>",
            processed=False,
        )
        db.add(email)
        db.commit()

        fetched = db.query(IncomingEmail).filter(
            IncomingEmail.gmail_message_id == "test_msg_001"
        ).first()
        assert fetched is not None
        assert fetched.sender == "test@example.com"
        assert fetched.subject == "Test Subject"
        assert fetched.processed is False

        # Cleanup
        db.delete(fetched)
        db.commit()

    def test_create_email_with_attachment(self, db):
        """Test email + attachment relationship."""
        email = IncomingEmail(
            gmail_message_id="test_msg_002",
            sender="vendor@example.com",
            subject="PO Attached",
            body_text="See attached",
            processed=False,
        )
        db.add(email)
        db.flush()

        attachment = EmailAttachment(
            email_id=email.id,
            filename="purchase_order.pdf",
            content_type="application/pdf",
            file_data=b"fake pdf content",
            file_size_bytes=16,
        )
        db.add(attachment)
        db.commit()

        fetched = db.query(IncomingEmail).filter(
            IncomingEmail.gmail_message_id == "test_msg_002"
        ).first()
        assert len(fetched.attachments) == 1
        assert fetched.attachments[0].filename == "purchase_order.pdf"
        assert fetched.attachments[0].file_size_bytes == 16

        # Cleanup — cascade should delete attachment
        db.delete(fetched)
        db.commit()

    def test_duplicate_gmail_id_rejected(self, db):
        """Unique constraint on gmail_message_id prevents duplicates."""
        email1 = IncomingEmail(
            gmail_message_id="test_msg_dup",
            sender="a@example.com",
            subject="First",
        )
        db.add(email1)
        db.commit()

        email2 = IncomingEmail(
            gmail_message_id="test_msg_dup",
            sender="b@example.com",
            subject="Duplicate",
        )
        db.add(email2)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

        # Cleanup
        original = db.query(IncomingEmail).filter(
            IncomingEmail.gmail_message_id == "test_msg_dup"
        ).first()
        if original:
            db.delete(original)
            db.commit()


# ── API Endpoint Tests ─────────────────────────────────────────────────

class TestSystemAPI:
    def test_get_status(self):
        """GET /api/system/email-monitor/status returns singleton status."""
        resp = client.get("/api/system/email-monitor/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_running" in data
        assert "emails_processed_total" in data

    def test_start_stop_cycle(self):
        """POST start then stop — verifies status transitions."""
        # Start
        resp = client.post("/api/system/email-monitor/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_running"] is True

        # Status should show running
        resp = client.get("/api/system/email-monitor/status")
        assert resp.json()["is_running"] is True

        # Stop
        resp = client.post("/api/system/email-monitor/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_running"] is False

    def test_start_when_already_running(self):
        """Starting when already running returns success=False."""
        client.post("/api/system/email-monitor/start")
        resp = client.post("/api/system/email-monitor/start")
        data = resp.json()
        assert data["success"] is False
        assert "already running" in data["message"]
        # Cleanup
        client.post("/api/system/email-monitor/stop")

    def test_stop_when_not_running(self):
        """Stopping when not running returns success=False."""
        # Ensure stopped first
        client.post("/api/system/email-monitor/stop")
        resp = client.post("/api/system/email-monitor/stop")
        data = resp.json()
        assert data["success"] is False
        assert "not running" in data["message"]

    def test_poll_now_without_credentials(self):
        """POST poll-now without Gmail credentials returns 0 new emails."""
        resp = client.post("/api/system/email-monitor/poll-now")
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_emails"] == 0


# ── Gmail Service Unit Tests (mocked) ─────────────────────────────────

class TestGmailPollerParsing:
    """Test email parsing helpers with mock data — no real Gmail API calls."""

    def test_get_header(self):
        headers = [
            {"name": "From", "value": "sender@example.com"},
            {"name": "Subject", "value": "Test Email"},
            {"name": "Date", "value": "Sat, 01 Feb 2026 10:00:00 +0000"},
        ]
        assert GmailPoller._get_header(headers, "From") == "sender@example.com"
        assert GmailPoller._get_header(headers, "subject") == "Test Email"
        assert GmailPoller._get_header(headers, "X-Missing") == ""

    def test_extract_body_simple(self):
        payload = {
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(b"Hello plain text").decode()
            },
        }
        text, html = GmailPoller._extract_body(payload)
        assert text == "Hello plain text"
        assert html == ""

    def test_extract_body_multipart(self):
        payload = {
            "mimeType": "multipart/alternative",
            "body": {},
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"Plain version").decode()
                    },
                },
                {
                    "mimeType": "text/html",
                    "body": {
                        "data": base64.urlsafe_b64encode(
                            b"<p>HTML version</p>"
                        ).decode()
                    },
                },
            ],
        }
        text, html = GmailPoller._extract_body(payload)
        assert text == "Plain version"
        assert html == "<p>HTML version</p>"

    def test_find_attachments(self):
        payload = {
            "mimeType": "multipart/mixed",
            "body": {},
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"Body").decode()
                    },
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "invoice.pdf",
                    "body": {
                        "attachmentId": "att_123",
                        "size": 5000,
                    },
                },
                {
                    "mimeType": "image/png",
                    "filename": "logo.png",
                    "body": {
                        "attachmentId": "att_456",
                        "size": 2000,
                    },
                },
            ],
        }
        attachments = GmailPoller._find_attachments(payload)
        assert len(attachments) == 2
        assert attachments[0]["filename"] == "invoice.pdf"
        assert attachments[0]["attachmentId"] == "att_123"
        assert attachments[1]["filename"] == "logo.png"

    def test_find_attachments_empty(self):
        payload = {
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(b"No attachments").decode()
            },
        }
        attachments = GmailPoller._find_attachments(payload)
        assert len(attachments) == 0

    @patch.dict("os.environ", {
        "GMAIL_CLIENT_ID": "",
        "GMAIL_CLIENT_SECRET": "",
        "GMAIL_REFRESH_TOKEN": "",
    })
    def test_poll_sync_no_credentials(self):
        """_poll_sync returns 0 when credentials are not configured."""
        poller = GmailPoller()
        result = poller._poll_sync()
        assert result == 0

    @patch("app.services.gmail_service.GmailPoller._build_credentials")
    @patch("app.services.gmail_service.GmailPoller._get_service")
    def test_poll_sync_no_messages(self, mock_service, mock_creds):
        """_poll_sync handles empty inbox gracefully."""
        mock_creds.return_value = MagicMock()
        service_mock = MagicMock()
        service_mock.users().messages().list().execute.return_value = {
            "messages": []
        }
        mock_service.return_value = service_mock

        poller = GmailPoller()
        result = poller._poll_sync()
        assert result == 0

    @patch("app.services.gmail_service.GmailPoller._build_credentials")
    @patch("app.services.gmail_service.GmailPoller._get_service")
    def test_poll_sync_duplicate_detection(self, mock_service, mock_creds, db):
        """_poll_sync skips emails that already exist in DB."""
        # Pre-insert an email with known gmail_message_id
        existing = IncomingEmail(
            gmail_message_id="existing_msg_123",
            sender="already@stored.com",
            subject="Already stored",
        )
        db.add(existing)
        db.commit()

        mock_creds.return_value = MagicMock()
        service_mock = MagicMock()
        service_mock.users().messages().list().execute.return_value = {
            "messages": [{"id": "existing_msg_123"}]
        }
        mock_service.return_value = service_mock

        poller = GmailPoller()
        result = poller._poll_sync()
        assert result == 0

        # Cleanup
        db.delete(existing)
        db.commit()
