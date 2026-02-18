# Ramjet Stock Tracking System - Master Build Document

**Version:** 1.0
**Date:** February 11, 2026
**Status:** Ready for Implementation
**Author:** Brett + Claude

---

## Agent Instructions

**READ THIS FIRST.** This feature is built across multiple agent sessions. Each agent works on one phase at a time using a three-document system:

### Documents (all in `docs/feature_plans/stock_tracking/`)

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
- **Existing product catalog:** `products`, `manufacturing_specs`, `material_specs`, `packaging_specs`, `pricing` tables already exist (built in order automation Phase 1).

---

## 1. Overview

A real-time stock tracking system for Ramjet Plastics. Uses QR-code-labelled cartons scanned via Bluetooth barcode scanners to maintain a live inventory ledger of finished goods and raw materials.

**The Problem:**
- Warehouse staff currently print order forms and physically walk the factory to count stock
- No regular stocktake cadence exists
- Stock counts happen ad-hoc before production runs to determine what's already on hand
- This manual process is slow, error-prone, and gives no visibility into stock levels between counts

**The Solution:**
- Every carton of finished goods gets a unique QR code label at the end of a production run
- Scanning cartons IN (production complete) and OUT (order fulfilment) maintains a live stock ledger
- Real-time stock levels are always visible — no manual counting required
- Quarterly stocktakes become verification exercises, not the primary count
- Raw materials are tracked by receiving deliveries in and recording usage out

**Goal:** Eliminate manual stock counting. Provide real-time visibility into finished goods and raw material inventory levels.

**Key Stakeholders:**
- **Grant** — Business owner (Ramjet Plastics)
- **Sharon** — Office/orders (uses dashboard for stock visibility)
- **Warehouse Staff** — Primary scanner operators (stock in, stock out, stocktakes)
- **Brett** — Developer

---

## 2. Architecture

### 2.1 System Flow

```
PRODUCTION LINE
│
▼
┌──────────────────────────────────────────────────────────┐
│ END OF PRODUCTION RUN                                     │
│                                                           │
│  1. Generate QR labels (unique per carton)                │
│     - Pink label = full carton                            │
│     - Yellow label = part-filled carton                   │
│  2. Print labels on regular printer                       │
│  3. Stick labels on cartons                               │
│  4. Scan each carton → STOCK IN                           │
│                                                           │
│  Tablet + Bluetooth Zebra DS22 scanner                    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND (Mac Mini M4)                             │
│                                                           │
│  - Receives scan events via REST API                      │
│  - Updates stock ledger (movement records)                │
│  - Calculates live stock levels                           │
│  - Generates QR codes and printable labels                │
│  - Manages raw material inventory                         │
│  - Produces reports and exports                           │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ REACT FRONTEND (Tablets + Desktop via WiFi)               │
│                                                           │
│  Scanning Interface:                                      │
│  - Mode selector: Stock In / Stock Out / Stocktake        │
│  - Auto-focused input captures scanner HID input          │
│  - Visual + audio feedback on scan                        │
│  - Partial box quantity entry                             │
│                                                           │
│  Stock Dashboard:                                         │
│  - Colour-coded stock levels (green/amber/red)            │
│  - Search and filter by product, colour, status           │
│  - Drill-down to individual carton history                │
│                                                           │
│  Product Management:                                      │
│  - Full CRUD for products                                 │
│  - Stock threshold configuration                          │
│                                                           │
│  Raw Materials:                                           │
│  - Receive deliveries, record usage                       │
│  - Stock levels with thresholds                           │
│                                                           │
│  Reports:                                                 │
│  - Stock valuation                                        │
│  - Movement history                                       │
│  - Point-in-time stock on hand                            │
│  - Spreadsheet export                                     │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Infrastructure

| Component | Details |
|-----------|---------|
| **Server** | Mac Mini M4 running Docker (backend + frontend + PostgreSQL) |
| **Tablets** | Cheap Android/iPad tablets, connected via WiFi to Mac Mini's IP |
| **Scanner** | Zebra DS22 series, Bluetooth paired to tablet, HID keyboard mode |
| **Labels** | Printed on regular printer (A4 sheets of sticker labels) |
| **Network** | All devices on same WiFi network. App accessed via Mac Mini's local IP (e.g., `http://192.168.1.x:5179`) |

### 2.3 Scanner Integration

The Zebra DS22 in Bluetooth HID mode acts as a wireless keyboard. When a QR code is scanned, the scanner "types" the QR content into the focused text field in the browser, followed by an Enter keystroke.

**Web app behaviour:**
1. Scanning page has an auto-focused text input
2. Scanner sends QR content as keystrokes → input field fills
3. Enter key triggers form submission
4. Backend processes the scan event
5. UI shows result (success/error) with visual and audio feedback
6. Input field auto-clears and re-focuses for next scan

