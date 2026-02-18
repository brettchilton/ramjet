# Phase 4 Handover: Order Integration & Stock Verification

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Created
- `backend/app/services/stock_verification_service.py` — Core verification logic:
  - `create_verifications_for_order(order_id, db)` — auto-creates StockVerification records for line items with existing stock
  - `confirm_verification(verification_id, verified_quantity, user_id, db, notes)` — warehouse confirms stock count, triggers WO generation if conditions met
  - `check_and_generate_works_orders(order_id, db)` — checks both approval + verification complete, generates adjusted WOs
  - `_generate_adjusted_works_orders(order, verifications, db)` — generates office order + works orders with qty = ordered - verified
  - `calculate_adjusted_quantity(ordered_qty, verified_qty)` — returns max(0, ordered - verified)
  - `get_verification_status_for_order(order_id, db)` — returns summary of verification status for an order

- `backend/app/api/stock_verification.py` — API endpoints:
  - `GET /api/stock-verifications/pending` — lists pending verifications grouped by order, enriched with order + line item context
  - `GET /api/stock-verifications/order/{order_id}` — gets all verifications for a specific order
  - `POST /api/stock-verifications/{id}/confirm` — confirms a verification with verified_quantity + optional notes

- `frontend/src/services/stockVerificationService.ts` — API calls: `fetchPendingVerifications()`, `confirmVerification()`
- `frontend/src/hooks/useStockVerification.ts` — React Query hooks: `usePendingVerifications()`, `useConfirmVerification()`
- `frontend/src/components/stock/VerificationTaskCard.tsx` — Reusable card component for each verification task (pending form or confirmed display)
- `frontend/src/routes/stock/verification.tsx` — Warehouse verification page at `/stock/verification`

### Files Modified
- `backend/app/api/orders.py` — `approve_order()` rewritten:
  - Sets status to `approved` first
  - Checks verification status via `get_verification_status_for_order()`
  - If no verifications exist → generates forms immediately (old behaviour)
  - If all verifications confirmed → generates with adjusted quantities
  - If verifications pending → returns "Awaiting stock verification" message
  - Response includes `verification_status` and `verifications` summary

- `backend/app/services/form_generation_service.py` — `generate_works_order()`:
  - Accepts optional `adjusted_quantity` and `verified_stock` parameters
  - Uses `adjusted_quantity` instead of `line_item.quantity` for production qty and material calculations
  - Adds "Stock Note" row showing stock on hand and produce quantity when stock was deducted
  - Displays "Ordered Qty" and "Produce Qty" separately in the WO

- `backend/app/services/extraction_service.py` — `create_order_from_extraction()`:
  - After order + line items created, calls `create_verifications_for_order()` for pending orders
  - Wrapped in try/except so verification creation failure doesn't break order creation

- `backend/app/core/models.py` — `Order.status` column widened from `String(20)` to `String(30)` to accommodate `works_order_generated`
- `backend/app/schemas/order_schemas.py` — Added `VerificationSummary` schema, extended `ApproveResponse` with `verification_status` and `verifications` fields
- `frontend/src/types/stock.ts` — Added `StockVerification`, `VerificationOrder`, `VerificationConfirmRequest`, `VerificationConfirmResponse` interfaces
- `frontend/src/routeTree.gen.ts` — Added `/stock/verification` route

### Database Change
- `orders.status` column altered from `VARCHAR(20)` to `VARCHAR(30)` (applied directly, no migration file — this should be captured in a migration for production)

## Key Implementation Details

- **Parallel flow**: Order approval and stock verification are independent. Either can happen first. Works orders only generate when BOTH are complete. The `check_and_generate_works_orders()` function is called from both `approve_order()` and `confirm_verification()`.

- **No verification for zero stock**: If a line item's product+colour has no in_stock items, no verification record is created. The order proceeds without waiting for verification for that line.

- **Adjusted quantity**: WO quantity = ordered - verified. If verified >= ordered, the works order for that line is skipped entirely (no file generated). Material requirements are calculated based on the adjusted production quantity.

- **Verification at order creation**: Verifications are auto-created in `extraction_service.py` after order + line items are committed. This happens inside a try/except so a failure doesn't break the order pipeline.

- **API returns enriched data**: The `/pending` endpoint groups verifications by order and includes order context (customer_name, po_number, status) and line item context (line_number, ordered_quantity, product_description) so the frontend doesn't need separate API calls.

- **Status column widened**: The `orders.status` column was `VARCHAR(20)` which couldn't fit `works_order_generated` (22 chars). Widened to `VARCHAR(30)` and updated the model to match.

## State of the Codebase
- **What works**: Full verification pipeline — order created → verifications auto-created → warehouse views pending tasks → confirms stock count → if approved + all verified → WOs generate with adjusted quantities. Both orderings (approve-then-verify and verify-then-approve) work correctly.
- **Known issues**: The `VARCHAR(20)` → `VARCHAR(30)` change was applied directly via SQL. If deploying to production, this needs to be captured in an Alembic migration.

## For the Next Phase

### Phase 5 (Stock-Out Scanning & Partial Boxes) should:
- Add `scan_out()` to `stock_service.py` (transitions `in_stock` → `picked`)
- Add `partial_repack()` for handling partial box scenarios
- Enable the Stock Out button on `/stock/scan` and add scan-out mode
- Link scan-out to orders (`order_id` on stock items)
- Generate yellow labels for partial boxes
- The `ScanInput` and `ScanResult` components are reusable for both modes

### Phase 6 (Dashboard & Thresholds) should:
- Use `GET /api/stock/summary` endpoint for the stock dashboard
- Add threshold-aware colouring
- Build admin dashboard and warehouse read-only stock lookup

## Test Results
- `create_verifications_for_order()` creates verification for line items with stock — PASS
- No verification created for line items with zero stock — PASS
- No verification created for unmatched products (no matched_product_code) — PASS
- `confirm_verification()` updates status, verified_qty, verified_by, verified_at — PASS
- WO NOT triggered when order not yet approved — PASS
- WO NOT triggered when verification still pending — PASS
- WO triggered when both approved AND verified — PASS
- Order status transitions to `works_order_generated` — PASS
- Office order file generated — PASS
- Works order file generated with adjusted quantity — PASS
- Verify-then-approve flow works (WO triggers on approve) — PASS
- Verified >= ordered → no WO file generated for that line — PASS
- `get_verification_status_for_order()` returns correct counts — PASS
- `calculate_adjusted_quantity()` edge cases all pass — PASS
- API endpoints registered and auth-protected (401 without auth) — PASS
- Frontend TypeScript compiles without errors — PASS
