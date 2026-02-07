# Ramjet Order Automation - Orchestration

**Last Updated:** February 7, 2026
**Current Phase:** Phase 5 complete — Phase 6 is next

---

## Phase Progress

| Phase | Name | Status | Agent Session | Date |
|-------|------|--------|---------------|------|
| 1 | Database & Product Data | COMPLETE | Phase 1 agent | 2026-02-07 |
| 2 | Gmail OAuth2 Integration | COMPLETE | Phase 2 agent | 2026-02-07 |
| 3 | LLM Extraction Pipeline | COMPLETE | Phase 3 agent | 2026-02-07 |
| 4 | Form Generation | COMPLETE | Phase 4 agent | 2026-02-07 |
| 5 | Frontend - Dashboard & Order Review | COMPLETE | Phase 5 agent | 2026-02-07 |
| 6 | Email Distribution | NOT STARTED | — | — |
| 7 | Polish & Demo Prep | NOT STARTED | — | — |

**Status values:** `NOT STARTED` → `IN PROGRESS` → `COMPLETE` (or `BLOCKED`)

---

## Phase Dependencies

```
Phase 1 (DB & Products) ──────┐
                               ├──► Phase 3 (LLM Extraction) ──► Phase 4 (Form Gen) ──► Phase 5 (Frontend) ──► Phase 6 (Email) ──► Phase 7 (Polish)
Phase 2 (Gmail OAuth2) ───────┘
```

Phases 1 & 2 can be built in parallel. Phase 3 requires both. Phases 4-7 are sequential.

---

## Key Decisions Log

Decisions made during implementation that deviate from or clarify `MASTER_BUILD.md`:

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| 2026-02-07 | 1 | Used natural key (product_code) for FKs instead of UUID | Matches SQLite schema; cleaner queries; product_code is immutable |
| 2026-02-07 | 1 | Split manufacturing data into separate table | SQLite had it in products table; normalized for better schema design |
| 2026-02-07 | 1 | Used Numeric instead of Float for all decimal fields | Precision required for pricing and material calculations |
| 2026-02-07 | 2 | Integer PKs for email tables instead of UUID | Internal-only tables, not exposed externally; simpler FK references |
| 2026-02-07 | 2 | BYTEA for attachment storage instead of DO Spaces | Fine for prototype PO docs (<5MB); DO Spaces available for prod scale-up |
| 2026-02-07 | 2 | Conditional Gmail startup | App boots without credentials; poller only starts if GMAIL_REFRESH_TOKEN is set |
| 2026-02-07 | 3 | Integer FK for orders.email_id | Matches Phase 2's Integer PK on incoming_emails (MASTER_BUILD.md had UUID) |
| 2026-02-07 | 3 | Sync extraction + async API wrapping | Matches gmail_service.py pattern; run_in_executor at API layer |
| 2026-02-07 | 3 | Error orders for failed extractions | Ensures visibility in the order list rather than silent failures |
| 2026-02-07 | 4 | Build Excel from scratch, not from templates | Legacy .xls templates incompatible with openpyxl; building from scratch gives full layout control |
| 2026-02-07 | 4 | Forms generated on approve action | Centralises generation; avoids premature generation for orders that may be rejected |
| 2026-02-07 | 4 | Approve/reject/update endpoints added in Phase 4 | Originally planned for Phase 5, but needed to support form generation workflow |
| 2026-02-07 | 5 | react-pdf for inline PDF viewing | Full page rendering in-browser, better than iframe approach |
| 2026-02-07 | 5 | HTML form preview from live data, not Excel files | Real-time preview before approval; Excel only generated on approve |
| 2026-02-07 | 5 | Read-only by default, explicit Edit toggle | Prevents accidental modifications to extracted data |
| 2026-02-07 | 5 | Added GET /api/system/emails/{id} endpoint | Frontend needs email body + attachments for source panel |

---

## Known Issues

Issues discovered during implementation that need resolution:

| Date | Phase | Issue | Status | Resolution |
|------|-------|-------|--------|------------|
| — | — | — | — | — |

---

## Files Created / Modified

Running inventory of all new or significantly modified files across all phases:

### Phase 1
- `backend/app/core/models.py` — Added Product, ManufacturingSpec, MaterialSpec, PackagingSpec, Pricing models
- `backend/app/schemas/__init__.py` — New package
- `backend/app/schemas/product_schemas.py` — Pydantic response models
- `backend/app/api/products.py` — Products REST API router
- `backend/app/services/enrichment_service.py` — Product lookup, fuzzy matching, calculations
- `backend/scripts/seed_products.py` — SQLite → PostgreSQL migration script
- `backend/tests/__init__.py` — New package
- `backend/tests/test_products.py` — 18 integration tests
- `backend/migrations/versions/853ac57bb136_add_product_catalog_tables.py` — Alembic migration
- `backend/app/main.py` — Registered products router
- `docs/feature_plans/order_automation/PHASE_1_HANDOVER.md` — Handover documentation