No native app required. No special drivers. Pure web.

### 2.4 Tech Stack (Existing)

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React 18 + TypeScript | Existing app |
| **Routing** | TanStack Router (file-based) | Add new routes |
| **UI** | shadcn/ui + Tailwind CSS | Existing components + new ones |
| **Data** | TanStack React Query | For API data fetching |
| **Backend** | FastAPI + Python 3.11 | Existing app |
| **Database** | PostgreSQL + SQLAlchemy | Existing, add new tables |
| **Migrations** | Alembic | Existing setup |
| **Auth** | Simple auth (dev) | Existing, no changes |
| **Containers** | Docker Compose | Existing orchestration |

### 2.5 New Dependencies

**Backend (add to requirements.txt):**
```
qrcode[pil]>=7.4          # QR code generation
Pillow>=10.0               # Image processing for label rendering
reportlab>=4.0             # PDF generation for printable labels
openpyxl>=3.1.0            # Spreadsheet export (already installed)
```

**Frontend (add to package.json):**
```
(none expected — standard web APIs + existing libraries sufficient)
```

---

## 3. Data Model

### 3.1 New PostgreSQL Tables

All new tables use the existing SQLAlchemy `Base` from `app/core/models.py` and will be added via Alembic migrations.

#### stock_items

Individual cartons tracked in the warehouse. Each has a unique QR code.

```
stock_items
├── id                      UUID (PK, auto)
├── barcode_id              VARCHAR(100) UNIQUE NOT NULL  -- QR content, e.g. "RJ-LOCAP2-BLK-20260211-001"
├── product_code            VARCHAR(50) FK → products.product_code NOT NULL
├── colour                  VARCHAR(100) NOT NULL
├── quantity                INTEGER NOT NULL              -- units in this carton
├── box_type                VARCHAR(10) NOT NULL          -- 'full' | 'partial'
├── status                  VARCHAR(20) NOT NULL DEFAULT 'in_stock'
│                           -- in_stock | picked | scrapped | consumed
├── production_date         DATE                          -- when the production run completed
├── scanned_in_at           TIMESTAMPTZ                   -- when first scanned into warehouse
├── scanned_in_by           UUID FK → users.id NULL
├── scanned_out_at          TIMESTAMPTZ NULL              -- when scanned out
├── scanned_out_by          UUID FK → users.id NULL
├── order_id                UUID FK → orders.id NULL      -- linked order (if picked for fulfilment)
├── parent_stock_item_id    UUID FK → stock_items.id NULL -- original full box (if this is a partial repack)
├── notes                   TEXT NULL
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

**Barcode ID format:** `RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}`
- Example: `RJ-LOCAP2-BLK-20260211-001`
- Colour short codes derived from colour name (first 3 chars uppercase, or configurable mapping)
- Sequence resets daily per product+colour combination

#### stock_movements

Immutable ledger of every stock change. Stock levels are derived from this table.

```
stock_movements
├── id                      UUID (PK, auto)
├── stock_item_id           UUID FK → stock_items.id NOT NULL
├── movement_type           VARCHAR(20) NOT NULL
│                           -- stock_in | stock_out | adjustment | stocktake_verified | partial_repack
├── quantity_change          INTEGER NOT NULL              -- positive = in, negative = out
├── reason                  TEXT NULL                      -- required for adjustments
├── order_id                UUID FK → orders.id NULL       -- for order fulfilment movements
├── stocktake_session_id    UUID FK → stocktake_sessions.id NULL
├── performed_by            UUID FK → users.id NOT NULL
├── created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

#### stock_thresholds

Per-product colour thresholds for colour-coded stock level display.

```
stock_thresholds
├── id                      UUID (PK, auto)
├── product_code            VARCHAR(50) FK → products.product_code NOT NULL
├── colour                  VARCHAR(100) NULL              -- NULL = all colours for this product
├── red_threshold           INTEGER NOT NULL DEFAULT 0     -- below this = red (critical)
├── amber_threshold         INTEGER NOT NULL DEFAULT 0     -- below this = amber (warning)
├── created_at              TIMESTAMPTZ
├── updated_at              TIMESTAMPTZ
│
UNIQUE(product_code, colour)
```

**Colour logic:**
- Stock quantity >= amber_threshold → **Green** (healthy)
- Stock quantity >= red_threshold but < amber_threshold → **Amber** (low)
- Stock quantity < red_threshold → **Red** (critical)

#### stocktake_sessions

Quarterly stocktake verification sessions.

