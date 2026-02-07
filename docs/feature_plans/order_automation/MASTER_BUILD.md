# Ramjet Order Automation - Master Build Document

**Version:** 1.1
**Date:** February 7, 2026
**Status:** Ready for Implementation
**Author:** Brett + Claude

---

## Agent Instructions

**READ THIS FIRST.** This feature is built across multiple agent sessions. Each agent works on one phase at a time using a three-document system:

### Documents (all in `docs/feature_plans/order_automation/`)

| Document | Purpose | Who Updates |
|----------|---------|-------------|
| `MASTER_BUILD.md` (this file) | Permanent spec — what to build, architecture, data model, all phases | Only update if requirements change |
| `ORCHESTRATION.md` | Bird's-eye progress — which phases are done, current phase, key decisions | Update at END of every session |
| `PHASE_X_HANDOVER.md` | Tactical handover from the previous phase — files created, gotchas, next steps | Written by finishing agent, read by next agent |

### Start of Session Checklist

1. Read `MASTER_BUILD.md` — understand the full system
2. Read `ORCHESTRATION.md` — see overall progress and which phase you're working on
3. Read the latest `PHASE_X_HANDOVER.md` — get detailed context from the previous phase
4. Enter plan mode for your phase before writing code

### End of Session Checklist

1. Update `ORCHESTRATION.md` — mark your phase complete (or note partial progress)
2. Write `PHASE_X_HANDOVER.md` for the next agent, including:
   - Files created or modified (with paths)
   - Migrations created and whether they've been run
   - Tests written and their pass/fail status
   - Decisions made that deviate from this master doc
   - Known issues or incomplete items
   - Explicit next steps for the next agent
3. Do NOT modify `MASTER_BUILD.md` unless requirements have actually changed

### Key Codebase Patterns

- **Backend:** FastAPI app at `backend/app/main.py`. Routers in `api/`, models in `core/models.py`, services in `services/`.
- **Frontend:** React + TypeScript at `frontend/src/`. File-based routing via TanStack Router in `routes/`. UI components via shadcn/ui in `components/ui/`.
- **Database:** PostgreSQL + SQLAlchemy. Migrations via Alembic (`backend/migrations/`).
- **Auth:** Simple auth (dev) via `SimpleAuthContext`. Use `VITE_USE_SIMPLE_AUTH=true` for development.
- **Form templates:** `docs/template_docs/OFFICE ORDER FORM.xls` and `docs/template_docs/WORKS ORDER FORM MASTER (1).xls`

---

## 1. Overview

Automated order processing system for Ramjet Plastics. Monitors a Gmail inbox for incoming purchase orders (email body, PDF attachments, Excel attachments), extracts structured order data using Claude AI, enriches with product master data, generates Office Order and Works Order Excel forms, and presents them to an operator (Sharon) for review and approval. On approval, completed forms are emailed to configured recipients.

**Goal:** Reduce order processing from 10-20 minutes of manual re-keying to ~2 minutes of review and approval.

**Key Stakeholders:**
- **Grant** - Business owner (Ramjet Plastics)
- **Sharon** - Primary operator (processes orders daily)
- **Brett** - Developer

---

## 2. Architecture

### 2.1 System Flow

