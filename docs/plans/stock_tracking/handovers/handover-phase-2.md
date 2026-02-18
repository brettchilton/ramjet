# Phase 2 Handover: QR Code Generation & Labels

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Created
- `backend/app/services/barcode_service.py` — Full barcode/label service with:
  - `get_colour_short()` — colour name to 3-char code mapping (with overrides for common colours)
  - `generate_barcode_ids()` — unique ID sequencing in format `RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}`
  - `generate_qr_image()` — QR code PNG generation using `qrcode` library
  - `create_stock_items()` — batch StockItem creation with `pending_scan` status
  - `generate_label_pdf()` — multi-page A4 PDF rendering with reportlab (2 cols x 5 rows = 10 labels/page)
  - `generate_labels()` — orchestrator function (validate → generate IDs → create records → render PDF)
- `frontend/src/services/stockService.ts` — API service for label generation (blob download) + product/colour fetching
- `frontend/src/hooks/useStock.ts` — React Query hooks: `useStockableProducts()`, `useProductDetail()`, `useGenerateLabels()`
- `frontend/src/routes/stock/labels.tsx` — Label generation page with:
  - Product dropdown (filtered to stockable + active products)
  - Colour dropdown (populated from product's material specs)
  - Quantity pre-filled from packaging spec
  - Box type radio (full=pink, partial=yellow with colour indicators)
  - Production date picker (defaults to today)
  - Auto-download PDF on generation
  - Tablet-friendly: large touch targets (h-12 inputs, h-14 submit button), text-base sizing

### Files Modified
- `backend/requirements.txt` — Added `qrcode[pil]>=7.4`, `Pillow>=10.0`, `reportlab>=4.0`
- `backend/app/schemas/stock_schemas.py` — Added `LabelGenerateRequest` and `LabelGenerateResponse` models
- `backend/app/api/stock.py` — Replaced stub with label generation endpoint (`POST /api/stock/labels/generate`)

## Key Implementation Details
- **Barcode ID format**: `RJ-LOCAP2-BLK-20260218-001` — sequence resets daily per product+colour
- **Sequence safety**: Uses `SELECT MAX(barcode_id)` with LIKE filter to find next sequence. For concurrent requests, the UNIQUE constraint on `barcode_id` will prevent duplicates (caller should retry on IntegrityError)
- **Label layout**: 90mm x 50mm labels, 2 columns x 5 rows on A4, with rounded corners. QR code on left, text (product, colour, qty, date) on right, barcode ID at bottom
- **Colour coding**: Pink background (`#FFB6C1`) for full boxes, yellow (`#FFEB3B`) for partial boxes — matches physical label sticker colours
- **Status flow**: Labels create `StockItem` records with `status='pending_scan'`. Phase 3 will transition these to `in_stock` on scan
- **PDF streaming**: Endpoint returns `StreamingResponse` with `application/pdf` content type. Custom headers include label count and first/last barcode IDs
- **Frontend blob download**: The `generateLabels` service function uses raw `fetch()` (not `apiClient`) because it needs to handle blob responses. The `useGenerateLabels` hook auto-downloads via temporary anchor element
- **Auth**: Endpoint uses `require_role("warehouse")` — accessible to warehouse and admin roles

## State of the Codebase
- **What works**: Full label generation pipeline — select product/colour, generate N labels, get PDF download with QR codes. Barcode IDs are unique and sequential. Stock items created in DB with `pending_scan` status. Frontend page renders correctly with HMR.
- **Known issues**: None. Dependencies installed in container but will need to be re-installed if container is rebuilt (they're in `requirements.txt` for the next build).

## For the Next Phase
- Phase 3 (Stock-In Scanning) should:
  - Create `backend/app/services/stock_service.py` with `scan_in()` — transitions `StockItem.status` from `pending_scan` to `in_stock`, sets `scanned_in_at` and `scanned_in_by`, creates `StockMovement` record
  - Add `POST /api/stock/scan-in` endpoint to `backend/app/api/stock.py`
  - Build `/stock/scan` page with auto-focused input, scanner integration (Zebra DS22 types barcode + Enter)
  - Build `ScanInput` component (auto-focus, auto-clear) and `ScanResult` component (success/error feedback)
  - StockItem records already exist with `pending_scan` status — scanning should look up by `barcode_id` and transition
  - Add `get_stock_levels()` to stock_service for aggregated stock queries
- The test product `LOCAP2` exists in the DB (created during testing). It has material spec for Black and packaging spec with qty_per_carton=500

## Test Results
- Barcode ID generation produces correct format (`RJ-LOCAP2-BLK-20260218-001`) — PASS
- Sequence increments correctly (001→005, then 006→008 on second batch) — PASS
- Colour short code mapping works (Black→BLK) — PASS
- QR code image generates at 290x290 pixels — PASS
- PDF renders correct number of labels (5 labels = 1 page, 10+ = multi-page) — PASS
- Pink labels for full boxes, yellow labels for partial boxes — PASS
- Invalid product code raises ValueError with clear message — PASS
- StockItem records created with correct data (barcode_id, product_code, colour, qty, box_type, status=pending_scan) — PASS
- API endpoint registered at `/api/stock/labels/generate` (verified via OpenAPI) — PASS
- Frontend route registered at `/stock/labels` (verified in routeTree.gen.ts) — PASS
- Frontend HMR picks up all new files without errors — PASS