```
stocktake_sessions
├── id                      UUID (PK, auto)
├── name                    VARCHAR(255)                   -- e.g. "Q1 2026 Stocktake"
├── status                  VARCHAR(20) NOT NULL DEFAULT 'in_progress'
│                           -- in_progress | completed | cancelled
├── started_by              UUID FK → users.id NOT NULL
├── completed_by            UUID FK → users.id NULL
├── started_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── completed_at            TIMESTAMPTZ NULL
├── total_expected          INTEGER NULL                   -- cartons expected (from system)
├── total_scanned           INTEGER NULL                   -- cartons actually scanned
├── total_discrepancies     INTEGER NULL                   -- mismatches found
├── notes                   TEXT NULL
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### stocktake_scans

Individual scan records during a stocktake session.

```
stocktake_scans
├── id                      UUID (PK, auto)
├── session_id              UUID FK → stocktake_sessions.id NOT NULL
├── barcode_scanned         VARCHAR(100) NOT NULL
├── stock_item_id           UUID FK → stock_items.id NULL  -- NULL if barcode not recognised
├── scan_result             VARCHAR(20) NOT NULL
│                           -- found | not_in_system | already_scanned | wrong_status
├── scanned_by              UUID FK → users.id NOT NULL
├── scanned_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── notes                   TEXT NULL
```

#### raw_materials

Raw material master data (resin, masterbatch, additives, packaging materials, etc.).

```
raw_materials
├── id                      UUID (PK, auto)
├── material_code           VARCHAR(50) UNIQUE NOT NULL    -- e.g. "RM-HDPE-BLACK"
├── material_name           VARCHAR(255) NOT NULL          -- e.g. "HDPE Resin - Black"
├── material_type           VARCHAR(50) NOT NULL           -- resin | masterbatch | additive | packaging | other
├── unit_of_measure         VARCHAR(20) NOT NULL           -- kg | litres | units | rolls
├── current_stock           DECIMAL(12,2) NOT NULL DEFAULT 0  -- cached current level
├── red_threshold           DECIMAL(12,2) NOT NULL DEFAULT 0
├── amber_threshold         DECIMAL(12,2) NOT NULL DEFAULT 0
├── default_supplier        VARCHAR(255) NULL
├── unit_cost               DECIMAL(10,2) NULL             -- latest unit cost
├── is_active               BOOLEAN DEFAULT TRUE
├── notes                   TEXT NULL
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

#### raw_material_movements

Immutable ledger of all raw material stock changes.

```
raw_material_movements
├── id                      UUID (PK, auto)
├── raw_material_id         UUID FK → raw_materials.id NOT NULL
├── movement_type           VARCHAR(20) NOT NULL
│                           -- received | used | adjustment | stocktake
├── quantity                DECIMAL(12,2) NOT NULL         -- positive = in, negative = out
├── unit_cost               DECIMAL(10,2) NULL             -- cost per unit (for received)
├── supplier                VARCHAR(255) NULL              -- for received
├── delivery_note           VARCHAR(255) NULL              -- delivery reference
├── reason                  TEXT NULL                      -- for adjustments
├── performed_by            UUID FK → users.id NOT NULL
├── created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### 3.2 Indexes

```sql
-- Stock items
CREATE INDEX idx_stock_items_barcode ON stock_items(barcode_id);
CREATE INDEX idx_stock_items_product ON stock_items(product_code, colour);
CREATE INDEX idx_stock_items_status ON stock_items(status);
CREATE INDEX idx_stock_items_order ON stock_items(order_id);

-- Stock movements
CREATE INDEX idx_stock_movements_item ON stock_movements(stock_item_id);
CREATE INDEX idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_stock_movements_date ON stock_movements(created_at);
CREATE INDEX idx_stock_movements_order ON stock_movements(order_id);

-- Stocktake
CREATE INDEX idx_stocktake_scans_session ON stocktake_scans(session_id);
CREATE INDEX idx_stocktake_scans_barcode ON stocktake_scans(barcode_scanned);

