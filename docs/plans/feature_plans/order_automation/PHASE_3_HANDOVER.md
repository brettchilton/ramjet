# Phase 3 Handover: LLM Extraction Pipeline

**Date:** February 7, 2026
**Status:** COMPLETE
**Previous Phase:** Phase 2 (Gmail OAuth2 Integration)
**Next Phase:** Phase 4 (Form Generation)

---

## What Was Built

The core LLM extraction pipeline: takes unprocessed emails from `incoming_emails`, sends content (body text + PDF/Excel/image attachments) to Claude AI, gets structured order data back, matches product codes against the catalog, and creates `orders` + `order_line_items` records.

---

## Files Created

| File | Description |
|------|-------------|
| `backend/app/core/models.py` | Added `Order` and `OrderLineItem` SQLAlchemy models with JSONB import |
| `backend/migrations/versions/c3d4e5f6g7h8_add_order_tables.py` | Alembic migration for orders + order_line_items tables |
| `backend/app/schemas/order_schemas.py` | Pydantic V2 schemas: OrderLineItemResponse, OrderSummary, OrderDetail, ProcessEmailsResponse, ProcessSingleResponse |
| `backend/app/services/extraction_service.py` | Core extraction service: content prep, Claude API calls, JSON parsing, order creation, pipeline orchestration |
| `backend/app/api/orders.py` | Orders API router: list, get, process-pending, process-email, reprocess |
| `backend/tests/test_extraction.py` | Comprehensive tests with mocked Anthropic API |

## Files Modified

| File | Changes |
|------|---------|
| `backend/requirements.txt` | Added `anthropic>=0.40.0`, `pdfplumber>=0.10.0` |
| `docker-compose.yml` | Added `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` env vars to backend service |
| `backend/app/main.py` | Added `orders` router import and `app.include_router(orders.router)` |

---

## Database Changes

### New Tables

**orders**
- UUID PK (`id`), Integer FK to `incoming_emails.id` (`email_id`)
- Status: pending | approved | rejected | error
- Header fields: customer_name, po_number, po_date, delivery_date, special_instructions
- Extraction metadata: extraction_confidence (Numeric 3,2), extraction_raw_json (JSONB)
- Approval fields: approved_by (UUID FK to users), approved_at, rejected_reason
- File storage: office_order_file (LargeBinary)
- Indexes: idx_orders_status, idx_orders_email

**order_line_items**
- UUID PK, UUID FK to orders.id (CASCADE delete)
- Extracted data: product_code, product_description, colour, quantity, unit_price
- Matched data: matched_product_code (FK to products.product_code), line_total
- Review flags: confidence (Numeric 3,2), needs_review (Boolean)
- File storage: works_order_file (LargeBinary)
- Index: idx_order_line_items_order_id

### Migration

- Revision: `c3d4e5f6g7h8`
- Down revision: `a1b2c3d4e5f6` (email tables migration)
- **Migration has NOT been run** — run with: `docker exec eezy_peezy_backend alembic upgrade head`

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `email_id` is Integer FK (not UUID) | Matches Phase 2's `incoming_emails.id` which uses Integer PK |
| Sync extraction service + async API wrapping | Matches `gmail_service.py` pattern; uses `run_in_executor` at the API layer |
| Error orders created on extraction failure | Ensures visibility — failed extractions show up in the order list with status "error" |
| `needs_review` flag set on multiple conditions | No match, low match confidence (<0.9), or low item confidence (<0.8) |
| PDF sent as native `document` content block | Uses Claude's native PDF support; falls back to pdfplumber text extraction for >25MB PDFs |
| Excel parsed to text via openpyxl | Claude can't read Excel natively; converted to tab-separated text |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/orders/` | List orders, optional `?status=` filter |
| `GET` | `/api/orders/{order_id}` | Get order detail with line items |
| `POST` | `/api/orders/process-pending` | Process all unprocessed emails |
| `POST` | `/api/orders/process-email/{email_id}` | Process a single email |
| `POST` | `/api/orders/{order_id}/reprocess` | Re-extract from source email |

Full CRUD (update, approve, reject) deferred to Phase 5 per plan.

---

## How to Test

```bash
# Run migration first
docker exec eezy_peezy_backend alembic upgrade head

# Run tests (mocked Anthropic — no API key needed)
docker exec eezy_peezy_backend python -m pytest tests/test_extraction.py -v

# Manual test (requires ANTHROPIC_API_KEY and emails in inbox)
# 1. Trigger email fetch
curl -X POST http://localhost:8006/api/system/email-monitor/poll-now
# 2. Process all unprocessed emails
curl -X POST http://localhost:8006/api/orders/process-pending
# 3. View created orders
curl http://localhost:8006/api/orders/
```

---

## Dependencies for Next Phase

Phase 4 (Form Generation) needs:
- `orders` and `order_line_items` tables populated with extracted data
- `enrichment_service.py` for full product specs (already exists from Phase 1)
- Excel templates from `docs/template_docs/`
- `openpyxl` (already in requirements.txt from Phase 1)

Phase 4 will:
- Create `services/form_generation_service.py`
- Load Excel templates, map cells, populate with enriched data
- Store generated files in `orders.office_order_file` and `order_line_items.works_order_file`

---

## Known Issues / Gotchas

- The `anthropic` package import in tests uses `anthropic.APIError` — if the package isn't installed, some tests will skip gracefully
- The extraction prompt is tuned for purchase orders; may need refinement with real-world email variety
- `pdfplumber` fallback only activates for PDFs >25MB (Claude API limit)
- Excel `.xls` (old format) files won't parse with openpyxl — only `.xlsx` is supported. If old-format Excel POs are common, consider adding `xlrd` dependency