```
┌──────────────────────────────────────────────────────────┐
│ GMAIL INBOX                                               │
│ Customers send POs via email (body text, PDF, Excel)      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND (Background Task)                         │
│                                                           │
│  1. Gmail Monitor (OAuth2 → Gmail API)                    │
│     - Polls inbox on interval                             │
│     - Downloads email body + attachments                  │
│     - Stores raw data in PostgreSQL                       │
│                                                           │
│  2. LLM Extraction (Anthropic Claude API)                 │
│     - Accepts email text, PDF (base64), Excel (parsed)    │
│     - Returns structured JSON with confidence scores      │
│                                                           │
│  3. Product Enrichment (PostgreSQL lookup)                 │
│     - Matches extracted product codes to catalog           │
│     - Pulls manufacturing, material, packaging specs       │
│     - Calculates materials, packaging, running time        │
│                                                           │
│  4. Form Generation (openpyxl)                            │
│     - Populates Office Order Form template                │
│     - Populates Works Order templates (one per line item)  │
│     - Stores generated files                              │
│                                                           │
│  5. Email Distribution (on approval)                      │
│     - Emails completed forms to configured recipients      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ REACT FRONTEND                                            │
│                                                           │
│  Dashboard Page:                                          │
│  - Email monitor status (running, last poll, errors)      │
│  - Orders in queue (pending, approved, rejected counts)   │
│  - Recent activity feed                                   │
│                                                           │
│  Order Review Page (combined single page):                │
│  - Left: Original PO source (PDF viewer / email text)     │
│  - Right: Editable extracted data form                    │
│  - Below: Tabbed form preview (Office Order | Works Orders)│
│  - Sticky footer: Approve / Edit / Reject actions         │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Tech Stack (Existing Codebase)

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React 18 + TypeScript | Existing app at `frontend/` |
| **Routing** | TanStack Router (file-based) | Add new route files |
| **UI Components** | shadcn/ui + Radix UI + Tailwind CSS | Existing component library |
| **State/Data** | TanStack React Query | For API data fetching |
| **Forms** | React Hook Form + Zod | For editable order fields |
| **Backend** | FastAPI + Python 3.11 | Existing app at `backend/` |
| **Database** | PostgreSQL + SQLAlchemy | Existing, add new tables |
| **Migrations** | Alembic | Existing setup |
| **Auth** | Simple auth (dev) / Kratos (prod) | Existing, no changes needed |
| **Containers** | Docker Compose | Existing orchestration |

### 2.3 New Dependencies

**Backend (add to requirements.txt):**
```
anthropic>=0.40.0          # Claude API for order extraction
google-auth>=2.20.0        # Gmail OAuth2
google-auth-oauthlib>=1.0  # OAuth2 flow helpers
google-api-python-client>=2.90.0  # Gmail API client
pdfplumber>=0.10.0         # PDF text extraction (fallback)
openpyxl>=3.1.0            # Excel read/write for forms
```

**Frontend (add to package.json):**
```
react-pdf                  # PDF viewer in browser
```

---

## 3. Data Model

### 3.1 New PostgreSQL Tables

All new tables use the existing SQLAlchemy `Base` from `app/core/models.py` and will be added via Alembic migrations.

#### products
The product master catalog. Migrated from the existing SQLite demo database.

```
products
├── id                      UUID (PK, auto)
├── product_code            VARCHAR(50) UNIQUE NOT NULL  -- e.g. "LOCAP2"
├── product_description     VARCHAR(255) NOT NULL
├── customer_name           VARCHAR(255)                 -- primary customer
├── is_active               BOOLEAN DEFAULT TRUE
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### manufacturing_specs
Production parameters per product.

```
manufacturing_specs
├── id                          UUID (PK, auto)
├── product_code                VARCHAR(50) FK → products.product_code
├── mould_no                    VARCHAR(50)
├── cycle_time_seconds          DECIMAL(8,2)
├── shot_weight_grams           DECIMAL(8,2)
├── num_cavities                INTEGER
├── product_weight_grams        DECIMAL(8,2)
├── estimated_running_time_hours DECIMAL(8,2)
├── machine_min_requirements    VARCHAR(255)
├── created_at                  TIMESTAMPTZ
└── updated_at                  TIMESTAMPTZ
```

#### material_specs
Material specifications per product + colour combination.

```
material_specs
├── id                      UUID (PK, auto)
├── product_code            VARCHAR(50) FK → products.product_code
├── colour                  VARCHAR(100) NOT NULL
├── material_grade          VARCHAR(100)
├── material_type           VARCHAR(100)
├── colour_no               VARCHAR(50)
├── colour_supplier         VARCHAR(255)
├── mb_add_rate             DECIMAL(5,2)       -- masterbatch add rate %
├── additive                VARCHAR(255)
├── additive_add_rate       DECIMAL(5,2)       -- additive rate %
├── additive_supplier       VARCHAR(255)
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ

UNIQUE(product_code, colour)
```

#### packaging_specs
Packaging requirements per product.