-- Raw materials
CREATE INDEX idx_raw_materials_code ON raw_materials(material_code);
CREATE INDEX idx_raw_materials_type ON raw_materials(material_type);
CREATE INDEX idx_raw_material_movements_material ON raw_material_movements(raw_material_id);
CREATE INDEX idx_raw_material_movements_date ON raw_material_movements(created_at);
```

### 3.3 Modifications to Existing Tables

**products** — Add `is_stockable` field:
```
├── is_stockable            BOOLEAN DEFAULT TRUE           -- whether this product is tracked in stock
```

No other existing tables are modified. The stock system reads from the existing product catalog and order tables but does not alter them.

---

## 4. Backend Modules

### 4.1 New Files

```
backend/app/
├── api/
│   ├── stock.py                        ← NEW: Stock CRUD, scan events, movements
│   ├── raw_materials.py                ← NEW: Raw material CRUD + movements
│   ├── stocktake.py                    ← NEW: Stocktake session management
│   ├── reports.py                      ← NEW: Stock reports + export
│   └── products.py                     ← MODIFY: Add full CRUD (currently read-only)
├── services/
│   ├── stock_service.py                ← NEW: Core stock logic (scan in/out, levels, thresholds)
│   ├── barcode_service.py              ← NEW: QR code generation + label rendering
│   ├── raw_material_service.py         ← NEW: Raw material inventory logic
│   ├── stocktake_service.py            ← NEW: Stocktake session + discrepancy logic
│   └── report_service.py              ← NEW: Report generation + spreadsheet export
├── schemas/
│   ├── stock_schemas.py                ← NEW: Pydantic models for stock
│   ├── raw_material_schemas.py         ← NEW: Pydantic models for raw materials
│   ├── stocktake_schemas.py            ← NEW: Pydantic models for stocktakes
│   └── report_schemas.py              ← NEW: Pydantic models for reports
├── core/
│   └── models.py                       ← MODIFY: Add all new table models
└── main.py                             ← MODIFY: Register new routers
```

### 4.2 barcode_service.py

Generates unique QR codes and printable label images/PDFs.

**Responsibilities:**
- Generate unique barcode IDs following the format `RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}`
- Render QR code images using the `qrcode` library
- Compose printable labels with QR code + human-readable text (product code, colour, quantity, date)
- Support batch label generation (e.g., "generate 20 labels for LOCAP2 Black, 500/carton")
- Output as PDF (multiple labels per A4 page) for printing on sticker sheets
- Differentiate pink (full) vs yellow (partial) label styling

**Label Layout (per sticker):**
```
┌─────────────────────────────┐
│  ┌─────────┐                │
│  │         │  LOCAP2        │
│  │  [QR]   │  Black         │
│  │         │  Qty: 500      │
│  └─────────┘  2026-02-11    │
│                              │
│  RJ-LOCAP2-BLK-20260211-001 │
└─────────────────────────────┘
```

### 4.3 stock_service.py

Core business logic for stock operations.

**Responsibilities:**
- **Scan In:** Validate barcode, create/update stock_item, record stock_movement
- **Scan Out:** Validate barcode, check status is `in_stock`, update to `picked`, record movement, optionally link to order
- **Partial Repack:** Mark original carton as `consumed`, create new partial stock_item with new barcode, record movements for both
- **Adjustment:** Record manual adjustment (damage, scrap) with mandatory reason
- **Stock Levels:** Calculate current stock per product+colour by aggregating `in_stock` items
- **Threshold Check:** Compare stock levels against thresholds, return colour status (green/amber/red)
- **Stock Summary:** Aggregate view — total units, total cartons, by product/colour

### 4.4 stocktake_service.py

Manages quarterly stocktake verification sessions.

**Responsibilities:**
- **Start Session:** Create session, snapshot expected stock (all `in_stock` items)
- **Process Scan:** Record each scan, classify result (found, not in system, already scanned, wrong status)
- **Live Progress:** Return scanned vs expected counts during session
- **Complete Session:** Calculate discrepancies, generate report, optionally auto-adjust stock
- **Discrepancy Report:** List items expected but not scanned, and items scanned but not expected

### 4.5 raw_material_service.py

Raw material inventory management.

**Responsibilities:**
- **Receive Delivery:** Record incoming raw material with quantity, supplier, delivery note, unit cost
- **Record Usage:** Record material consumed (manual entry — no WO integration in this phase)
- **Adjustment:** Manual stock adjustment with reason
- **Stock Level:** Current stock derived from movements (cached in `current_stock` field)
- **Threshold Check:** Colour-coded levels same as finished goods

### 4.6 report_service.py

Report generation and export.

**Responsibilities:**
- **Stock Valuation:** Current stock × unit price, grouped by product/colour
- **Movement History:** Filterable log of all movements (date range, product, type)
- **Point-in-Time Stock:** Stock on hand as of a specified date (replay movements)
- **Spreadsheet Export:** All reports exportable as .xlsx via openpyxl
- **Stocktake Report:** Summary + detail of completed stocktake sessions

### 4.7 API Endpoints

#### Stock Router (`api/stock.py`, prefix: `/api/stock`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List stock items (filter by product, colour, status) |
| `GET` | `/summary` | Aggregated stock levels per product+colour with thresholds |
| `GET` | `/{stock_item_id}` | Get stock item detail + movement history |
| `POST` | `/scan-in` | Process a stock-in scan event |
| `POST` | `/scan-out` | Process a stock-out scan event |
| `POST` | `/scan` | Generic scan endpoint (auto-detects context based on mode) |
| `POST` | `/partial-repack` | Handle partial box scenario |
| `POST` | `/adjustment` | Manual stock adjustment |
| `GET` | `/labels/generate` | Generate QR labels for a batch (returns PDF) |
| `GET` | `/thresholds` | List all stock thresholds |
| `PUT` | `/thresholds/{id}` | Update a stock threshold |
| `POST` | `/thresholds` | Create a stock threshold |

#### Products Router (`api/products.py` — MODIFY existing, prefix: `/api/products`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List products (existing — add search params) |
| `GET` | `/{product_code}` | Get product detail (existing) |
| `POST` | `/` | **NEW:** Create product |
| `PUT` | `/{product_code}` | **NEW:** Update product |
| `DELETE` | `/{product_code}` | **NEW:** Delete product (soft delete via is_active) |

#### Raw Materials Router (`api/raw_materials.py`, prefix: `/api/raw-materials`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List raw materials (filter by type, search) |
| `GET` | `/{id}` | Get raw material detail + movement history |
| `POST` | `/` | Create raw material |
| `PUT` | `/{id}` | Update raw material |
| `DELETE` | `/{id}` | Soft delete raw material |
| `POST` | `/{id}/receive` | Record delivery received |
| `POST` | `/{id}/use` | Record material used |
| `POST` | `/{id}/adjustment` | Manual adjustment |

#### Stocktake Router (`api/stocktake.py`, prefix: `/api/stocktake`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sessions` | List stocktake sessions |
| `GET` | `/sessions/{id}` | Session detail + progress |
| `POST` | `/sessions` | Start new stocktake session |
| `POST` | `/sessions/{id}/scan` | Record a scan during stocktake |
| `POST` | `/sessions/{id}/complete` | Complete session + generate discrepancy report |
| `POST` | `/sessions/{id}/cancel` | Cancel session |
| `GET` | `/sessions/{id}/discrepancies` | Get discrepancy report |

