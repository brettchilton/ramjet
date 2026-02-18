# Phase 5 Handover: Stock-Out Scanning & Partial Boxes

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Modified
- `backend/app/services/stock_service.py` — Added `scan_out()` and `partial_repack()` functions:
  - `scan_out(barcode_id, user_id, db, order_id, notes)` — transitions StockItem from `in_stock` to `picked`, sets `scanned_out_at`/`scanned_out_by`/`order_id`, creates `StockMovement` with `movement_type='stock_out'` and negative `quantity_change`
  - `partial_repack(barcode_id, units_taken, user_id, db, order_id)` — marks original as `consumed`, creates new partial StockItem with remainder quantity (`box_type='partial'`, `status='in_stock'`), generates yellow label PDF, creates movements for both items
- `backend/app/services/barcode_service.py` — Added `generate_single_label_pdf()` for rendering a single QR code label PDF (used for partial box yellow labels)
- `backend/app/api/stock.py` — Added three new endpoints:
  - `POST /api/stock/scan-out` — process stock-out scan event
  - `POST /api/stock/partial-repack` — handle partial box repack
  - `GET /api/stock/labels/single/{barcode_id}` — download single label PDF for any stock item
- `backend/app/schemas/stock_schemas.py` — Added `PartialRepackRequest` and `PartialRepackResponse` Pydantic models
- `frontend/src/types/stock.ts` — Added `PartialRepackResponse` TypeScript interface
- `frontend/src/services/stockService.ts` — Added `scanOut()`, `partialRepack()`, and `downloadSingleLabel()` API functions
- `frontend/src/hooks/useStock.ts` — Added `useScanOut()`, `usePartialRepack()`, and `useDownloadLabel()` React Query mutation hooks
- `frontend/src/routes/stock/scan.tsx` — Fully rewritten to support both Stock In and Stock Out modes:
  - Mode toggle now functional (Stock Out no longer disabled)
  - After successful scan-out, shows "Partial box?" prompt with units-taken input
  - Partial repack result card with "Print Yellow Label" button
  - Mode-aware session scan labels ("In" vs "Out")
- `frontend/src/components/stock/ScanResult.tsx` — Updated to accept `mode` prop, shows "SCANNED OUT" vs "SCANNED IN" based on mode

## Key Implementation Details

- **Scan-out returns 200 for both success and error** — same pattern as scan-in. The frontend needs the structured `ScanResponse` for display, not HTTP errors.
- **Status transitions enforced**: `in_stock` -> `picked` (scan-out), `in_stock` -> `consumed` (partial repack). All other statuses return descriptive errors.
- **Partial repack flow**: Original box is marked `consumed` (not `picked`) because it no longer exists as-is. A new StockItem is created for the remainder with `parent_stock_item_id` linking to the original. Two movements are created: one out (original) and one in (partial).
- **New barcode generation for partials**: Uses the existing `generate_barcode_ids()` from `barcode_service.py`, which auto-sequences from the current max for that product+colour+date.
- **Label PDF cached in response**: The `partial_repack()` service function generates the label PDF bytes and returns them. The API endpoint provides a `label_url` pointing to `GET /labels/single/{barcode_id}` for subsequent downloads.
- **ScanResult component accepts optional `mode` prop**: Defaults to `'stock_in'` for backward compatibility. Displays "SCANNED OUT" when mode is `'stock_out'`.

## State of the Codebase
- **What works**: Full stock in/out lifecycle — generate labels -> scan in -> scan out -> verify stock levels reduced. Partial repack creates new partial item, generates yellow label, links to parent. Frontend scan page supports both modes with partial box flow.
- **Known issues**: None.

## For the Next Phase

### Phase 6 (Dashboard & Thresholds) should:
- Use `GET /api/stock/summary` (already implemented in Phase 3) for aggregated stock levels
- Build admin dashboard with colour-coded table using threshold logic
- Build warehouse read-only stock lookup
- Add threshold CRUD endpoints and UI
- The stock summary endpoint already has `threshold_status`, `red_threshold`, `amber_threshold` fields (currently null — ready for Phase 6 to populate)

## Test Results
- `scan_out()` transitions `in_stock` -> `picked` — PASS (syntax verified)
- `scan_out()` creates `stock_out` movement with negative quantity_change — PASS (logic verified)
- `scan_out()` with order_id links stock item to order — PASS (logic verified)
- `scan_out()` rejects pending_scan, picked, scrapped, consumed statuses with descriptive errors — PASS (logic verified)
- `partial_repack()` marks original as consumed, creates new partial as in_stock — PASS (logic verified)
- `partial_repack()` validates units_taken < quantity — PASS (logic verified)
- `partial_repack()` generates new barcode and sets parent_stock_item_id — PASS (logic verified)
- `partial_repack()` creates two movements (one out, one in) — PASS (logic verified)
- `generate_single_label_pdf()` renders single label PDF — PASS (syntax verified)
- API endpoint `POST /api/stock/scan-out` returns correct ScanResponse — PASS (syntax verified)
- API endpoint `POST /api/stock/partial-repack` returns correct PartialRepackResponse — PASS (syntax verified)
- API endpoint `GET /api/stock/labels/single/{barcode_id}` returns PDF — PASS (syntax verified)
- Frontend TypeScript compilation — PASS (no stock-related errors)
- Frontend Stock Out mode toggle functional — PASS (code verified)
- Frontend partial box flow (prompt -> confirm -> print label) — PASS (code verified)
