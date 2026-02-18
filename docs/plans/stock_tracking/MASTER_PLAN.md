# Stock Tracking System - Master Plan

## 1. Executive Summary

A real-time stock tracking system for Ramjet Plastics. Uses QR-code-labelled cartons scanned via Bluetooth barcode scanners to maintain a live inventory ledger of finished goods and raw materials. Stock levels feed directly into the order process — determining how much to produce rather than just tracking what's shipped.

### Current State
- Warehouse staff print order forms and physically walk the factory to count stock
- No regular stocktake cadence — counts happen ad-hoc before production runs
- Stock counts are slow, error-prone, and give no visibility between counts
- Re-tooling injection moulding machines is extremely expensive, so knowing exact stock on hand before generating works orders is critical
- No role separation — all users see the same interface

### Target State
- Every carton gets a unique QR code label; scanning in/out maintains a live ledger
- Real-time stock levels visible on dashboard — no manual counting required
- When an order is created, warehouse verifies existing stock in parallel with Sharon's approval
- Works orders only generate after both approval and stock verification, with verified stock deducted from the production quantity
- Two-tier user roles: Warehouse (simplified tablet UI) and Admin (full access)
- Quarterly stocktakes become verification exercises, not the primary count
- Raw materials tracked by receiving deliveries in and recording usage out

---

## 2. Architecture Overview

### 2.1 System Flow

```
PRODUCTION LINE
│
▼
┌──────────────────────────────────────────────────────────────┐
│ END OF PRODUCTION RUN                                        │
│                                                              │
│  1. Generate QR labels (unique per carton)                   │
│     - Pink label = full carton                               │
│     - Yellow label = part-filled carton                      │
│  2. Print labels on regular printer                          │
│  3. Stick labels on cartons                                  │
│  4. Scan each carton → STOCK IN                              │
│                                                              │
│  Tablet + Bluetooth Zebra DS22 scanner                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND (Mac Mini M4)                                │
│                                                              │
│  - Receives scan events via REST API                         │
│  - Updates stock ledger (movement records)                   │
│  - Calculates live stock levels                              │
│  - Generates QR codes and printable labels                   │
│  - Auto-creates stock verification tasks on new orders       │
│  - Manages raw material inventory                            │
│  - Produces reports and exports                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ REACT FRONTEND (Tablets + Desktop via WiFi)                  │
│                                                              │
│  WAREHOUSE ROLE (tablet-optimised):                          │
│  - Scan page (home) — Stock In / Stock Out                   │
│  - Label generation                                          │
│  - Read-only stock lookup                                    │
│  - Stock verification tasks                                  │
│                                                              │
│  ADMIN ROLE (full access):                                   │
│  - Everything warehouse sees, plus:                          │
│  - Stock dashboard with thresholds                           │
│  - Product management (CRUD)                                 │
│  - Raw materials management                                  │
│  - Stocktake sessions                                        │
│  - Reports and export                                        │
│  - Order review and approval                                 │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Order Integration Flow (Critical)

This is the key architectural change from the old build pack. Stock levels are an **input** to works order generation, not just a record of what shipped.

```
ORDER CREATED (status: "pending")
│
├──────────────────────────────────┐
│                                  │
▼                                  ▼
┌─────────────────────┐   ┌─────────────────────────┐
│  SHARON REVIEWS     │   │  WAREHOUSE VERIFIES     │
│  (existing flow)    │   │  STOCK (new)             │
│                     │   │                          │
│  Approves or        │   │  For each line item with │
│  rejects order      │   │  matching stock:         │
│                     │   │  - Confirm quantity       │
│                     │   │  - Or adjust: "only 15"  │
└────────┬────────────┘   └────────┬──────────────────┘
         │                         │
         ▼                         ▼
    ┌──────────────────────────────────┐
    │  BOTH COMPLETE?                   │
    │                                   │
    │  Sharon approved: YES             │
    │  Stock verified:  YES             │
    │                                   │
    │  → Generate works orders          │
    │  → WO qty = ordered - verified    │
    │  → If verified >= ordered,        │
    │    no works order needed          │
    └──────────────────────────────────┘