#### Reports Router (`api/reports.py`, prefix: `/api/reports`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stock-valuation` | Current stock valuation report |
| `GET` | `/movement-history` | Movement history (filterable) |
| `GET` | `/stock-on-hand` | Point-in-time stock on hand |
| `GET` | `/stocktake/{session_id}` | Stocktake session report |
| `GET` | `/export/{report_type}` | Download report as .xlsx |

---

## 5. Frontend Pages

All pages follow existing patterns: file-based TanStack Router routes, shadcn/ui components, TanStack React Query, Tailwind CSS. All pages must be **tablet-friendly** (large touch targets, readable fonts, responsive layout).

### 5.1 New Files

```
frontend/src/
├── routes/
│   ├── stock/
│   │   ├── index.tsx                   ← Stock dashboard (levels, search, thresholds)
│   │   ├── scan.tsx                    ← Scanning interface (Stock In / Out / Stocktake)
│   │   ├── labels.tsx                  ← Label generation and printing
│   │   ├── $stockItemId.tsx            ← Individual carton detail + history
│   │   └── stocktake/
│   │       ├── index.tsx               ← Stocktake session list
│   │       └── $sessionId.tsx          ← Active stocktake session
│   ├── raw-materials/
│   │   ├── index.tsx                   ← Raw materials list + CRUD
│   │   └── $materialId.tsx             ← Raw material detail + movements
│   ├── products/
│   │   └── index.tsx                   ← Product management (CRUD — enhance existing)
│   └── reports/
│       └── index.tsx                   ← Reports dashboard + export
├── components/
│   ├── stock/
│   │   ├── StockLevelCard.tsx          ← Colour-coded stock level per product
│   │   ├── StockTable.tsx              ← Searchable/filterable stock table
│   │   ├── ScanInput.tsx               ← Auto-focused scanner input with feedback
│   │   ├── ScanResult.tsx              ← Success/error display after scan
│   │   ├── MovementHistory.tsx         ← Timeline of movements for an item
│   │   ├── ThresholdEditor.tsx         ← Inline threshold configuration
│   │   ├── LabelPreview.tsx            ← Preview generated labels before printing
│   │   ├── StocktakeProgress.tsx       ← Live progress during stocktake
│   │   └── DiscrepancyTable.tsx        ← Stocktake discrepancy results
│   ├── raw-materials/
│   │   ├── RawMaterialTable.tsx        ← Raw material list with levels
│   │   ├── ReceiveForm.tsx             ← Receive delivery form
│   │   └── UsageForm.tsx               ← Record usage form
│   └── reports/
│       └── ReportCard.tsx              ← Report type selector card
├── services/
│   ├── stockService.ts                 ← Stock API calls
│   ├── rawMaterialService.ts           ← Raw material API calls
│   ├── stocktakeService.ts             ← Stocktake API calls
│   └── reportService.ts               ← Report API calls
├── hooks/
│   ├── useStock.ts                     ← React Query hooks for stock
│   ├── useRawMaterials.ts              ← React Query hooks for raw materials
│   ├── useStocktake.ts                 ← React Query hooks for stocktakes
│   └── useReports.ts                   ← React Query hooks for reports
└── types/
    ├── stock.ts                        ← Stock TypeScript interfaces
    └── rawMaterials.ts                 ← Raw material TypeScript interfaces
```