```
packaging_specs
├── id                      UUID (PK, auto)
├── product_code            VARCHAR(50) FK → products.product_code
├── qty_per_bag             INTEGER
├── bag_size                VARCHAR(100)
├── qty_per_carton          INTEGER
├── carton_size             VARCHAR(100)
├── cartons_per_pallet      INTEGER
├── cartons_per_layer       INTEGER
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### pricing
Unit pricing per product + colour (optionally per customer).

```
pricing
├── id                      UUID (PK, auto)
├── product_code            VARCHAR(50) FK → products.product_code
├── colour                  VARCHAR(100)
├── customer_name           VARCHAR(255) NULL   -- NULL = default price
├── unit_price              DECIMAL(10,2) NOT NULL
├── currency                VARCHAR(3) DEFAULT 'AUD'
├── effective_date          DATE
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### incoming_emails
Raw email data captured from Gmail.

```
incoming_emails
├── id                      UUID (PK, auto)
├── gmail_message_id        VARCHAR(255) UNIQUE NOT NULL
├── from_address            VARCHAR(255)
├── from_name               VARCHAR(255)
├── subject                 VARCHAR(500)
├── body_text               TEXT                -- plain text body
├── body_html               TEXT                -- HTML body
├── received_at             TIMESTAMPTZ
├── processed               BOOLEAN DEFAULT FALSE
├── processing_error        TEXT NULL
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### email_attachments
Files attached to incoming emails.

```
email_attachments
├── id                      UUID (PK, auto)
├── email_id                UUID FK → incoming_emails.id
├── filename                VARCHAR(255)
├── content_type            VARCHAR(100)       -- e.g. "application/pdf"
├── file_data               BYTEA              -- raw file bytes
├── file_size_bytes         INTEGER
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### orders
Extracted and enriched order data.

```
orders
├── id                      UUID (PK, auto)
├── email_id                UUID FK → incoming_emails.id NULL
├── status                  VARCHAR(20) NOT NULL DEFAULT 'pending'
│                           -- pending | approved | rejected | error
├── customer_name           VARCHAR(255)
├── po_number               VARCHAR(100)
├── po_date                 DATE
├── delivery_date           DATE NULL
├── special_instructions    TEXT NULL
├── extraction_confidence   DECIMAL(3,2)       -- 0.00 to 1.00
├── extraction_raw_json     JSONB              -- raw LLM output
├── approved_by             UUID FK → users.id NULL
├── approved_at             TIMESTAMPTZ NULL
├── rejected_reason         TEXT NULL
├── office_order_file       BYTEA NULL         -- generated Excel bytes
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### order_line_items
Individual products within an order.

```
order_line_items
├── id                      UUID (PK, auto)
├── order_id                UUID FK → orders.id
├── line_number             INTEGER NOT NULL
├── product_code            VARCHAR(50)         -- as extracted
├── matched_product_code    VARCHAR(50) FK → products.product_code NULL
├── product_description     VARCHAR(255)        -- as extracted
├── colour                  VARCHAR(100)
├── quantity                INTEGER NOT NULL
├── unit_price              DECIMAL(10,2) NULL
├── line_total              DECIMAL(12,2) NULL
├── confidence              DECIMAL(3,2)        -- field-level confidence
├── needs_review            BOOLEAN DEFAULT FALSE
├── works_order_file        BYTEA NULL          -- generated Excel bytes
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### email_monitor_status
Tracks the health of the background email polling task.

```
email_monitor_status
├── id                      INTEGER PK DEFAULT 1  -- singleton row
├── is_running              BOOLEAN DEFAULT FALSE
├── last_poll_at            TIMESTAMPTZ NULL
├── last_success_at         TIMESTAMPTZ NULL
├── last_error              TEXT NULL
├── last_error_at           TIMESTAMPTZ NULL
├── emails_processed_total  INTEGER DEFAULT 0
├── updated_at              TIMESTAMPTZ
```

### 3.2 Indexes