```

### 2.3 Infrastructure

| Component | Details |
|-----------|---------|
| **Server** | Mac Mini M4 running Docker (backend + frontend + PostgreSQL) |
| **Tablets** | Cheap Android/iPad tablets, connected via WiFi to Mac Mini's IP |
| **Scanner** | Zebra DS22 series, Bluetooth paired to tablet, HID keyboard mode |
| **Labels** | Printed on regular printer (A4 sheets of sticker labels) |
| **Network** | All devices on same WiFi. App accessed via Mac Mini's local IP (e.g., `http://192.168.1.x:5179`) |

### 2.4 Scanner Integration

The Zebra DS22 in Bluetooth HID mode acts as a wireless keyboard. When a QR code is scanned, the scanner "types" the QR content into the focused text field, followed by an Enter keystroke.

**Web app behaviour:**
1. Scanning page has an auto-focused text input
2. Scanner sends QR content as keystrokes → input field fills
3. Enter key triggers form submission
4. Backend processes the scan event
5. UI shows result (success/error) with visual and audio feedback
6. Input field auto-clears and re-focuses for next scan

No native app required. No special drivers. Pure web.

### 2.5 Tech Stack (Existing)

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | React 18 + TypeScript | Existing app |
| **Routing** | TanStack Router (file-based) | Add new routes |
| **UI** | shadcn/ui + Tailwind CSS | Existing components + new ones |
| **Data** | TanStack React Query | For API data fetching |
| **Backend** | FastAPI + Python 3.11 | Existing app |
| **Database** | PostgreSQL + SQLAlchemy | Existing, add new tables |
| **Migrations** | Alembic | Existing setup |
| **Auth** | Simple auth (dev) / Ory Kratos (prod) | Extend with "warehouse" role |
| **Containers** | Docker Compose | Existing orchestration |

### 2.6 New Dependencies

**Backend (add to requirements.txt):**
```
qrcode[pil]>=7.4          # QR code generation
Pillow>=10.0               # Image processing for label rendering
reportlab>=4.0             # PDF generation for printable labels
openpyxl>=3.1.0            # Spreadsheet export (already installed)
```

**Frontend:**
```
(none expected — standard web APIs + existing libraries sufficient)
```

---

## 3. Role System

### 3.1 User Roles

Extend the existing `User.role` field (currently `"inspector"`, `"admin"`, `"viewer"`) to include `"warehouse"`.

| Role | Description | Access |
|------|-------------|--------|
| **admin** | Full access — Sharon, Grant, Brett | Everything: orders, stock, products, raw materials, reports, stocktake, user management |
| **warehouse** | Simplified tablet UI — warehouse staff | Scan page (home), label generation, read-only stock lookup, stock verification tasks |
| **inspector** | Existing role — kept for backwards compatibility | Order review (existing functionality) |
| **viewer** | Existing role — read-only access | Read-only views |

### 3.2 Backend Role Guards

The existing `require_role()` dependency in `backend/app/core/auth.py` already supports this pattern:

```python
# Existing implementation — admin always has access
def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(status_code=403, ...)
        return current_user
    return role_checker
```

Usage on new endpoints:
```python
# Warehouse + Admin can access
@router.post("/scan-in", dependencies=[Depends(require_role("warehouse"))])

# Admin only
@router.post("/thresholds", dependencies=[Depends(require_role("admin"))])
```

### 3.3 Frontend Role-Based Navigation

**Current state:** Header nav has a single "Orders" link (see `frontend/src/components/Layout/Header.tsx`).

**Target state:** Role-conditional nav rendering.

| Nav Item | Warehouse | Admin |
|----------|-----------|-------|
| Scan (home for warehouse) | Yes | Yes |
| Labels | Yes | Yes |
| Stock Lookup | Yes (read-only) | Yes (full dashboard) |
| Verification Tasks | Yes | Yes |
| Orders | No | Yes |
| Products | No | Yes |
| Raw Materials | No | Yes |
| Stocktake | No | Yes |
| Reports | No | Yes |

The `user.role` is already available via `SimpleAuthContext` / `useUnifiedAuth()`.

---

## 4. Data Model

### 4.1 New PostgreSQL Tables

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

#### stock_verifications

Links orders to warehouse stock confirmation. Created automatically when an order is created.