### 5.2 Stock Dashboard (`/stock`)

Main stock overview page. Tablet-optimised.

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  [🔍 Search products...]            [Scan] [Labels]       │
│                                                           │
│  Summary Cards:                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │ Total SKUs │ │ Total Units│ │ Low Stock  │            │
│  │    42      │ │  156,000   │ │  ●● 5      │            │
│  └────────────┘ └────────────┘ └────────────┘            │
│                                                           │
│  Stock Levels:                     [Filter ▾] [Export]    │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Product    │ Colour │ Cartons │ Units  │ Status    │   │
│  │ LOCAP2     │ Black  │ 12      │ 6,000  │ ● Green   │   │
│  │ LOCAP2     │ White  │ 3       │ 1,500  │ ● Amber   │   │
│  │ GLCAPRB    │ Black  │ 0       │ 0      │ ● Red     │   │
│  │ PY0063-1A  │ Yellow │ 25      │ 12,500 │ ● Green   │   │
│  └────────────────────────────────────────────────────┘   │
│  Click row → drill down to carton list                    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Scanning Page (`/stock/scan`)

Primary scanning interface. Designed for tablet use with the Bluetooth scanner.

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Scan Mode:                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │ STOCK IN │ │ STOCK OUT│ │STOCKTAKE │                  │
│  │ (active) │ │          │ │          │                  │
│  └──────────┘ └──────────┘ └──────────┘                  │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │                                                    │     │
│  │  [  Scan barcode or enter manually...          ]  │     │
│  │                                                    │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Last Scan Result:                                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │  ✓ SCANNED IN                                      │     │
│  │  LOCAP2 — Louvre End Cap 152mm                     │     │
│  │  Black — 500 units — Full box                      │     │
│  │  RJ-LOCAP2-BLK-20260211-001                        │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Session Summary:                                         │
│  Scanned this session: 15 cartons (7,500 units)           │
│                                                           │
│  Recent Scans:                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 10:45  RJ-LOCAP2-BLK-20260211-001  ✓ In         │     │
│  │ 10:44  RJ-LOCAP2-BLK-20260211-002  ✓ In         │     │
│  │ 10:43  RJ-GLCAPRB-BLK-20260210-005 ✗ Not found  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Behaviour:**
- Large touch-friendly mode selector buttons
- Input field auto-focuses on page load and after each scan
- Audio beep on successful scan, error tone on failure
- For **Stock Out** mode: if linked to an order, show a pick list of expected items
- For **Partial box** on Stock Out: prompt for remaining quantity, generate yellow label

### 5.4 Label Generation Page (`/stock/labels`)

Generate and print QR code labels.

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│                                                           │
│  Generate Labels                                          │
│                                                           │
│  Product:  [LOCAP2 - Louvre End Cap 152mm     ▾]         │
│  Colour:   [Black                              ▾]         │
│  Quantity per carton: [500                      ]         │
│  Number of labels:    [20                       ]         │
│  Box type: (●) Full  ( ) Partial                          │
│                                                           │
│  [Generate Preview]                                       │
│                                                           │
│  Preview:                                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                    │
│  │ [QR] │ │ [QR] │ │ [QR] │ │ [QR] │                    │
│  │ L... │ │ L... │ │ L... │ │ L... │                    │
│  └──────┘ └──────┘ └──────┘ └──────┘                    │
│                                                           │
│  [Print Labels (PDF)]                                     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5.5 Product Management (`/products`)

Enhanced from current read-only product listing to full CRUD.

- Search and filter products
- Add new product (with manufacturing specs, material specs, packaging specs, pricing)
- Edit existing product
- Soft delete (set `is_active = false`)
- Configure stock thresholds per product+colour
- View current stock level for each product

### 5.6 Raw Materials (`/raw-materials`)

Raw material inventory management.

- List all raw materials with current stock and colour-coded levels
- Add/edit/delete raw materials
- Receive delivery (quantity, supplier, delivery note, unit cost)
- Record usage (quantity, reason)
- Manual adjustment (quantity, reason)
- Movement history per material