```sql
-- Product lookups
CREATE INDEX idx_products_code ON products(product_code);
CREATE INDEX idx_products_customer ON products(customer_name);
CREATE INDEX idx_material_specs_product_colour ON material_specs(product_code, colour);
CREATE INDEX idx_pricing_product_colour ON pricing(product_code, colour);

-- Order processing
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_email ON orders(email_id);
CREATE INDEX idx_incoming_emails_processed ON incoming_emails(processed);
CREATE INDEX idx_incoming_emails_gmail_id ON incoming_emails(gmail_message_id);
```

---

## 4. Backend Modules

All new code lives under `backend/app/`. Follow existing patterns (SQLAlchemy models in `core/models.py`, routers in `api/`, services in `services/`).

### 4.1 New Files

```
backend/app/
├── core/
│   └── models.py                    ← ADD new table models here
├── api/
│   ├── orders.py                    ← NEW: Order CRUD + review endpoints
│   ├── products.py                  ← NEW: Product catalog endpoints
│   └── system.py                    ← NEW: Email monitor status endpoints
├── services/
│   ├── gmail_service.py             ← NEW: Gmail OAuth2 + inbox polling
│   ├── extraction_service.py        ← NEW: Claude API extraction pipeline
│   ├── enrichment_service.py        ← NEW: Product lookup + calculations
│   └── form_generation_service.py   ← NEW: Excel form population
├── templates/                        ← Excel form templates (copied from source)
│   ├── OFFICE_ORDER_FORM.xls        ← Source: docs/template_docs/OFFICE ORDER FORM.xls
│   └── WORKS_ORDER_FORM.xls         ← Source: docs/template_docs/WORKS ORDER FORM MASTER (1).xls
└── main.py                          ← ADD router includes + background task startup
```

### 4.2 gmail_service.py

Handles Gmail OAuth2 authentication and inbox polling.

**Responsibilities:**
- OAuth2 token management (initial auth flow, refresh tokens)
- Poll inbox for new unread messages
- Download email body (text + HTML) and attachments (PDF, Excel, images)
- Store raw email data in `incoming_emails` + `email_attachments` tables
- Mark emails as read in Gmail after processing
- Update `email_monitor_status` singleton

