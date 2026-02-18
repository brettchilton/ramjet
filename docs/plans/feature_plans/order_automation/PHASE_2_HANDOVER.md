# Phase 2 Handover: Gmail OAuth2 Integration

**Status:** COMPLETE
**Date:** 2026-02-07

---

## What Was Built

Gmail inbox monitoring via OAuth2 — connects to a Gmail account, polls for unread emails, stores raw email data + attachments in PostgreSQL, and exposes a system status/control API. This is the email ingestion layer that Phase 3 (LLM Extraction) will consume.

### Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/gmail_service.py` | GmailPoller class — OAuth2 credentials, background polling loop, email parsing, attachment download, error isolation |
| `backend/app/api/system.py` | System API router — email monitor status, start, stop, poll-now endpoints |
| `backend/app/schemas/email_schemas.py` | Pydantic V2 schemas for all email/monitor API responses |
| `backend/migrations/versions/a1b2c3d4e5f6_add_email_monitoring_tables.py` | Alembic migration for 3 email tables + singleton status row |
| `backend/scripts/gmail_oauth_setup.py` | One-time OAuth2 consent flow script (browser-based) |
| `backend/tests/test_email_monitor.py` | Integration + unit tests with mocked Gmail API |

### Files Modified

| File | Change |
|------|--------|
| `backend/requirements.txt` | Added google-auth, google-auth-oauthlib, google-api-python-client |
| `backend/app/core/models.py` | Added LargeBinary import + 3 new models: IncomingEmail, EmailAttachment, EmailMonitorStatus |
| `backend/app/main.py` | Registered system router, added gmail_poller startup/shutdown hooks |
| `docker-compose.yml` | Added 4 Gmail env vars to backend service |
| `.gitignore` | Added client_secret.json patterns |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/email-monitor/status` | Current monitor status (is_running, last_poll_at, error, total count) |
| POST | `/api/system/email-monitor/start` | Start background polling task |
| POST | `/api/system/email-monitor/stop` | Gracefully stop polling task |
| POST | `/api/system/email-monitor/poll-now` | Trigger single poll cycle, returns new email count |

---

## Database Schema

3 new PostgreSQL tables:

- **incoming_emails** — Integer PK, gmail_message_id (UNIQUE), sender, subject, body_text, body_html, received_at, processed flag, timestamps
- **email_attachments** — Integer PK, FK to incoming_emails.id (CASCADE), filename, content_type, file_data (BYTEA), file_size_bytes
- **email_monitor_status** — Singleton (id=1), is_running, last_poll_at, last_error, emails_processed_total

Indexes: `idx_incoming_emails_gmail_id`, `idx_incoming_emails_processed`, `idx_email_attachments_email_id`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_CLIENT_ID` | _(empty)_ | Google OAuth2 Client ID |
| `GMAIL_CLIENT_SECRET` | _(empty)_ | Google OAuth2 Client Secret |
| `GMAIL_REFRESH_TOKEN` | _(empty)_ | OAuth2 refresh token (from setup script) |
| `GMAIL_POLL_INTERVAL_SECONDS` | `60` | Seconds between poll cycles |

---

## Architecture Decisions

1. **Conditional startup** — App boots cleanly without Gmail credentials; poller just doesn't start
2. **run_in_executor** — Gmail API is synchronous; wrapped in thread executor to keep async event loop free
3. **Session-per-poll-cycle** — Background task creates/closes its own SQLAlchemy session (can't use FastAPI Depends)
4. **BYTEA for attachments** — Stores attachment binary data directly in PostgreSQL. Fine for prototype PO documents (<5MB). Existing DO Spaces infra available for production scale-up
5. **Module-level singleton** — `gmail_poller` instance shared between startup hooks and API router
6. **Integer PKs for email tables** — Simpler than UUID for these internal-only tables (not exposed externally)
7. **Exponential backoff** — On errors, poll interval doubles (capped at 300s), resets on success
8. **Error isolation** — Each email processed in try/except; one failure doesn't crash the loop

---

## Gmail OAuth2 Setup

To configure Gmail access:

1. Create OAuth2 credentials in Google Cloud Console (Desktop app type)
2. Download `client_secret.json` to `backend/scripts/`
3. Run `python backend/scripts/gmail_oauth_setup.py`
4. Copy the printed env vars to `.env`

---

## Notes for Next Phases

- **Phase 3** should query `incoming_emails` WHERE `processed = FALSE` to find new emails for LLM extraction
- **Phase 3** should set `processed = TRUE` after successfully extracting order data from an email
- **Phase 3** can access attachment binary data via `email.attachments` relationship (e.g., PDF purchase orders for OCR/parsing)
- The `poll-now` endpoint is useful for testing/demos without waiting for the background loop
- The `EmailMonitorStatus.emails_processed_total` counter tracks total emails fetched (not processed by LLM)