### 5.7 Reports (`/reports`)

Report generation and export dashboard.

- **Stock Valuation** — current stock × pricing, grouped by product
- **Movement History** — filterable date range, product, movement type
- **Stock on Hand** — select a date, see what stock existed at that point
- **Stocktake Reports** — summary of completed stocktake sessions
- **Export** — all reports downloadable as .xlsx

### 5.8 Navigation

Add to existing header navigation:
- **Stock** → `/stock` (dashboard)
- **Products** → `/products` (CRUD management)
- **Raw Materials** → `/raw-materials`
- **Reports** → `/reports`

Scanning and label pages accessible from the stock dashboard via action buttons.

---

## 6. Stock Lifecycle Flows

### 6.1 Production Complete → Stock In

```
1. Production run finishes, cartons are boxed
2. Warehouse staff opens /stock/labels on tablet
3. Selects product, colour, qty per carton, number of cartons
4. Generates and prints QR labels (PDF → printer)
5. Sticks pink labels on full cartons, yellow on any partial cartons
6. Opens /stock/scan, selects "Stock In" mode
7. Scans each carton — system creates stock_item + stock_movement
8. Dashboard updates in real-time
```

### 6.2 Order Fulfilment → Stock Out

```
1. Sharon approves an order in the existing order system
2. Order appears on the stock scanning page as a "pick list" (optional enhancement)
3. Warehouse staff opens /stock/scan, selects "Stock Out" mode
4. Optionally selects the order being fulfilled
5. Scans each carton being picked — system updates stock_item status + records movement
6. If a partial carton is needed:
   a. Scan the full carton (stock out)
   b. System prompts: "Partial box — how many units remaining?"
   c. Enter remaining quantity
   d. System generates a new yellow-label QR code for the partial box
   e. Staff prints the yellow label and sticks it on the remaining box
   f. Staff scans the new partial box in (stock in)
```

### 6.3 Manual Adjustment

```
1. Staff finds a damaged/expired carton
2. Opens /stock/scan or /stock/{itemId}
3. Records adjustment: quantity change + mandatory reason
4. Stock item status updated to 'scrapped'
5. Movement recorded in ledger
```

### 6.4 Quarterly Stocktake

```
1. Manager starts a new stocktake session at /stock/stocktake
2. System snapshots all expected in_stock items
3. Warehouse staff walk the warehouse with tablets
4. Scan every carton they find
5. System tracks: found (expected), not found (missing), unexpected (not in system)
6. Live progress bar shows scanned vs expected
7. When complete, manager reviews discrepancy report
8. Approve adjustments to reconcile system with reality
```

---

## 7. Build Phases

Each phase is independently buildable and testable.

### Phase 1: Database Model & Product CRUD
**Scope:** Add stock tables, enhance products with full CRUD.

- Add SQLAlchemy models: `StockItem`, `StockMovement`, `StockThreshold`, `StocktakeSession`, `StocktakeScan`, `RawMaterial`, `RawMaterialMovement`
- Add `is_stockable` field to existing `Product` model
- Create Alembic migration
- Enhance `api/products.py` with CREATE, UPDATE, DELETE endpoints
- Add Pydantic schemas for stock and product CRUD
- Test: product CRUD operations, migration runs cleanly

**Dependencies:** None
**Estimated effort:** Small-Medium

### Phase 2: QR Code Generation & Label Printing
**Scope:** Generate unique QR codes, render printable label PDFs.

- Create `services/barcode_service.py` — QR generation, unique ID sequencing, label PDF rendering
- Create `api/stock.py` (label endpoints only) — `/api/stock/labels/generate`
- Frontend: `/stock/labels` route — label generation form, preview, print
- Test: generate labels, verify QR codes scan correctly with Zebra DS22

**Dependencies:** Phase 1
**Estimated effort:** Medium

### Phase 3: Stock-In Scanning (Production → Warehouse)
**Scope:** Scan cartons into stock after production.

- Create `services/stock_service.py` — scan-in logic, stock item creation, movement recording
- Add scan-in endpoints to `api/stock.py`
- Frontend: `/stock/scan` route — scanning interface with "Stock In" mode
- Scanner HID integration (auto-focus input, enter-key submission)
- Audio feedback (success/error tones)
- Session summary (cartons scanned this session)
- Test: scan in multiple cartons, verify stock levels update

**Dependencies:** Phase 2
**Estimated effort:** Medium

### Phase 4: Stock-Out Scanning & Partial Boxes (Order Fulfilment)
**Scope:** Scan cartons out when fulfilling orders. Handle partial boxes.

