# Stock Tracking System - Agent Prompts

## Purpose

Ready-to-use prompts for each implementation phase. Copy-paste the relevant prompt to start a new agent session for that phase.

Each prompt tells the agent to:
1. Read the master plan and orchestration guide
2. Read the phase-specific document
3. Read the previous phase's handover document (if not Phase 1)
4. Implement the phase following exit criteria
5. Create a handover document when done

---

## Phase 1: Database Models & Role System

```
You are implementing Phase 1 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — full system architecture and data model
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_1_DATABASE_AND_ROLES.md` — your implementation spec

**Reference files to read before coding:**
- `backend/app/core/models.py` — existing SQLAlchemy models (add new models here)
- `backend/app/core/auth.py` — existing role-based auth (require_role at line 170)
- `backend/app/api/products.py` — existing read-only product endpoints (add CRUD)
- `backend/app/schemas/order_schemas.py` — Pydantic schema patterns to follow
- `frontend/src/components/Layout/Header.tsx` — current nav (make role-conditional)
- `frontend/src/hooks/useUnifiedAuth.tsx` — user.role is available here
- `frontend/src/contexts/SimpleAuthContext.tsx` — auth context with user object

**Your task:**
1. Add all 8 new SQLAlchemy models to `backend/app/core/models.py` (StockItem, StockMovement, StockThreshold, StockVerification, StocktakeSession, StocktakeScan, RawMaterial, RawMaterialMovement)
2. Add `is_stockable = Column(Boolean, default=True)` to the Product model
3. Create Alembic migration: `docker-compose exec backend alembic revision --autogenerate -m "add_stock_tracking_tables"`
4. Run migration: `docker-compose exec backend alembic upgrade head`
5. Add Product CRUD endpoints (POST, PUT, DELETE) to `backend/app/api/products.py` with `require_role("admin")`
6. Create `backend/app/schemas/stock_schemas.py` with Pydantic models for stock entities
7. Create stub routers in `backend/app/api/` (stock.py, stock_verification.py, raw_materials.py, stocktake.py, reports.py) and register in `backend/app/main.py`
8. Modify `frontend/src/components/Layout/Header.tsx` to render navigation based on `user.role`
9. Test: migration runs cleanly, product CRUD works, role-conditional nav renders correctly

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-1.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 2: QR Code Generation & Labels

```
You are implementing Phase 2 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — full system architecture
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_2_QR_LABELS.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-1.md` — what Phase 1 built

**Reference files to read before coding:**
- `backend/app/core/models.py` — StockItem model (created in Phase 1)
- `backend/app/api/stock.py` — stub router (created in Phase 1, add label endpoint)
- `backend/app/services/form_generation_service.py` — PDF generation patterns with openpyxl/reportlab
- `frontend/src/routes/orders/$orderId.tsx` — route pattern to follow
- `frontend/src/hooks/useOrders.ts` — React Query hook pattern
- `frontend/src/services/orderService.ts` — API service pattern

**Your task:**
1. Create `backend/app/services/barcode_service.py` — QR generation, unique barcode ID sequencing, label PDF rendering
2. Add label generation endpoint to `backend/app/api/stock.py`: `POST /api/stock/labels/generate`
3. Create `frontend/src/routes/stock/labels.tsx` — label generation form (product/colour dropdowns, quantity, box type)
4. Create `frontend/src/services/stockService.ts` and `frontend/src/hooks/useStock.ts`
5. Install backend dependencies: `qrcode[pil]`, `Pillow`, `reportlab`
6. Test: generate labels → verify QR codes contain correct barcode IDs → verify PDF renders correctly

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-2.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 3: Stock-In Scanning

```
You are implementing Phase 3 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — full system architecture
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_3_STOCK_IN_SCANNING.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-2.md` — what Phase 2 built

**Reference files to read before coding:**
- `backend/app/core/models.py` — StockItem, StockMovement models
- `backend/app/api/stock.py` — existing stock router (add scan-in endpoint)
- `backend/app/services/barcode_service.py` — barcode service from Phase 2
- `frontend/src/routes/stock/labels.tsx` — Phase 2 route pattern
- `frontend/src/hooks/useOrders.ts` — React Query mutation patterns
- `frontend/src/services/orderService.ts` — API service patterns

**Your task:**
1. Create `backend/app/services/stock_service.py` — scan_in() logic, status transitions, stock level calculation
2. Add scan-in endpoint to `backend/app/api/stock.py`: `POST /api/stock/scan-in`
3. Create `frontend/src/routes/stock/scan.tsx` — scanning interface with "Stock In" mode
4. Create `frontend/src/components/stock/ScanInput.tsx` — reusable auto-focused scanner input
5. Create `frontend/src/components/stock/ScanResult.tsx` — success/error result display
6. Add audio feedback (Web Audio API — success beep, error tone)
7. Add TypeScript interfaces in `frontend/src/types/stock.ts`
8. Test: generate labels (Phase 2) → scan in → verify stock levels update → verify movements recorded

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-3.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 4: Order Integration & Stock Verification