```
stock_verifications
├── id                      UUID (PK, auto)
├── order_id                UUID FK → orders.id NOT NULL
├── order_line_item_id      UUID FK → order_line_items.id NOT NULL
├── product_code            VARCHAR(50) FK → products.product_code NOT NULL
├── colour                  VARCHAR(100) NOT NULL
├── system_stock_quantity   INTEGER NOT NULL              -- stock level at time of order creation
├── verified_quantity       INTEGER NULL                  -- warehouse-confirmed quantity (NULL = not yet verified)
├── status                  VARCHAR(20) NOT NULL DEFAULT 'pending'
│                           -- pending | confirmed | expired
├── verified_by             UUID FK → users.id NULL
├── verified_at             TIMESTAMPTZ NULL
├── notes                   TEXT NULL
├── created_at              TIMESTAMPTZ
└── updated_at              TIMESTAMPTZ
```

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

Raw material master data.

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

### 4.2 Indexes

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

-- Stock verifications
CREATE INDEX idx_stock_verifications_order ON stock_verifications(order_id);
CREATE INDEX idx_stock_verifications_status ON stock_verifications(status);
CREATE INDEX idx_stock_verifications_line_item ON stock_verifications(order_line_item_id);

-- Stocktake
CREATE INDEX idx_stocktake_scans_session ON stocktake_scans(session_id);
CREATE INDEX idx_stocktake_scans_barcode ON stocktake_scans(barcode_scanned);

-- Raw materials
CREATE INDEX idx_raw_materials_code ON raw_materials(material_code);
CREATE INDEX idx_raw_materials_type ON raw_materials(material_type);
CREATE INDEX idx_raw_material_movements_material ON raw_material_movements(raw_material_id);
CREATE INDEX idx_raw_material_movements_date ON raw_material_movements(created_at);
```

### 4.3 Modifications to Existing Tables

**products** — Add `is_stockable` field:
```
├── is_stockable            BOOLEAN DEFAULT TRUE           -- whether this product is tracked in stock
```

**orders** — Extend status values:
```
status: pending | approved | rejected | error | verified | works_order_generated
```

The `approved` status now means "Sharon approved" but works order generation waits for stock verification too. New statuses:
- `verified` — both Sharon approved AND stock verified
- `works_order_generated` — works orders have been created with adjusted quantities

---

## 5. Backend Modules

### 5.1 New Files

```
backend/app/
├── api/
│   ├── stock.py                        ← NEW: Stock CRUD, scan events, movements
│   ├── stock_verification.py           ← NEW: Verification task endpoints
│   ├── raw_materials.py                ← NEW: Raw material CRUD + movements
│   ├── stocktake.py                    ← NEW: Stocktake session management
│   ├── reports.py                      ← NEW: Stock reports + export
│   └── products.py                     ← MODIFY: Add full CRUD (currently read-only)
├── services/
│   ├── stock_service.py                ← NEW: Core stock logic (scan in/out, levels, thresholds)
│   ├── barcode_service.py              ← NEW: QR code generation + label rendering
│   ├── stock_verification_service.py   ← NEW: Verification task creation + confirmation
│   ├── raw_material_service.py         ← NEW: Raw material inventory logic
│   ├── stocktake_service.py            ← NEW: Stocktake session + discrepancy logic
│   ├── report_service.py               ← NEW: Report generation + spreadsheet export
│   └── form_generation_service.py      ← MODIFY: Deduct verified stock from WO quantity
├── schemas/
│   ├── stock_schemas.py                ← NEW: Pydantic models for stock
│   ├── stock_verification_schemas.py   ← NEW: Pydantic models for verification
│   ├── raw_material_schemas.py         ← NEW: Pydantic models for raw materials
│   ├── stocktake_schemas.py            ← NEW: Pydantic models for stocktakes
│   └── report_schemas.py               ← NEW: Pydantic models for reports
├── core/
│   └── models.py                       ← MODIFY: Add all new table models
└── main.py                             ← MODIFY: Register new routers
```

### 5.2 API Endpoints

#### Stock Router (`api/stock.py`, prefix: `/api/stock`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | warehouse, admin | List stock items (filter by product, colour, status) |
| `GET` | `/summary` | warehouse (read-only), admin | Aggregated stock levels per product+colour with thresholds |
| `GET` | `/{stock_item_id}` | warehouse, admin | Stock item detail + movement history |
| `POST` | `/scan-in` | warehouse, admin | Process a stock-in scan event |
| `POST` | `/scan-out` | warehouse, admin | Process a stock-out scan event |
| `POST` | `/partial-repack` | warehouse, admin | Handle partial box scenario |
| `POST` | `/adjustment` | admin | Manual stock adjustment |
| `GET` | `/labels/generate` | warehouse, admin | Generate QR labels for a batch (returns PDF) |
| `GET` | `/thresholds` | admin | List all stock thresholds |
| `PUT` | `/thresholds/{id}` | admin | Update a stock threshold |
| `POST` | `/thresholds` | admin | Create a stock threshold |

#### Stock Verification Router (`api/stock_verification.py`, prefix: `/api/stock-verifications`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/pending` | warehouse, admin | List pending verification tasks |
| `GET` | `/order/{order_id}` | warehouse, admin | Get verification tasks for an order |
| `POST` | `/{id}/confirm` | warehouse, admin | Confirm/adjust verified quantity |
| `POST` | `/{id}/expire` | admin | Expire a verification (stock changed) |