**Background Task:**
- Runs inside FastAPI using `asyncio.create_task()` on startup
- Configurable poll interval (default: 60 seconds)
- Graceful shutdown on app teardown
- Error isolation (one email failure doesn't stop polling)

**OAuth2 Flow:**
- Uses `google-auth-oauthlib` for initial consent
- Stores refresh token in database or `.env`
- Auto-refreshes access tokens
- Scopes: `gmail.readonly`, `gmail.modify` (to mark as read)

**Configuration (.env):**
```
GMAIL_CLIENT_ID=<from Google Cloud Console>
GMAIL_CLIENT_SECRET=<from Google Cloud Console>
GMAIL_REFRESH_TOKEN=<obtained during initial OAuth2 consent>
GMAIL_POLL_INTERVAL_SECONDS=60
GMAIL_WATCH_LABEL=INBOX
```

### 4.3 extraction_service.py

Handles multi-format order extraction via Claude API.

**Responsibilities:**
- Accept raw email data (body text + attachments)
- Detect attachment types and prepare for LLM
- Send to Claude API with structured extraction prompt
- Return standardised JSON with per-field confidence scores
- Handle extraction failures gracefully

**Multi-Format Handling:**
```
Email body text  → Send as text content to Claude
PDF attachment   → Send as base64 document to Claude (native PDF support)
Excel attachment → Parse with openpyxl → convert to structured text → send to Claude
Image attachment → Send as base64 image to Claude (vision capability)
```

**Extraction Output Schema:**
```json
{
  "customer_name": { "value": "Shape Aluminium", "confidence": 0.98 },
  "po_number": { "value": "12022", "confidence": 0.99 },
  "po_date": { "value": "2026-02-04", "confidence": 0.95 },
  "delivery_date": { "value": null, "confidence": 0.0 },
  "special_instructions": { "value": "MUST BE UV STABLE", "confidence": 0.97 },
  "line_items": [
    {
      "product_code": { "value": "LOCAP2", "confidence": 0.96 },
      "description": { "value": "LOUVRE END CAP 152mm", "confidence": 0.94 },
      "quantity": { "value": 1000, "confidence": 0.99 },
      "colour": { "value": "Black", "confidence": 0.90 },
      "unit_price": { "value": 1.32, "confidence": 0.88 }
    }
  ],
  "overall_confidence": 0.95
}
```

**Configuration (.env):**
```
ANTHROPIC_API_KEY=<your key>
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### 4.4 enrichment_service.py

Matches extracted data against the product catalog and performs calculations.

**Responsibilities:**
- Match extracted product codes to `products` table (exact + fuzzy)
- Pull full specs from `manufacturing_specs`, `material_specs`, `packaging_specs`
- Look up pricing from `pricing` table
- Calculate:
  - Total material required (kg) = product_weight * qty * 1.05 waste factor
  - Masterbatch required (kg) = total_material * mb_add_rate
  - Additive required (kg) = total_material * additive_add_rate
  - Base material (kg) = total_material - masterbatch - additive
  - Bags needed = CEIL(qty / qty_per_bag)
  - Cartons needed = CEIL(qty / qty_per_carton)
  - Running time (hrs) = (cycle_time * qty) / (num_cavities * 3600)
- Flag unmatched products for manual review (`needs_review = True`)

**Fuzzy Matching:**
- Exact match on `product_code` first
- Then case-insensitive match
- Then partial match on description
- Assign lower confidence to fuzzy matches

### 4.5 form_generation_service.py

Generates populated Excel forms using openpyxl.

**Responsibilities:**
- Load Excel templates from `backend/app/templates/`
- Populate Office Order Form (F-21) with order header + line items
- Populate Works Order Form per line item with full specs from enrichment
- Return Excel file bytes (stored in `orders.office_order_file` and `order_line_items.works_order_file`)

**Office Order Form Fields:**
- Customer name, date, PO number
- Line items: product code, description, colour, qty, unit price, line total
- Order total
- Special instructions

**Works Order Form Fields (per line item, 30+ fields):**
- Header: date, WO#, product code, description, qty, due date
- Manufacturing: mould no, cycle time, shot weight, cavities, product weight, running time, machine requirements
- Material: grade, type, colour, colour no, supplier, MB add rate, additive, additive rate, additive supplier
- Packaging: qty per bag, bag size, qty per carton, carton size, cartons per pallet
- Calculated: total material kg, masterbatch kg, additive kg, base material kg, bags needed, cartons needed

### 4.6 API Endpoints

#### Orders Router (`api/orders.py`, prefix: `/api/orders`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List orders (filterable by status) |
| `GET` | `/{order_id}` | Get order with line items + source email |
| `PUT` | `/{order_id}` | Update order fields (edit before approve) |
| `PUT` | `/{order_id}/line-items/{item_id}` | Update a single line item |
| `POST` | `/{order_id}/approve` | Approve order → generate forms → email |
| `POST` | `/{order_id}/reject` | Reject order with reason |
| `GET` | `/{order_id}/forms/office-order` | Download Office Order Excel |
| `GET` | `/{order_id}/forms/works-order/{item_id}` | Download Works Order Excel |
| `GET` | `/{order_id}/source-pdf/{attachment_id}` | Serve original PDF attachment |
| `POST` | `/{order_id}/reprocess` | Re-run LLM extraction |

#### Products Router (`api/products.py`, prefix: `/api/products`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List all products (search, filter by customer) |
| `GET` | `/{product_code}` | Get full product specs |
| `GET` | `/{product_code}/calculate` | Calculate materials for given qty + colour |

#### System Router (`api/system.py`, prefix: `/api/system`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/email-monitor/status` | Get email monitor health |
| `POST` | `/email-monitor/start` | Start polling (if stopped) |
| `POST` | `/email-monitor/stop` | Stop polling |
| `POST` | `/email-monitor/poll-now` | Trigger immediate poll |

---

## 5. Frontend Pages

All new pages follow existing patterns: file-based routes in `frontend/src/routes/`, shadcn/ui components, TanStack React Query for data fetching, Tailwind CSS for styling.

### 5.1 New Files

```
frontend/src/
├── routes/
│   ├── orders/
│   │   ├── index.tsx                ← Dashboard (system status + order list)
│   │   └── $orderId.tsx             ← Combined Order Review page
│   └── products/
│       └── index.tsx                ← Product catalog browser (optional)
├── components/
│   ├── orders/
│   │   ├── OrderList.tsx            ← Table of orders with status badges
│   │   ├── SystemStatus.tsx         ← Email monitor health card
│   │   ├── OrderSourcePanel.tsx     ← PDF viewer / email text display
│   │   ├── OrderDataForm.tsx        ← Editable extracted data form
│   │   ├── FormPreview.tsx          ← Tabbed Office Order / Works Order preview
│   │   ├── ConfidenceBadge.tsx      ← Colour-coded confidence indicator
│   │   ├── OrderActions.tsx         ← Approve / Edit / Reject button bar
│   │   └── RejectDialog.tsx         ← Modal for rejection reason
│   └── products/
│       └── ProductSearch.tsx        ← Product code autocomplete
├── services/
│   ├── orderService.ts             ← Order API calls
│   ├── productService.ts           ← Product API calls
│   └── systemService.ts            ← System status API calls
└── hooks/
    ├── useOrders.ts                 ← React Query hooks for orders
    ├── useProducts.ts               ← React Query hooks for products
    └── useSystemStatus.ts           ← React Query hook for monitor status
```

### 5.2 Dashboard Page (`/orders`)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Header (existing)                                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Email Monitor │ │ Pending: 3   │ │ Processed    │    │
│  │ ● Running     │ │              │ │ Today: 12    │    │
│  │ Last: 30s ago │ │              │ │              │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
│  Orders                                    [Filter ▾]   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Status │ Customer        │ PO#    │ Items │ Date  │   │
│  │ ● Pend │ Shape Aluminium │ 12022  │ 2     │ Today │   │
│  │ ● Pend │ Cleber Pty Ltd  │ PO0020 │ 5     │ Today │   │
│  │ ✓ Appr │ ABC Plastics    │ 4455   │ 1     │ Yest. │   │
│  │ ✗ Rej  │ Widget Corp     │ 9901   │ 3     │ Yest. │   │
│  └──────────────────────────────────────────────────┘   │
│  Clicking a row navigates to /orders/{orderId}           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Components Used:**
- `SystemStatus` — card showing email monitor health (polls `/api/system/email-monitor/status`)
- `OrderList` — table with status badges, clickable rows
- shadcn `Card`, `Table`, `Badge`, `Select` (for filter)

### 5.3 Order Review Page (`/orders/{orderId}`)

This is the combined review + preview + approve page.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Header (existing)                                        │
├─────────────────────────────────────────────────────────┤
│ ← Back to Orders    Shape Aluminium - PO 12022   [Pending]│
├──────────────────────────┬──────────────────────────────┤
│                          │                               │
│  ORIGINAL SOURCE         │  EXTRACTED ORDER DATA         │
│                          │                               │
│  [Email] [PDF: po.pdf]   │  Customer: [Shape Aluminium ] │
│                          │  PO #:     [12022          ] │
│  ┌────────────────────┐  │  PO Date:  [2026-02-04     ] │
│  │                    │  │  Delivery:  [              ] │
│  │   PDF Viewer       │  │                               │
│  │   or               │  │  Line Items:                  │
│  │   Email body text  │  │  ┌───────────────────────────┐│
│  │                    │  │  │ 1. LOCAP2 ● 96%           ││
│  │                    │  │  │    Qty: [1000] Black       ││
│  │                    │  │  │    Price: $1.32  = $1,320  ││
│  │                    │  │  ├───────────────────────────┤│
│  │                    │  │  │ 2. GLCAPRB ● 94%          ││
│  │                    │  │  │    Qty: [1000] Black       ││
│  │                    │  │  │    Price: $0.73  = $730    ││
│  │                    │  │  └───────────────────────────┘│
│  └────────────────────┘  │                               │
│                          │  Special: MUST BE UV STABLE    │
│                          │  Overall Confidence: 95%       │
├──────────────────────────┴──────────────────────────────┤
│                                                          │
│  [Office Order] [WO: LOCAP2] [WO: GLCAPRB]              │
│  ┌──────────────────────────────────────────────────┐   │
│  │                                                    │   │
│  │   Form Preview (rendered as HTML table             │   │
│  │   matching the Excel template layout)              │   │
│  │                                                    │   │
│  │   Office Order shows: customer, PO, line items,    │   │
│  │   totals, special instructions                     │   │
│  │                                                    │   │
│  │   Works Orders show: full 30+ field breakdown      │   │
│  │   per product including material calcs             │   │
│  │                                                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  [✓ Approve & Email]          [✎ Edit]     [✗ Reject]   │
└──────────────────────────────────────────────────────────┘
```

**Behaviour:**
- Fields are **read-only by default**. Clicking "Edit" toggles all fields to editable.
- Editing a field recalculates downstream values (totals, material calcs) and regenerates form previews.
- "Approve & Email" triggers `POST /api/orders/{id}/approve` → generates final Excel files → emails them.
- "Reject" opens a dialog for a reason, triggers `POST /api/orders/{id}/reject`.
- Confidence badges: green (>90%), amber (70-90%), red (<70%).
- Fields with `needs_review = true` are highlighted with a warning indicator.

**Components Used:**
- `OrderSourcePanel` — tabs for email body vs PDF viewer (react-pdf)
- `OrderDataForm` — React Hook Form with Zod validation, inline confidence badges
- `FormPreview` — HTML table rendering of the Excel forms (tabs per form)
- `ConfidenceBadge` — colour-coded pill showing confidence %
- `OrderActions` — sticky bottom bar with Approve / Edit / Reject
- `RejectDialog` — shadcn Dialog with textarea for reason
- `ProductSearch` — autocomplete for product code field (queries `/api/products`)

---

## 6. Email Distribution (On Approval)

When Sharon clicks "Approve & Email":

1. Backend generates final Office Order + Works Order Excel files
2. Files are stored in the `orders` and `order_line_items` tables
3. Email is sent via the existing `email_service.py` with forms attached
4. Order status updated to `approved`

**Configuration (.env):**
```
ORDER_EMAIL_RECIPIENTS=sharon@ramjetplastics.com,production@ramjetplastics.com
ORDER_EMAIL_CC=grant@ramjetplastics.com
```

The email service already supports Mailgun and SMTP. We extend it with a new convenience method `send_approved_order()` that attaches the generated Excel files.

---

## 7. Build Phases

Each phase is independently buildable and testable. A future agent should take one phase at a time and enter plan mode for that phase.

### Phase 1: Database & Product Data
**Scope:** Add product tables to PostgreSQL, migrate demo data, create product API.

- Add SQLAlchemy models for: `products`, `manufacturing_specs`, `material_specs`, `packaging_specs`, `pricing`
- Create Alembic migration
- Write seed script to migrate 57 products from existing SQLite demo DB
- Create `api/products.py` router with list, get, calculate endpoints
- Create `services/enrichment_service.py` with product lookup + calculation logic
- Test: query products via API, verify calculations match existing `product_lookup.py`

**Dependencies:** None
**Estimated effort:** Small

### Phase 2: Gmail OAuth2 Integration
**Scope:** Connect to Gmail, poll for emails, store raw data.

- Set up Google Cloud project + OAuth2 credentials (manual step, document in README)
- Create `services/gmail_service.py` with OAuth2 token management
- Add SQLAlchemy models for: `incoming_emails`, `email_attachments`, `email_monitor_status`
- Create Alembic migration
- Implement background polling task in FastAPI startup
- Create `api/system.py` router for monitor status
- Test: send test email to Gmail account, verify it appears in DB

**Dependencies:** None (parallel with Phase 1)
**Estimated effort:** Medium

### Phase 3: LLM Extraction Pipeline
**Scope:** Extract structured order data from emails using Claude.

- Create `services/extraction_service.py`
- Implement multi-format handling (text, PDF base64, Excel parse)
- Design and test Claude extraction prompt
- Add SQLAlchemy models for: `orders`, `order_line_items`
- Create Alembic migration
- Wire into email processing: new email → extract → create order
- Test: process the two real customer POs (Shape Aluminium, Cleber)

**Dependencies:** Phase 1 (for product matching), Phase 2 (for email input)
**Estimated effort:** Medium

### Phase 4: Form Generation
**Scope:** Generate populated Excel forms from enriched order data.

- Obtain/create Office Order and Works Order Excel templates
- Create `services/form_generation_service.py`
- Map enriched data fields to Excel cell positions
- Generate Office Order form (one per order)
- Generate Works Order forms (one per line item)
- Store generated files in order tables
- Test: generate forms for Shape Aluminium order, compare to manual version

**Dependencies:** Phase 1 + Phase 3
**Estimated effort:** Medium

### Phase 5: Frontend - Dashboard & Order Review
**Scope:** Build the two frontend pages.

- Create route files: `orders/index.tsx`, `orders/$orderId.tsx`
- Create `api/orders.py` router (list, get, update, approve, reject)
- Build all frontend components (see section 5.1)
- Wire up TanStack React Query hooks
- Implement editable form with recalculation
- Implement PDF viewer for source documents
- Implement form preview (HTML rendering of Excel data)
- Implement approve/reject workflow
- Add navigation link in Header
- Test: full walkthrough from dashboard → review → approve

**Dependencies:** Phase 3 + Phase 4
**Estimated effort:** Large

### Phase 6: Email Distribution
**Scope:** Email approved forms to configured recipients.

- Extend `email_service.py` with `send_approved_order()` method
- Attach Office Order + Works Order Excel files to email
- Trigger on approval
- Add configuration for recipients
- Test: approve an order, verify email arrives with correct attachments

**Dependencies:** Phase 4 + Phase 5
**Estimated effort:** Small

### Phase 7: Polish & Demo Prep
**Scope:** End-to-end testing, bug fixes, demo readiness.

- End-to-end test: send email → extraction → review → approve → email received
- Error handling and edge cases
- Loading states, empty states, error states in UI
- Mobile responsiveness (basic)
- Demo walkthrough documentation

**Dependencies:** All previous phases
**Estimated effort:** Small-Medium

---

## 8. Configuration Summary

All new environment variables to add to `.env`:

```bash
# Gmail OAuth2
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_POLL_INTERVAL_SECONDS=60

# Anthropic Claude API
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Order Distribution
ORDER_EMAIL_RECIPIENTS=sharon@ramjetplastics.com
ORDER_EMAIL_CC=grant@ramjetplastics.com

# Form Templates (source: docs/template_docs/)
FORM_TEMPLATES_PATH=/app/templates
```

---

## 9. Open Questions

These should be resolved before or during implementation:

1. **Excel templates** — ✅ RESOLVED. Templates available at:
   - `docs/template_docs/OFFICE ORDER FORM.xls`
   - `docs/template_docs/WORKS ORDER FORM MASTER (1).xls`
   These will be copied into `backend/app/templates/` during Phase 4 and cell positions mapped for openpyxl population.

2. **Gmail account** — Which Gmail address will be used? Needs Google Cloud project setup with Gmail API enabled.

3. **Works Order numbering** — How are WO numbers generated? Sequential? Per-year? Need to define the scheme.

4. **Product data source** — The 57 demo products are sufficient for the prototype. For production, Grant needs to provide the real product master data.

5. **Form preview fidelity** — Should the HTML preview exactly mirror the Excel layout, or is a clean data representation sufficient for the demo?

---

## 10. Success Criteria

**For the demo to Grant:**
- Send a test email with a PO PDF to the Gmail inbox
- System automatically picks it up and extracts the order
- Sharon (or Grant) opens the dashboard and sees the pending order
- Clicks into the order review page
- Sees the original PO alongside the extracted data
- Reviews the auto-populated forms
- Clicks "Approve & Email"
- Receives the completed Office Order and Works Orders in their inbox
- Total time from email to approval: under 2 minutes

---

*This document is the single source of truth for the Order Automation feature. Each build phase should reference this document. Future agents should read this before planning any implementation work.*