```
You are implementing Phase 4 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

This is the most architecturally significant phase. Read the master plan's order integration flow (Section 2.2) carefully.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — especially Section 2.2 (Order Integration Flow) and Section 7.2
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_4_ORDER_INTEGRATION.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-3.md` — what Phase 3 built

**Reference files to read before coding:**
- `backend/app/api/orders.py` — existing order endpoints (modify approve_order)
- `backend/app/services/form_generation_service.py` — works order generation (modify for adjusted quantity)
- `backend/app/services/extraction_service.py` — where orders are created (hook verification creation)
- `backend/app/services/stock_service.py` — get_stock_levels() from Phase 3
- `backend/app/core/models.py` — StockVerification model, Order model
- `frontend/src/routes/orders/$orderId.tsx` — order review page pattern
- `frontend/src/hooks/useOrders.ts` — React Query patterns

**Your task:**
1. Create `backend/app/services/stock_verification_service.py` — auto-create verifications, confirm, trigger WO generation
2. Create `backend/app/api/stock_verification.py` with endpoints: GET /pending, GET /order/{id}, POST /{id}/confirm
3. Modify `backend/app/api/orders.py` approve_order() — check verifications before generating WOs
4. Modify `backend/app/services/form_generation_service.py` — accept adjusted_quantity parameter
5. Hook verification creation into order processing (after line items created + products matched)
6. Create `frontend/src/routes/stock/verification.tsx` — warehouse verification UI
7. Create service + hooks for verification API calls
8. Test: full flow — create order → verify stock → approve → WO with adjusted qty

**Critical:** The order approval and stock verification run in PARALLEL. Works orders generate only when BOTH are complete.

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-4.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 5: Stock-Out Scanning & Partial Boxes

```
You are implementing Phase 5 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — Section 7.3 (Stock Out flow)
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_5_STOCK_OUT_AND_PARTIAL.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-3.md` — what Phase 3 built (scan page, ScanInput component)

**Reference files to read before coding:**
- `backend/app/services/stock_service.py` — add scan_out() and partial_repack()
- `backend/app/services/barcode_service.py` — generate labels for partial boxes
- `backend/app/api/stock.py` — add scan-out and partial-repack endpoints
- `frontend/src/routes/stock/scan.tsx` — add Stock Out mode to existing scan page
- `frontend/src/components/stock/ScanInput.tsx` — reusable component from Phase 3

**Your task:**
1. Add `scan_out()` to `backend/app/services/stock_service.py` — status transitions, movement recording, order linking
2. Add `partial_repack()` to `backend/app/services/stock_service.py` — consume original, create partial, yellow label
3. Add endpoints to `backend/app/api/stock.py`: POST /scan-out, POST /partial-repack, GET /labels/single/{barcode_id}
4. Add "Stock Out" mode to `frontend/src/routes/stock/scan.tsx` with mode toggle
5. Add partial box flow: scan out → "Partial box?" prompt → quantity input → confirm → print yellow label
6. Test: scan in → scan out → verify stock level reduced; scan in → partial repack → verify new item created

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-5.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 6: Stock Dashboard & Thresholds

```
You are implementing Phase 6 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — Section 3 (Role System), Section 6.2 (Role-Based Navigation)
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_6_DASHBOARD_AND_THRESHOLDS.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-3.md` — what Phase 3 built

Note: Also read Phase 5 handover if available, but Phase 5 is not a strict dependency.

**Reference files to read before coding:**
- `backend/app/services/stock_service.py` — get_stock_levels() from Phase 3
- `backend/app/core/models.py` — StockThreshold model
- `frontend/src/routes/orders/$orderId.tsx` — page pattern to follow
- `frontend/src/hooks/useOrders.ts` — React Query hook patterns
- `frontend/src/components/Layout/Header.tsx` — role-conditional nav from Phase 1

**Your task:**
1. Add stock summary endpoint to `backend/app/api/stock.py`: GET /summary (with search/filter)
2. Add stock item detail endpoint: GET /{stock_item_id}
3. Add stock item list endpoint: GET / (with filters)
4. Add threshold CRUD endpoints: GET/POST/PUT/DELETE /thresholds
5. Create `frontend/src/routes/stock/index.tsx` — admin dashboard + warehouse read-only lookup
6. Create `frontend/src/routes/stock/$stockItemId.tsx` — carton detail with movement history
7. Create components: StockLevelCard, StockTable, MovementHistory, ThresholdEditor
8. Test: scan in stock → dashboard shows levels → configure thresholds → colours update → drill down to carton

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-6.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 7: Stocktake Verification