#### Products Router (`api/products.py` — MODIFY existing, prefix: `/api/products`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | any authenticated | List products (existing — add search params) |
| `GET` | `/{product_code}` | any authenticated | Get product detail (existing) |
| `POST` | `/` | admin | **NEW:** Create product |
| `PUT` | `/{product_code}` | admin | **NEW:** Update product |
| `DELETE` | `/{product_code}` | admin | **NEW:** Soft delete (is_active=false) |

#### Raw Materials Router (`api/raw_materials.py`, prefix: `/api/raw-materials`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | admin | List raw materials (filter by type, search) |
| `GET` | `/{id}` | admin | Raw material detail + movement history |
| `POST` | `/` | admin | Create raw material |
| `PUT` | `/{id}` | admin | Update raw material |
| `DELETE` | `/{id}` | admin | Soft delete |
| `POST` | `/{id}/receive` | admin | Record delivery received |
| `POST` | `/{id}/use` | admin | Record material used |
| `POST` | `/{id}/adjustment` | admin | Manual adjustment |

#### Stocktake Router (`api/stocktake.py`, prefix: `/api/stocktake`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sessions` | admin | List stocktake sessions |
| `GET` | `/sessions/{id}` | admin | Session detail + progress |
| `POST` | `/sessions` | admin | Start new stocktake session |
| `POST` | `/sessions/{id}/scan` | warehouse, admin | Record a scan during stocktake |
| `POST` | `/sessions/{id}/complete` | admin | Complete session + generate discrepancy report |
| `POST` | `/sessions/{id}/cancel` | admin | Cancel session |
| `GET` | `/sessions/{id}/discrepancies` | admin | Get discrepancy report |

#### Reports Router (`api/reports.py`, prefix: `/api/reports`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/stock-valuation` | admin | Current stock valuation report |
| `GET` | `/movement-history` | admin | Movement history (filterable) |
| `GET` | `/stock-on-hand` | admin | Point-in-time stock on hand |
| `GET` | `/stocktake/{session_id}` | admin | Stocktake session report |
| `GET` | `/export/{report_type}` | admin | Download report as .xlsx |

---

## 6. Frontend Pages

All pages follow existing patterns: file-based TanStack Router routes, shadcn/ui components, TanStack React Query, Tailwind CSS. All pages must be **tablet-friendly** (large touch targets, readable fonts, responsive layout).

### 6.1 New Files

```
frontend/src/
├── routes/
│   ├── stock/
│   │   ├── index.tsx                   ← Stock dashboard (admin) / Stock lookup (warehouse)
│   │   ├── scan.tsx                    ← Scanning interface (Stock In / Out)
│   │   ├── labels.tsx                  ← Label generation and printing
│   │   ├── $stockItemId.tsx            ← Individual carton detail + history
│   │   ├── verification.tsx            ← Stock verification tasks (warehouse + admin)
│   │   └── stocktake/
│   │       ├── index.tsx               ← Stocktake session list (admin only)
│   │       └── $sessionId.tsx          ← Active stocktake session
│   ├── raw-materials/
│   │   ├── index.tsx                   ← Raw materials list + CRUD (admin only)
│   │   └── $materialId.tsx             ← Raw material detail + movements
│   ├── products/
│   │   └── index.tsx                   ← Product management (CRUD — admin only)
│   └── reports/
│       └── index.tsx                   ← Reports dashboard + export (admin only)
├── components/
│   ├── stock/
│   │   ├── StockLevelCard.tsx          ← Colour-coded stock level per product
│   │   ├── StockTable.tsx              ← Searchable/filterable stock table
│   │   ├── ScanInput.tsx               ← Auto-focused scanner input with feedback
│   │   ├── ScanResult.tsx              ← Success/error display after scan
│   │   ├── MovementHistory.tsx         ← Timeline of movements for an item
│   │   ├── ThresholdEditor.tsx         ← Inline threshold configuration
│   │   ├── LabelPreview.tsx            ← Preview generated labels before printing
│   │   ├── VerificationTaskCard.tsx    ← Pending verification task display
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
│   ├── stockVerificationService.ts     ← Verification API calls
│   ├── rawMaterialService.ts           ← Raw material API calls
│   ├── stocktakeService.ts             ← Stocktake API calls
│   └── reportService.ts               ← Report API calls
├── hooks/
│   ├── useStock.ts                     ← React Query hooks for stock
│   ├── useStockVerification.ts         ← React Query hooks for verifications
│   ├── useRawMaterials.ts              ← React Query hooks for raw materials
│   ├── useStocktake.ts                 ← React Query hooks for stocktakes
│   └── useReports.ts                   ← React Query hooks for reports
└── types/
    ├── stock.ts                        ← Stock TypeScript interfaces
    └── rawMaterials.ts                 ← Raw material TypeScript interfaces
```

