# Ramjet Plastics — Order Automation System

## Overview

The order automation system monitors a Gmail inbox for incoming purchase orders, extracts structured data using Claude AI, matches products against the internal catalog, and generates Office Order and Works Order Excel files for manufacturing.

The entire pipeline runs automatically — emails arrive, orders appear on the dashboard ready for review.

---

## How It Works (End-to-End Flow)

### 1. Email Monitoring

A background poller (`GmailPoller`) runs inside the FastAPI backend as an asyncio task. Every 60 seconds (configurable via `GMAIL_POLL_INTERVAL_SECONDS`), it:

1. Connects to Gmail via OAuth2 using stored credentials
2. Lists unread messages (max 50 per cycle)
3. Skips duplicates (checks `gmail_message_id` against existing records)
4. Downloads full message content — headers, body text/HTML, and attachments
5. Stores everything in `IncomingEmail` + `EmailAttachment` tables
6. Marks messages as read in Gmail (removes UNREAD label)
7. Automatically triggers LLM extraction for any new emails

**Error handling:** Exponential backoff on connection failures (max 5 min). Individual email errors don't crash the poller.

**Files:** `backend/app/services/gmail_service.py`, `backend/app/api/system.py`

### 2. LLM Extraction

When new emails arrive, the extraction service processes each one:

1. Builds a prompt containing the email body, subject, sender, and attachment content
2. Sends it to Claude (default: `claude-sonnet-4-5-20250929`) with a structured extraction prompt
3. Claude returns JSON with field-level confidence scores (0.0–1.0):

```json
{
  "customer_name": { "value": "Acme Corp", "confidence": 0.95 },
  "po_number": { "value": "PO-12345", "confidence": 0.98 },
  "po_date": { "value": "2026-02-07", "confidence": 0.90 },
  "delivery_date": { "value": "2026-02-14", "confidence": 0.85 },
  "special_instructions": { "value": "Deliver to Dock B", "confidence": 0.80 },
  "line_items": [
    {
      "product_code": { "value": "PY0063-1A", "confidence": 0.95 },
      "description": { "value": "Pylon Cap", "confidence": 0.90 },
      "quantity": { "value": 5000, "confidence": 0.98 },
      "colour": { "value": "Yellow", "confidence": 0.92 },
      "unit_price": { "value": 0.45, "confidence": 0.88 }
    }
  ],
  "overall_confidence": 0.91
}
```

**Supported attachment types:**
- PDF — sent natively to Claude as base64 document blocks (max 25MB; fallback text extraction for larger)
- Excel — parsed via openpyxl into tab-separated text
- Images (JPEG, PNG, GIF, WebP) — sent as image blocks

**Files:** `backend/app/services/extraction_service.py`

### 3. Product Matching

Each extracted line item's product code is matched against the product catalog:

| Priority | Match Type | Confidence |
|----------|-----------|------------|
| 1 | Exact match | 1.0 |
| 2 | Case-insensitive match | 0.9 |
| 3 | Partial (ILIKE) match | 0.6 |

Items are flagged `needs_review = true` when:
- Product code doesn't match any catalog entry (confidence < 0.9)
- Overall item confidence is below 0.80

**Files:** `backend/app/services/enrichment_service.py`

### 4. Order Creation

From the extraction results, the system creates:
- An `Order` record (status: `pending`) with header fields
- `OrderLineItem` records for each line item, including matched product codes and confidence scores
- The raw extraction JSON is stored in `extraction_raw_json` for auditability

Non-order emails (newsletters, spam, etc.) create `error` status orders that are hidden from the default dashboard view.

### 5. Human Review

Users review orders on the frontend dashboard:

- **Dashboard** — shows status cards (Pending, Approved, Rejected, Errors) with counts. Click any card to filter the order list. Errors are hidden by default.
- **Order Detail** — three-panel layout:
  - **Source Panel** (left) — original email content and downloadable attachments
  - **Extracted Data** (right) — editable form with confidence badges on each field. Amber highlights on items needing review.
  - **Form Preview** (bottom) — live preview of the Office Order and Works Orders that will be generated

Users can edit any extracted field, and line totals auto-recalculate when quantity or unit price changes.

### 6. Approval & Form Generation

When a user clicks **Approve**:
1. The backend generates an Office Order Excel file (company-wide summary)
2. For each line item, generates a Works Order Excel file (manufacturing instructions)
3. Stores all files in the database
4. Sets order status to `approved` with timestamp

The user can then download the generated `.xlsx` files from the Form Preview tab.

**Reject** sets the status to `rejected` and stores the rejection reason.

---

## Form Outputs

### Office Order (.xlsx)

A summary document for the office/sales team:

- Company header: "RAMJET PLASTICS" / "OFFICE ORDER"
- Customer info: name, PO number, PO date, delivery date
- Line items table: line #, product code, description, colour, qty, unit price, line total
- Subtotal, GST (10%), Total (inc. GST)
- Special instructions (if any)

### Works Order (.xlsx)

One per line item, for the manufacturing floor. WO number format: `WO-{po_number}-{line_number}`

