# Phase 2: QR Code Generation & Labels

## 1. Overview

**Objective**: Generate unique QR codes for cartons and render printable label PDFs.

**Scope**:
- `services/barcode_service.py` — QR generation, unique ID sequencing, label PDF rendering
- Label generation endpoint on `api/stock.py`
- Frontend: `/stock/labels` route — label generation form, preview, print

**Does NOT include**:
- Scanning logic (Phase 3)
- Stock movements (Phase 3)
- Dashboard (Phase 6)

**Dependencies**: Phase 1 (StockItem model, Product CRUD, role guards)

---

## 2. Barcode Service

### 2.1 `backend/app/services/barcode_service.py`

**Responsibilities:**
- Generate unique barcode IDs following format: `RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}`
- Render QR code images using the `qrcode` library
- Compose printable labels with QR code + human-readable text
- Support batch label generation (e.g., "generate 20 labels for LOCAP2 Black, 500/carton")
- Output as PDF (multiple labels per A4 page) using `reportlab`
- Differentiate pink (full) vs yellow (partial) label styling

### 2.2 Barcode ID Format

```
RJ-LOCAP2-BLK-20260211-001
│  │      │   │        │
│  │      │   │        └── Sequence (resets daily per product+colour)
│  │      │   └── Date (YYYYMMDD)
│  │      └── Colour short code (first 3 chars uppercase)
│  └── Product code
└── Prefix (configurable via QR_CODE_PREFIX env var)
```

**Sequence logic:**
- Query `stock_items` for today's date + product_code + colour_short
- Next sequence = max existing + 1 (or 001 if none exist today)
- Must handle concurrent requests safely (use DB sequence or SELECT FOR UPDATE)

### 2.3 Colour Short Code Mapping

Generate from colour name: first 3 characters uppercase.
- Black → BLK
- White → WHT
- Yellow → YEL
- Natural → NAT
- Red → RED

Store as a helper function. Can be extended later with configurable overrides.

### 2.4 Label Layout

Each label sticker:
```
┌─────────────────────────────┐
│  ┌─────────┐                │
│  │         │  LOCAP2        │
│  │  [QR]   │  Black         │
│  │         │  Qty: 500      │
│  └─────────┘  2026-02-11    │
│                              │
│  RJ-LOCAP2-BLK-20260211-001 │
│  ■ FULL BOX (pink bg)       │
└─────────────────────────────┘
```

**Pink background** for full cartons, **yellow background** for partial cartons.

### 2.5 PDF Generation

Use `reportlab` to compose multi-label A4 pages:
- Page size: A4 (configurable via `LABEL_PAGE_SIZE`)
- Labels per page: configurable via `LABELS_PER_PAGE` (default 10, 2 columns × 5 rows)
- Each label contains: QR code image, product code, colour, quantity, date, barcode ID, box type indicator

---

## 3. API Endpoint

### 3.1 Label Generation

Add to `api/stock.py`:

```
POST /api/stock/labels/generate
```

**Request body:**
```json
{
  "product_code": "LOCAP2",
  "colour": "Black",
  "quantity_per_carton": 500,
  "number_of_labels": 20,
  "box_type": "full",
  "production_date": "2026-02-11"
}
```

**Response:** PDF file (application/pdf) with generated labels.

**Auth:** `require_role("warehouse")` — accessible to warehouse + admin.

**Behaviour:**
1. Validate product_code exists in products table
2. Generate N unique barcode IDs
3. Create `StockItem` records in DB with status `pending_scan` (not yet in stock — they become `in_stock` when scanned in Phase 3)
4. Render PDF with QR labels
5. Return PDF as streaming response

**Note:** Labels are generated before scanning. The stock items are created with a pre-scan status so the barcode IDs are reserved. Phase 3's scan-in will transition these to `in_stock`.

---

## 4. Frontend: Label Generation Page

### 4.1 Route: `/stock/labels`

**File:** `frontend/src/routes/stock/labels.tsx`

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Generate Labels                                          │
│                                                           │
│  Product:  [LOCAP2 - Louvre End Cap 152mm     ▾]         │
│  Colour:   [Black                              ▾]        │
│  Quantity per carton: [500                      ]         │
│  Number of labels:    [20                       ]         │
│  Box type: (●) Full  ( ) Partial                          │
│  Production date: [2026-02-11]                            │
│                                                           │
│  [Generate & Download PDF]                                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Behaviour:**
- Product dropdown populated from `/api/products/` (only `is_stockable=true`)
- Colour dropdown populated from product's material specs
- Quantity pre-filled from product's packaging spec (`qty_per_carton`)
- Production date defaults to today
- On submit: POST to `/api/stock/labels/generate`, download returned PDF
- Large, touch-friendly form elements for tablet use

### 4.2 Service + Hook

**File:** `frontend/src/services/stockService.ts`
- `generateLabels(params)` — POST to `/api/stock/labels/generate`, return blob

**File:** `frontend/src/hooks/useStock.ts`
- `useGenerateLabels()` — mutation hook wrapping `generateLabels`

---

## 5. File Structure

```
backend/app/
├── services/
│   └── barcode_service.py              ← NEW
├── api/
│   └── stock.py                        ← NEW (label endpoint)
├── schemas/
│   └── stock_schemas.py                ← MODIFY: Add LabelGenerateRequest

frontend/src/
├── routes/
│   └── stock/
│       └── labels.tsx                  ← NEW
├── services/
│   └── stockService.ts                 ← NEW
├── hooks/
│   └── useStock.ts                     ← NEW
```

---

## 6. Environment Variables

```bash
LABEL_COMPANY_NAME=RAMJET PLASTICS     # Already in .env from Phase 1
LABEL_PAGE_SIZE=A4
LABELS_PER_PAGE=10
QR_CODE_PREFIX=RJ
QR_CODE_ERROR_CORRECTION=M
```

---

## 7. Testing Requirements

### Unit Tests
- Barcode ID generation produces correct format
- Sequence increments correctly
- Colour short code mapping works
- QR code image generates valid QR content
- PDF renders correct number of labels per page
- Duplicate barcode IDs are prevented

### Integration Tests
- Generate 20 labels via API, verify 20 StockItem records created
- Verify PDF response is valid PDF
- Verify barcode IDs are unique and sequential
- Frontend form submits and triggers PDF download

---

## 8. Exit Criteria

- [ ] `barcode_service.py` generates unique barcode IDs in correct format
- [ ] QR code images render correctly (scannable by Zebra DS22)
- [ ] PDF labels render with correct layout (QR + text + colour coding)
- [ ] Pink/yellow label differentiation works
- [ ] Batch generation creates correct number of labels
- [ ] API endpoint returns valid PDF
- [ ] Frontend label generation page works on tablet
- [ ] Product/colour dropdowns populated from database
- [ ] StockItem records created in database for generated labels
- [ ] Sequence numbers increment correctly within same day/product/colour

---

## 9. Handoff to Phase 3

**Artifacts provided:**
- `barcode_service.py` with QR generation and PDF rendering
- Label generation endpoint on `/api/stock/labels/generate`
- Frontend `/stock/labels` page
- StockItem records exist in DB (status: pending scan)

**Phase 3 will:**
- Create `stock_service.py` with scan-in logic
- Add scan-in endpoint to `api/stock.py`
- Build scanning UI at `/stock/scan`
- Transition StockItem records from pending to `in_stock` on scan

---

*Document created: 2026-02-18*
*Status: Planning*
