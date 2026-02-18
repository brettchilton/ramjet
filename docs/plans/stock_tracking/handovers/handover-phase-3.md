# Phase 3 Handover: Stock-In Scanning

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Created
- `backend/app/services/stock_service.py` — Core stock service with:
  - `scan_in(barcode_id, user_id, db, notes)` — transitions StockItem from `pending_scan` to `in_stock`, sets `scanned_in_at`/`scanned_in_by`, creates `StockMovement` record
  - `get_stock_levels(db, product_code, colour)` — aggregates in_stock items by product_code+colour, returns carton count and total units
- `frontend/src/types/stock.ts` — TypeScript interfaces: `StockItem`, `StockMovement`, `ScanResponse`, `ScanSessionEntry`, `StockSummaryItem`, `ScanMode`
- `frontend/src/components/stock/ScanInput.tsx` — Reusable auto-focused scanner input:
  - Auto-focuses on mount and after each scan
  - Re-focuses when user taps elsewhere on page (tablet use case)
  - 300ms debounce prevents double-submit from rapid scans
  - `inputMode="none"` prevents virtual keyboard on tablets while allowing physical scanner/keyboard
  - Shows spinner during processing
- `frontend/src/components/stock/ScanResult.tsx` — Success/error result display:
  - Green card + CheckCircle icon for success
  - Red card + XCircle icon for errors
  - Shows product details (code, description, colour, quantity, box type, barcode ID) on success
  - Web Audio API feedback — 880Hz sine beep (success), 220Hz square tone (error)
  - AudioContext lazy-initialised on first scan to comply with browser autoplay policies
- `frontend/src/routes/stock/scan.tsx` — Main scanning page:
  - Stock In / Stock Out mode toggle (Stock Out disabled — placeholder for Phase 5)
  - ScanInput + ScanResult integration
  - Session summary (carton count, total units)
  - Recent scans list (capped at 20, most recent first)
  - Session state is local (resets on page reload)

### Files Modified
- `backend/app/api/stock.py` — Added `POST /api/stock/scan-in` and `GET /api/stock/summary` endpoints
- `backend/app/schemas/stock_schemas.py` — Updated `ScanResponse` to include `success`, `error`, `barcode_id`, `product_description` fields
- `frontend/src/services/stockService.ts` — Added `scanIn()` API call
- `frontend/src/hooks/useStock.ts` — Added `useScanIn()` mutation hook with configurable `onSuccess`/`onError` callbacks
- `frontend/src/routeTree.gen.ts` — Auto-regenerated to include `/stock/scan` route

## Key Implementation Details

- **Scan-in returns 200 for both success and error**: The `POST /api/stock/scan-in` endpoint always returns HTTP 200 with `success: true/false`. This is intentional — the frontend needs the structured `ScanResponse` with barcode details for display, not a generic HTTP error. Validation errors (duplicate scan, unknown barcode, wrong status) are returned inline.
- **Status transitions enforced**: Only `pending_scan` → `in_stock` is allowed. Attempting to scan an `in_stock`, `picked`, `scrapped`, or `consumed` item returns a descriptive error.
- **Movement recording**: Every successful scan-in creates an immutable `StockMovement` record with `movement_type='stock_in'` and `quantity_change=+quantity`.
- **Product description in response**: The scan-in endpoint fetches the Product model to include `product_description` in the response, giving the scanner operator context about what they just scanned.
- **Audio feedback uses Web Audio API**: No audio files needed. Success = short 880Hz sine wave (0.15s). Error = 220Hz square wave (0.3s). AudioContext is lazy-created on first use.
- **Scanner HID mode**: The ScanInput component works with the Zebra DS22 in Bluetooth HID mode. The scanner types the QR content as keystrokes into the focused input, then sends Enter which triggers form submission.

## State of the Codebase
- **What works**: Full scan-in pipeline — generate labels (Phase 2) → scan barcode → item transitions to `in_stock` → movement recorded → stock levels update. Frontend scan page renders correctly with HMR. Audio and visual feedback both working.
- **Known issues**: None.

## For the Next Phase

### Phase 4 (Order Integration & Stock Verification) should:
- Use `get_stock_levels()` from `stock_service.py` to check available stock when orders are created
- Auto-create `StockVerification` records linked to order line items
- Build warehouse verification UI at `/stock/verification`
- Modify works order generation to wait for both approval AND verification
- Deduct verified stock from WO quantities

### Phase 5 (Stock-Out Scanning & Partial Boxes) should:
- Add `scan_out()` to `stock_service.py` (transitions `in_stock` → `picked`)
- Add `partial_repack()` for handling partial box scenarios
- Enable the Stock Out button on `/stock/scan` and add scan-out mode
- Generate yellow labels for partial boxes
- The `ScanInput` and `ScanResult` components are designed to be reusable for both modes

### Phase 6 (Dashboard & Thresholds) should:
- Use `GET /api/stock/summary` endpoint (already implemented) for the stock dashboard
- Add threshold-aware colouring (the `StockSummaryItem` schema already has `threshold_status`, `red_threshold`, `amber_threshold` fields — currently null)
- Build the admin dashboard and warehouse read-only stock lookup

## Test Results
- `scan_in()` transitions pending_scan → in_stock — PASS
- `scan_in()` creates StockMovement with correct quantity_change — PASS
- `scan_in()` sets scanned_in_at and scanned_in_by — PASS
- Duplicate scan returns "Already scanned in" error — PASS
- Unknown barcode returns "Barcode not recognised" error — PASS
- Picked/scrapped/consumed items return descriptive error — PASS
- `get_stock_levels()` aggregates correctly by product_code+colour — PASS
- API endpoint `POST /api/stock/scan-in` returns correct ScanResponse — PASS
- API endpoint `GET /api/stock/summary` returns aggregated levels — PASS
- Frontend route `/stock/scan` registered in routeTree.gen.ts — PASS
- Frontend HMR picks up all new files without errors — PASS