Seven sections:
1. **Order Details** — WO#, PO#, customer, product, delivery date, colour, quantity
2. **Manufacturing Specifications** — mould number, cycle time, shot weight, cavities, product weight, estimated running time, machine requirements
3. **Material Specifications** — material grade/type, colour info, masterbatch rate, additive details
4. **Material Requirements (Calculated)** — base material kg, masterbatch kg, additive kg, total material kg (includes 5% waste factor)
5. **Packaging** — qty per bag, bag size, qty per carton, carton size, palletisation
6. **Packaging Requirements (Calculated)** — bags and cartons needed for the order quantity
7. **Notes** — special instructions

Sections 2–6 require a matched product in the catalog. Unmatched products show "specifications unavailable" placeholders.

---

## Product Catalog

The catalog drives the Works Order content. Five related tables:

| Table | Purpose |
|-------|---------|
| `Product` | Product code, description, customer |
| `ManufacturingSpec` | Mould, cycle time, weights, machine requirements |
| `MaterialSpec` | Per-colour material grades, additives, masterbatch rates |
| `PackagingSpec` | Bag/carton/pallet configurations |
| `Pricing` | Per-colour, per-customer unit pricing |

Products are seeded via `backend/scripts/seed_products.py`.

---

## API Endpoints

### Orders

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/orders/` | List orders (filterable by status) |
| `GET` | `/api/orders/{id}` | Order detail with line items |
| `PUT` | `/api/orders/{id}` | Update header fields (pending only) |
| `PUT` | `/api/orders/{id}/line-items/{item_id}` | Update line item (auto-recalcs total) |
| `POST` | `/api/orders/{id}/approve` | Approve + generate forms |
| `POST` | `/api/orders/{id}/reject` | Reject with reason |
| `GET` | `/api/orders/{id}/forms/office-order` | Download Office Order .xlsx |
| `GET` | `/api/orders/{id}/forms/works-order/{item_id}` | Download Works Order .xlsx |
| `GET` | `/api/orders/{id}/source-pdf/{attachment_id}` | Download original attachment |
| `POST` | `/api/orders/process-pending` | Batch process unprocessed emails |
| `POST` | `/api/orders/{id}/reprocess` | Delete & re-extract from source email |

### Email Monitor

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/system/email-monitor/status` | Poller status + metrics |
| `POST` | `/api/system/email-monitor/start` | Start the poller |
| `POST` | `/api/system/email-monitor/stop` | Stop the poller |
| `POST` | `/api/system/email-monitor/poll-now` | Trigger immediate poll |

---

## Configuration

All configuration is via environment variables in `.env`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `GMAIL_CLIENT_ID` | Google OAuth2 client ID | — |
| `GMAIL_CLIENT_SECRET` | Google OAuth2 client secret | — |
| `GMAIL_REFRESH_TOKEN` | OAuth2 refresh token (from setup script) | — |
| `GMAIL_POLL_INTERVAL_SECONDS` | Polling frequency | `60` |
| `ANTHROPIC_API_KEY` | Claude API key | — |
| `ANTHROPIC_MODEL` | Claude model ID | `claude-sonnet-4-5-20250929` |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `VITE_API_URL` | Backend API URL for frontend | `http://localhost:8006` |

### Gmail Setup

1. Create OAuth2 credentials (Desktop app type) in Google Cloud Console
2. Run `backend/scripts/gmail_oauth_setup.py` to complete the OAuth flow
3. Copy the refresh token to `.env`
4. The monitored email address must be added as a test user in the OAuth consent screen

---

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   Gmail      │────▶│  GmailPoller (background asyncio task)       │
│   Inbox      │     │  polls every 60s, stores emails              │
└─────────────┘     └──────────────┬───────────────────────────────┘
                                   │ auto-triggers
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │  Extraction Service                          │
                    │  Claude AI extracts structured order data    │
                    │  + product code matching                     │
                    └──────────────┬───────────────────────────────┘
                                   │ creates
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │  PostgreSQL                                  │
                    │  Orders + LineItems + Products + Emails      │
                    └──────────────┬───────────────────────────────┘
                                   │ serves
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │  FastAPI Backend                             │
                    │  REST API for orders, forms, email monitor   │
                    └──────────────┬───────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │  React Frontend (TanStack Router + Query)    │
                    │  Dashboard → Order Review → Form Preview     │
                    │  Auto-polls for new orders every 10s         │
                    └──────────────────────────────────────────────┘
                                   │ on approve
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │  Form Generation Service                    │
                    │  Office Order + Works Order .xlsx files      │
                    │  (openpyxl, stored in DB as LargeBinary)     │
                    └──────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, Alembic, asyncio |
| Database | PostgreSQL |
| AI | Anthropic Claude API (structured extraction) |
| Email | Gmail API (OAuth2) |
| Excel Generation | openpyxl |
| Frontend | React, TypeScript, TanStack Router, TanStack Query |
| UI Components | Radix UI, Tailwind CSS, shadcn/ui |
| Infrastructure | Docker Compose |