- Add scan-out logic to `stock_service.py` — status transition, order linking
- Add partial repack logic — consume original, create partial with new barcode
- Add scan-out and partial-repack endpoints to `api/stock.py`
- Frontend: "Stock Out" mode on scan page, partial box flow (quantity prompt + auto-label)
- Integration with existing orders — optionally link scan-out to an approved order
- Test: scan out cartons, partial box workflow, verify stock levels and movements

**Dependencies:** Phase 3
**Estimated effort:** Medium-Large

### Phase 5: Stock Dashboard, Search & Thresholds
**Scope:** Build the stock dashboard with live levels, search, and threshold configuration.

- Stock summary endpoint — aggregated levels per product+colour
- Threshold CRUD endpoints
- Frontend: `/stock` dashboard — summary cards, colour-coded stock table, search/filter
- Frontend: `/stock/{stockItemId}` — individual carton detail + movement timeline
- Threshold editor — inline configuration of red/amber levels per product
- Export stock levels as spreadsheet
- Test: verify colour coding, search, drill-down, export

**Dependencies:** Phase 3 (needs stock data to display)
**Estimated effort:** Medium-Large

### Phase 6: Stocktake Verification
**Scope:** Quarterly stocktake session management.

- Create `services/stocktake_service.py` — session management, discrepancy calculation
- Create `api/stocktake.py` — session CRUD, scan recording, completion
- Add Pydantic schemas for stocktake
- Frontend: `/stock/stocktake` — session list, start new session
- Frontend: `/stock/stocktake/{sessionId}` — live scanning with progress bar, discrepancy display
- Auto-adjustment option on completion
- Test: run a full stocktake session, verify discrepancy detection

**Dependencies:** Phase 5
**Estimated effort:** Medium

### Phase 7: Raw Materials Inventory
**Scope:** Track raw material stock levels.

- Create `services/raw_material_service.py` — receive, use, adjust, levels
- Create `api/raw_materials.py` — full CRUD + movement endpoints
- Add Pydantic schemas for raw materials
- Frontend: `/raw-materials` — list with colour-coded levels, CRUD, receive/use forms
- Frontend: `/raw-materials/{materialId}` — detail + movement history
- Test: receive delivery, record usage, verify levels and thresholds

**Dependencies:** Phase 1
**Estimated effort:** Medium

### Phase 8: Reports & Export
**Scope:** Report generation and spreadsheet export.

- Create `services/report_service.py` — valuation, movement history, point-in-time, stocktake reports
- Create `api/reports.py` — report endpoints + export
- Frontend: `/reports` — report type selector, date range pickers, preview, download
- Spreadsheet export via openpyxl
- Test: generate each report type, verify export downloads correctly

**Dependencies:** Phase 5 + Phase 7
**Estimated effort:** Medium

---

## 8. Configuration

New environment variables to add to `.env`:

```bash
# Stock Tracking
LABEL_COMPANY_NAME=RAMJET PLASTICS     # Printed on labels
LABEL_PAGE_SIZE=A4                      # Label sheet size
LABELS_PER_PAGE=10                      # Labels per printed page

# QR Code
QR_CODE_PREFIX=RJ                       # Prefix for all barcode IDs
QR_CODE_ERROR_CORRECTION=M             # L, M, Q, H (Medium recommended)
```

---

## 9. Open Questions

1. **Label sticker sheets** — What specific sticker sheet size/layout will be used? (e.g., Avery L7160, 21 labels per A4). This determines PDF label layout.
2. **Colour short codes** — Should colour abbreviations be configurable (e.g., Black→BLK, White→WHT) or auto-generated?
3. **Stock Out + Orders** — Should stock-out be mandatory before an order can be marked as dispatched? Or is it optional/independent?
4. **Raw material categories** — What types of raw materials need tracking? (Resin, masterbatch, additives — anything else?)
5. **Multi-user scanning** — Can multiple warehouse staff scan simultaneously on different tablets during the same stocktake?
6. **Report format** — Any specific spreadsheet format/layout for exports, or is a clean data dump sufficient for now?

---

## 10. Success Criteria

**For the demo to Grant:**
- Production run completes → warehouse staff generates and prints QR labels on a tablet
- Staff sticks labels on cartons and scans them in — stock levels update live
- Sharon checks the stock dashboard and sees current levels colour-coded
- An order is approved → warehouse staff scans cartons out
- Partial box handled correctly with new yellow label
- Stock dashboard reflects the change immediately
- Quarterly stocktake: walk warehouse, scan everything, review discrepancies
- Raw materials received and tracked with levels visible
- Reports generated and exported as spreadsheets
- All scanning done via cheap tablets with Bluetooth Zebra scanner over WiFi

---

*This document is the single source of truth for the Stock Tracking feature. Each build phase should reference this document. Future agents should read this before planning any implementation work.*