### 6.2 Role-Based Navigation

The Header component (`frontend/src/components/Layout/Header.tsx`) currently renders a single "Orders" nav link. This must be extended to render navigation conditionally based on `user.role`:

**Warehouse user sees:**
- Scan (home page — `/stock/scan`)
- Labels (`/stock/labels`)
- Stock (`/stock` — read-only lookup)
- Tasks (`/stock/verification`)

**Admin user sees:**
- Orders (`/orders`)
- Stock (`/stock` — full dashboard)
- Products (`/products`)
- Raw Materials (`/raw-materials`)
- Reports (`/reports`)

---

## 7. Stock Lifecycle Flows

### 7.1 Production Complete → Stock In

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

### 7.2 Order Created → Parallel Verification

```
1. Email arrives, AI extracts order data (existing flow)
2. Order created with status "pending"
3. System auto-creates StockVerification records:
   - For each line item, check if matching product+colour has stock
   - If stock exists, create a verification task
   - If no stock, no verification needed (full quantity must be produced)
4. Two parallel tracks begin:
   a. Sharon reviews order in dashboard (existing approval flow)
   b. Warehouse sees verification tasks on their interface
5. Warehouse physically checks stock, confirms: "yes, 20 exist" or adjusts
6. When BOTH are complete:
   - Works orders generate with adjusted quantities
   - WO quantity = ordered quantity - confirmed stock quantity
   - If confirmed stock >= ordered quantity, no works order needed for that line
```

### 7.3 Order Fulfilment → Stock Out

```
1. Works orders generated (quantities adjusted for verified stock)
2. Warehouse opens /stock/scan, selects "Stock Out" mode
3. Optionally selects the order being fulfilled
4. Scans each carton being picked
5. If a partial carton is needed:
   a. Scan the full carton (stock out)
   b. System prompts: "Partial box — how many units remaining?"
   c. Enter remaining quantity
   d. System generates new yellow-label QR code for partial box
   e. Staff prints yellow label and sticks it on remaining box
   f. Staff scans new partial box in (stock in)
```

### 7.4 Manual Adjustment

```
1. Admin finds a damaged/expired carton
2. Opens /stock/{itemId}
3. Records adjustment: quantity change + mandatory reason
4. Stock item status updated to 'scrapped'
5. Movement recorded in ledger
```

### 7.5 Quarterly Stocktake

```
1. Admin starts a new stocktake session at /stock/stocktake
2. System snapshots all expected in_stock items
3. Warehouse staff walk the warehouse with tablets
4. Scan every carton they find
5. System tracks: found (expected), not found (missing), unexpected (not in system)
6. Live progress bar shows scanned vs expected
7. When complete, admin reviews discrepancy report
8. Approve adjustments to reconcile system with reality
```

---

## 8. Privacy & Security

- All stock endpoints require authentication (existing JWT/Kratos)
- Role-based access control on every endpoint (warehouse vs admin)
- Warehouse users cannot modify thresholds, products, or raw materials
- Stock adjustments require a mandatory reason (audit trail)
- All movements are immutable — recorded in append-only ledger
- Stock verifications tied to specific users for accountability

---