```
You are implementing Phase 7 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — Section 7.5 (Quarterly Stocktake flow)
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and handoff criteria
3. `docs/plans/stock_tracking/phases/PHASE_7_STOCKTAKE.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-6.md` — what Phase 6 built

**Reference files to read before coding:**
- `backend/app/core/models.py` — StocktakeSession, StocktakeScan models
- `backend/app/services/stock_service.py` — stock item queries, movement creation
- `frontend/src/components/stock/ScanInput.tsx` — reuse for stocktake scanning
- `frontend/src/routes/stock/scan.tsx` — scanning page patterns

**Your task:**
1. Create `backend/app/services/stocktake_service.py` — session management, scan processing, discrepancy calculation
2. Create `backend/app/api/stocktake.py` — session CRUD, scan recording, completion
3. Create `backend/app/schemas/stocktake_schemas.py`
4. Create `frontend/src/routes/stock/stocktake/index.tsx` — session list (admin only)
5. Create `frontend/src/routes/stock/stocktake/$sessionId.tsx` — active session with scanning + progress
6. Create components: StocktakeProgress, DiscrepancyTable
7. Create service + hooks for stocktake API calls
8. Test: start session → scan items → complete → verify discrepancies detected → test auto-adjust

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-7.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 8: Raw Materials

```
You are implementing Phase 8 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

Note: This phase can be built in parallel with Phases 3-7. It only depends on Phase 1.

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — Section 4.1 (raw_materials and raw_material_movements tables)
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies
3. `docs/plans/stock_tracking/phases/PHASE_8_RAW_MATERIALS.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-1.md` — what Phase 1 built (models, role guards)

**Reference files to read before coding:**
- `backend/app/core/models.py` — RawMaterial, RawMaterialMovement models from Phase 1
- `backend/app/api/products.py` — CRUD endpoint patterns from Phase 1
- `backend/app/schemas/stock_schemas.py` — Pydantic schema patterns
- `frontend/src/routes/orders/$orderId.tsx` — detail page pattern
- `frontend/src/hooks/useOrders.ts` — React Query patterns
- `frontend/src/services/orderService.ts` — API service patterns

**Your task:**
1. Create `backend/app/services/raw_material_service.py` — receive, use, adjust, stock levels
2. Create `backend/app/api/raw_materials.py` — full CRUD + movement endpoints (admin only)
3. Create `backend/app/schemas/raw_material_schemas.py`
4. Create `frontend/src/routes/raw-materials/index.tsx` — list with colour-coded levels
5. Create `frontend/src/routes/raw-materials/$materialId.tsx` — detail + movement history
6. Create components: RawMaterialTable, ReceiveForm, UsageForm
7. Create service + hooks for raw material API calls
8. Create TypeScript interfaces in `frontend/src/types/rawMaterials.ts`
9. Test: create material → receive delivery → record usage → verify stock level → check thresholds

**When complete:** Create handover at `docs/plans/stock_tracking/handovers/handover-phase-8.md`. Use the template in ORCHESTRATION.md section 7.
```

---

## Phase 9: Reports & Export

```
You are implementing Phase 9 of the Stock Tracking System for Ramjet Plastics. Do NOT enter plan mode — proceed directly to implementation.

This is the final phase. It depends on both Phase 6 (stock dashboard data) and Phase 8 (raw material data).

**Read these documents in order:**
1. `docs/plans/stock_tracking/MASTER_PLAN.md` — overall architecture
2. `docs/plans/stock_tracking/ORCHESTRATION.md` — phase dependencies and overall success criteria
3. `docs/plans/stock_tracking/phases/PHASE_9_REPORTS.md` — your implementation spec
4. `docs/plans/stock_tracking/handovers/handover-phase-6.md` — stock dashboard context
5. `docs/plans/stock_tracking/handovers/handover-phase-8.md` — raw material context

**Reference files to read before coding:**
- `backend/app/services/form_generation_service.py` — openpyxl styling patterns (reuse _HEADER_FONT, _HEADER_FILL, etc.)
- `backend/app/services/stock_service.py` — stock level queries
- `backend/app/services/raw_material_service.py` — raw material queries
- `backend/app/services/stocktake_service.py` — stocktake data
- `frontend/src/hooks/useOrders.ts` — React Query patterns

**Your task:**
1. Create `backend/app/services/report_service.py` — all 5 report generators + Excel export
2. Create `backend/app/api/reports.py` — report endpoints (JSON) + export endpoint (.xlsx)
3. Create `backend/app/schemas/report_schemas.py`
4. Create `frontend/src/routes/reports/index.tsx` — report type selector, filters, preview, download
5. Create components: ReportCard
6. Create service + hooks for report API calls
7. Reuse openpyxl styling from form_generation_service.py for consistent Excel appearance
8. Test: generate each report type → verify data accuracy → export as Excel → verify file is valid

**When complete:**
1. Create handover at `docs/plans/stock_tracking/handovers/handover-phase-9.md`
2. This is the final phase — verify the full demo scenario from ORCHESTRATION.md Section 5 works end-to-end
3. Ask if the user wants `docs/` updated to reflect the stock tracking feature
```

---

## Usage Notes

1. **Start each session fresh.** Each prompt is self-contained — the agent reads the docs, not memory.
2. **Handover documents are critical.** They're the bridge between phases. Each agent must create one.
3. **Exit criteria are the definition of done.** Don't mark complete until all boxes are checked.
4. **Read the reference files.** They contain patterns to follow — don't invent new patterns.
5. **Parallel opportunities:** Phase 8 can run alongside Phases 3-7. Phase 4 and Phase 5 can run in parallel after Phase 3.
6. **Phase 4 is the hardest.** It modifies existing order flow. Test thoroughly.
