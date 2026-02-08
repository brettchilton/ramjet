# Phase 4 Handover: Form Generation

**Date:** February 7, 2026
**Status:** COMPLETE
**Previous Phase:** Phase 3 (LLM Extraction Pipeline)
**Next Phase:** Phase 5 (Frontend - Dashboard & Order Review)

---

## What Was Built

Form generation service that builds Office Order and Works Order Excel files (.xlsx) from enriched order data using openpyxl. Also added the approve/reject/update/download API endpoints needed to support the Phase 5 frontend review workflow.

---

## Files Created

| File | Description |
|------|-------------|
| `backend/app/services/form_generation_service.py` | Core service: `generate_office_order()`, `generate_works_order()`, `generate_all_forms()` |
| `backend/tests/test_form_generation.py` | Comprehensive tests for form generation, approve/reject, update, and download endpoints |

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/schemas/order_schemas.py` | Added `OrderUpdateRequest`, `LineItemUpdateRequest`, `RejectRequest`, `ApproveResponse`, `RejectResponse` schemas; added `has_forms` to `OrderSummary`, `has_office_order` to `OrderDetail` |
| `backend/app/api/orders.py` | Added 7 new endpoints (PUT order, PUT line item, POST approve, POST reject, GET office order, GET works order, GET source PDF); updated list/detail to populate `has_forms`/`has_office_order` |

---

## No Database Changes

No new migrations or dependencies. The `office_order_file` (LargeBinary) column on `orders` and `works_order_file` (LargeBinary) column on `order_line_items` were already created in Phase 3's migration. `openpyxl` was already in `requirements.txt`.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Build Excel from scratch (not from templates) | Legacy `.xls` templates can't be used with openpyxl; building from scratch gives full control over formatting |
| Forms generated on approve | Forms are generated during the approve action via `run_in_executor` to avoid blocking the event loop |
| Works orders use enrichment service | Pulls full product specs and calculates material/packaging requirements for matched products; sections left blank for unmatched products |
| Australian date format (dd/mm/YYYY) | Matches business convention for Ramjet Plastics |
| Decimal → float conversion | openpyxl doesn't handle Python `Decimal` objects; all numeric values converted via `_to_float()` |
| WO# format: `WO-{po_number}-{line_number}` | Links works orders back to the source PO for traceability |

---

## API Endpoints (New)

| Method | Path | Description |
|--------|------|-------------|
| `PUT` | `/api/orders/{order_id}` | Update order header (pending only) |
| `PUT` | `/api/orders/{order_id}/line-items/{item_id}` | Update line item + recalculate line_total (pending only) |
| `POST` | `/api/orders/{order_id}/approve` | Approve order → generate all forms → set status=approved |
| `POST` | `/api/orders/{order_id}/reject` | Reject order with reason (pending only) |
| `GET` | `/api/orders/{order_id}/forms/office-order` | Download Office Order .xlsx |
| `GET` | `/api/orders/{order_id}/forms/works-order/{item_id}` | Download Works Order .xlsx |
| `GET` | `/api/orders/{order_id}/source-pdf/{attachment_id}` | Download original email attachment |

### Updated Endpoints

| Method | Path | Change |
|--------|------|--------|
| `GET` | `/api/orders/` | Now includes `has_forms` boolean field |
| `GET` | `/api/orders/{order_id}` | Now includes `has_office_order` boolean field |

---

## Office Order Layout

7 columns (A-G):
- Row 1-2: Company title ("RAMJET PLASTICS") + form title ("OFFICE ORDER")
- Row 4-5: Customer/PO#/dates in label-value pairs
- Row 7: Table headers (Line, Product Code, Description, Colour, Qty, Unit Price, Line Total)
- Row 8+: Line items with alternating blue row fills
- Below items: Order Total row (green fill)
- Optional: Special Instructions section

## Works Order Layout

6 columns (A-F), key-value pair format:
- Title rows (company, "WORKS ORDER", WO number)
- Section 1: Order Details
- Section 2: Manufacturing Specifications
- Section 3: Material Specifications
- Section 4: Material Requirements (Calculated)
- Section 5: Packaging
- Section 6: Packaging Requirements (Calculated)
- Section 7: Notes

Each section has a blue header bar. Unmatched products show "specifications unavailable" messages.

---

## How to Test

```bash
# Run tests (uses real DB, no mocking needed for form generation)
docker exec eezy_peezy_backend python -m pytest tests/test_form_generation.py -v

# Manual test (if orders exist in DB)
# 1. List pending orders
curl http://localhost:8006/api/orders/?status=pending
# 2. Approve an order (generates forms)
curl -X POST http://localhost:8006/api/orders/{order_id}/approve
# 3. Download Office Order
curl -o office_order.xlsx http://localhost:8006/api/orders/{order_id}/forms/office-order
# 4. Open office_order.xlsx to verify formatting and data
```

---

## Dependencies for Next Phase

Phase 5 (Frontend - Dashboard & Order Review) needs:
- All API endpoints from Phases 3+4 are ready
- Frontend components for: order list (with `has_forms` indicators), order detail view, approve/reject buttons, form download links, line item editing
- Consider WebSocket or polling for real-time status updates

---

## Known Issues / Gotchas

- `get_product_full_specs()` returns a single dict when colour is specified, a list when it's not — the form generation service handles both cases
- Material requirements can only be calculated when both `matched_product_code` and `colour` are present
- Generated files are stored as LargeBinary (BYTEA) in PostgreSQL — adequate for prototype but consider object storage for production scale
- The approve endpoint is async with `run_in_executor` — form generation for orders with many line items may take a moment