## 9. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time to check stock levels | 30-60 min manual walk | Instant (dashboard) | Before/after comparison |
| Stock accuracy | Unknown (ad-hoc counts) | >98% (verified by stocktake) | Quarterly stocktake discrepancy rate |
| Works order over-production | Frequent (unknown stock) | Near zero (verified stock deducted) | WO quantity vs actual production needed |
| Stock visibility | None between counts | Real-time | Dashboard availability |

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Warehouse adoption resistance | Medium | High | Simplified UI, training session, bedding-in period with mandatory verification |
| WiFi connectivity drops | Low | Medium | Scan page works offline-first (queue scans, sync when reconnected) — future enhancement |
| Scanner hardware issues | Low | Low | Manual barcode entry fallback on scan page |
| Stock verification delays orders | Medium | Medium | Verification runs in parallel with Sharon's review; doesn't add serial time |
| Incorrect initial stock data | High | Medium | Mandatory physical verification during bedding-in builds trust before relying on system counts |

---

## 11. Phase Overview

| Phase | Focus | Dependencies | Deliverables |
|-------|-------|--------------|--------------|
| **Phase 1** | Database Models & Role System | None | All SQLAlchemy models, "warehouse" role, role guards, Alembic migration |
| **Phase 2** | QR Code Generation & Labels | Phase 1 | Barcode service, label PDF rendering, label generation page |
| **Phase 3** | Stock-In Scanning | Phase 2 | Scan-in logic, scanning interface, audio/visual feedback |
| **Phase 4** | Order Integration & Stock Verification | Phase 3 | Auto-verification tasks, warehouse verification UI, modified works order generation |
| **Phase 5** | Stock-Out Scanning & Partial Boxes | Phase 3 | Scan-out, partial box handling, yellow label generation |
| **Phase 6** | Stock Dashboard & Thresholds | Phase 3 | Admin dashboard, warehouse stock lookup, threshold config |
| **Phase 7** | Stocktake Verification | Phase 6 | Session management, live scanning, discrepancy detection |
| **Phase 8** | Raw Materials | Phase 1 | Admin CRUD, receive/use/adjust, colour-coded thresholds |
| **Phase 9** | Reports & Export | Phase 6 + Phase 8 | Valuation, movement history, point-in-time, stocktake reports, Excel export |

See `ORCHESTRATION.md` for detailed sequencing and handoffs.

---

## 12. Out of Scope

- Automatic raw material deduction against works orders
- Raw material assignment to production runs
- Cross-checking raw material levels against planned works orders
- Automated purchase order generation for low-stock raw materials
- Integration with external accounting/ERP systems
- Barcode scanning via mobile phone camera (uses dedicated Bluetooth scanner only)
- Offline-first scanning with sync (future enhancement)
- Multi-warehouse support

---

## 13. Dependencies

### External Dependencies
- Zebra DS22 Bluetooth barcode scanners (hardware — already owned)
- Cheap tablets for warehouse staff (hardware — to be purchased)
- A4 sticker label sheets for label printing
- WiFi network coverage in warehouse

### Internal Dependencies
- Existing User model and auth system (`backend/app/core/auth.py`)
- Existing Product catalog (`products`, `manufacturing_specs`, `material_specs`, `packaging_specs`, `pricing`)
- Existing Order system (`orders`, `order_line_items`, `backend/app/api/orders.py`)
- Existing form generation service (`backend/app/services/form_generation_service.py`)
- Existing frontend auth context (`frontend/src/contexts/SimpleAuthContext.tsx`)
- Existing header navigation (`frontend/src/components/Layout/Header.tsx`)

---

## 14. Configuration

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

## 15. Key Stakeholders

- **Grant** — Business owner (Ramjet Plastics)
- **Sharon** — Office/orders (uses dashboard for stock visibility, approves orders)
- **Warehouse Staff** — Primary scanner operators (stock in, stock out, verification, stocktakes)
- **Brett** — Developer

---

## 16. References

- `docs/PROJECT_OVERVIEW.md` — Overall project architecture
- `docs/BACKEND_STRUCTURE.md` — API patterns and conventions
- `docs/AUTHENTICATION.md` — Auth system details
- `docs/DATABASE_SETUP.md` — Database conventions
- `docs/FRONTEND_SETUP.md` — Frontend patterns
- `docs/plans/feature_plans/stock_tracking/_archive/` — Previous build pack (superseded)

---

*Document created: 2026-02-18*
*Status: Planning*