### Phase 2
- `backend/app/services/gmail_service.py` — GmailPoller class (OAuth2, polling, parsing, attachments)
- `backend/app/api/system.py` — System API router (status, start, stop, poll-now)
- `backend/app/schemas/email_schemas.py` — Pydantic V2 email/monitor schemas
- `backend/migrations/versions/a1b2c3d4e5f6_add_email_monitoring_tables.py` — Alembic migration (3 tables)
- `backend/scripts/gmail_oauth_setup.py` — One-time OAuth2 consent flow script
- `backend/tests/test_email_monitor.py` — Integration + unit tests
- `backend/app/core/models.py` — Added IncomingEmail, EmailAttachment, EmailMonitorStatus models
- `backend/app/main.py` — Registered system router + Gmail startup/shutdown hooks
- `backend/requirements.txt` — Added google-auth, google-auth-oauthlib, google-api-python-client
- `docker-compose.yml` — Added 4 Gmail env vars
- `.gitignore` — Added client_secret.json patterns
- `docs/feature_plans/order_automation/PHASE_2_HANDOVER.md` — Handover documentation

### Phase 3
- `backend/app/core/models.py` — Added Order, OrderLineItem models + JSONB import
- `backend/migrations/versions/c3d4e5f6g7h8_add_order_tables.py` — Alembic migration (2 tables)
- `backend/app/schemas/order_schemas.py` — Pydantic V2 order/line-item schemas
- `backend/app/services/extraction_service.py` — Core extraction pipeline (content prep, Claude API, order creation)
- `backend/app/api/orders.py` — Orders REST API router (5 endpoints)
- `backend/tests/test_extraction.py` — Integration + unit tests with mocked Anthropic
- `backend/app/main.py` — Registered orders router
- `backend/requirements.txt` — Added anthropic, pdfplumber
- `docker-compose.yml` — Added ANTHROPIC_API_KEY, ANTHROPIC_MODEL env vars
- `docs/feature_plans/order_automation/PHASE_3_HANDOVER.md` — Handover documentation

### Phase 4
- `backend/app/services/form_generation_service.py` — Office Order + Works Order Excel generation
- `backend/app/schemas/order_schemas.py` — Added 5 new schemas + 2 new fields on existing schemas
- `backend/app/api/orders.py` — Added 7 new endpoints (approve, reject, update, download), updated 2 existing
- `backend/tests/test_form_generation.py` — Comprehensive tests for form generation and new endpoints
- `docs/feature_plans/order_automation/PHASE_4_HANDOVER.md` — Handover documentation

### Phase 5
- `frontend/src/types/orders.ts` — TypeScript interfaces for orders, emails, products
- `frontend/src/services/orderService.ts` — API service layer (all order/email/product endpoints)
- `frontend/src/hooks/useOrders.ts` — TanStack React Query hooks (queries + mutations)
- `frontend/src/components/orders/ConfidenceBadge.tsx` — Confidence score badge component
- `frontend/src/components/orders/StatusBadge.tsx` — Order status badge component
- `frontend/src/components/orders/RejectDialog.tsx` — Rejection reason dialog
- `frontend/src/components/orders/OrderSourcePanel.tsx` — Email + PDF/image source viewer
- `frontend/src/components/orders/OrderDataForm.tsx` — Extracted data form (read-only + editable)
- `frontend/src/components/orders/FormPreview.tsx` — Office Order + Works Order HTML previews
- `frontend/src/components/orders/OrderActions.tsx` — Approve/Edit/Reject action bar
- `frontend/src/routes/orders/index.tsx` — Orders dashboard page
- `frontend/src/routes/orders/$orderId.tsx` — Order review page
- `frontend/src/components/ui/badge.tsx` — shadcn Badge component (new)
- `frontend/src/components/ui/table.tsx` — shadcn Table component (new)
- `frontend/src/components/Layout/Header.tsx` — Added Orders navigation link
- `frontend/src/routes/index.tsx` — Redirect to /orders instead of /dashboard
- `backend/app/api/system.py` — Added GET /api/system/emails/{id} endpoint
- `docs/feature_plans/order_automation/PHASE_5_HANDOVER.md` — Handover documentation

### Phase 6
_(not started)_

### Phase 7
_(not started)_

---

## Environment / Config Changes

Track any new environment variables, dependencies, or infrastructure changes:

| Phase | Change | Notes |
|-------|--------|-------|
| 1 | 5 new PostgreSQL tables | products, manufacturing_specs, material_specs, packaging_specs, pricing |
| 1 | pytest added to container | `pip install pytest` needed in Docker for tests |
| 2 | 3 new PostgreSQL tables | incoming_emails, email_attachments, email_monitor_status |
| 2 | 3 new pip packages | google-auth, google-auth-oauthlib, google-api-python-client |
| 2 | 4 new env vars in docker-compose | GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, GMAIL_POLL_INTERVAL_SECONDS |
| 3 | 2 new PostgreSQL tables | orders, order_line_items |
| 3 | 2 new pip packages | anthropic, pdfplumber |
| 3 | 2 new env vars in docker-compose | ANTHROPIC_API_KEY, ANTHROPIC_MODEL |
| 5 | 1 new npm package | react-pdf (PDF viewer) |
| 5 | 1 new backend endpoint | GET /api/system/emails/{id} — email detail with body + attachments |

---

## How to Update This Document

At the **end of every agent session**:

1. Update the Phase Progress table (status + date)
2. Log any key decisions in the Decisions Log
3. Log any known issues
4. Add files created/modified under the relevant phase
5. Note any new env vars or dependency changes
6. Update "Last Updated" date and "Current Phase" at the top
