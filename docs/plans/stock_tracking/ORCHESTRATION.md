# Stock Tracking System - Orchestration Guide

## 1. Purpose

This document coordinates the execution of all 9 phases, defining:
- Phase sequencing and dependencies
- Parallel work opportunities
- Handoff criteria between phases
- Testing gates
- Migration strategy

---

## 2. Phase Dependency Graph

```
                    ┌─────────────────────────┐
                    │       PHASE 1            │
                    │  Database & Role System   │
                    └─────────┬───────────────┘
                              │
              ┌───────────────┼───────────────────────┐
              ▼               │                       ▼
    ┌─────────────────┐       │             ┌─────────────────┐
    │    PHASE 2      │       │             │    PHASE 8      │
    │   QR Labels     │       │             │  Raw Materials   │
    └────────┬────────┘       │             └────────┬────────┘
             │                │                      │
             ▼                │                      │
    ┌─────────────────┐       │                      │
    │    PHASE 3      │       │                      │
    │  Stock-In Scan  │       │                      │
    └────────┬────────┘       │                      │
             │                │                      │
     ┌───────┼────────┐      │                      │
     ▼       │        ▼      │                      │
┌────────┐   │  ┌──────────┐ │                      │
│PHASE 4 │   │  │ PHASE 5  │ │                      │
│ Order  │   │  │ Stock-Out│ │                      │
│Integr. │   │  │& Partial │ │                      │
└────────┘   │  └──────────┘ │                      │
             │                │                      │
             ▼                │                      │
    ┌─────────────────┐       │                      │
    │    PHASE 6      │       │                      │
    │  Dashboard &    │       │                      │
    │  Thresholds     │       │                      │
    └────────┬────────┘       │                      │
             │                │                      │
             ▼                │                      │
    ┌─────────────────┐       │                      │
    │    PHASE 7      │       │                      │
    │   Stocktake     │       │                      │
    └────────┬────────┘       │                      │
             │                │                      │
             └────────────────┼──────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │       PHASE 9            │
                    │   Reports & Export       │
                    └─────────────────────────┘
```

### Dependency Matrix

| Phase | Depends On | Can Start After | Blocks |
|-------|------------|-----------------|--------|
| Phase 1 | — | Immediately | Phase 2, 3, 4, 5, 6, 7, 8 |
| Phase 2 | Phase 1 | Phase 1 complete | Phase 3 |
| Phase 3 | Phase 2 | Phase 2 complete | Phase 4, 5, 6 |
| Phase 4 | Phase 3 | Phase 3 complete | — |
| Phase 5 | Phase 3 | Phase 3 complete | — |
| Phase 6 | Phase 3 | Phase 3 complete | Phase 7 |
| Phase 7 | Phase 6 | Phase 6 complete | Phase 9 |
| Phase 8 | Phase 1 | Phase 1 complete | Phase 9 |
| Phase 9 | Phase 6 + Phase 8 | Both Phase 6 and Phase 8 complete | — |

---

## 3. Parallel Work Opportunities

After Phase 1 completes, two independent tracks open:

**Track A (Main): Finished Goods**
```
Phase 2 → Phase 3 → Phase 4 (can parallel Phase 5) → Phase 6 → Phase 7
```

**Track B (Independent): Raw Materials**
```
Phase 8 (can start immediately after Phase 1)
```

**Specific parallel opportunities:**
- **Phase 4 and Phase 5** can run in parallel after Phase 3 (both extend stock_service.py but touch different functions)
- **Phase 8** can run in parallel with Phases 2-7 (completely independent domain)
- **Phase 9** requires both Track A (Phase 6+7) and Track B (Phase 8) to complete

---

## 4. Phase Handoff Criteria

### Phase 1 → Phase 2

**Exit Criteria for Phase 1:**
- [ ] All 8 SQLAlchemy models defined and importable
- [ ] `is_stockable` field on Product model
- [ ] Alembic migration runs cleanly (up + down)
- [ ] Product CRUD endpoints working (POST, PUT, DELETE)
- [ ] `require_role("warehouse")` tested
- [ ] Header renders role-conditional navigation
- [ ] New routers registered in main.py (even if empty stubs)

**Handoff Artifacts:**
- All models in `backend/app/core/models.py`
- Migration in `backend/migrations/versions/`
- Product CRUD in `backend/app/api/products.py`
- Role-conditional nav in `frontend/src/components/Layout/Header.tsx`

---

### Phase 2 → Phase 3

**Exit Criteria for Phase 2:**
- [ ] Barcode service generates unique IDs in correct format
- [ ] QR codes scannable by Zebra DS22
- [ ] PDF labels render correctly (pink/yellow differentiation)
- [ ] API endpoint returns valid PDF
- [ ] Frontend label page works on tablet
- [ ] StockItem records created in DB for generated labels

**Handoff Artifacts:**
- `backend/app/services/barcode_service.py`
- Label endpoint on `backend/app/api/stock.py`
- Frontend at `/stock/labels`
- StockItem records in database (status: pending_scan)

---

### Phase 3 → Phase 4, 5, 6

**Exit Criteria for Phase 3:**
- [ ] Scan-in transitions items from pending_scan to in_stock
- [ ] StockMovement records created on every scan
- [ ] Scanning page works on tablet with auto-focus
- [ ] Audio/visual feedback functional
- [ ] Stock level calculation function works
- [ ] ScanInput + ScanResult components reusable

**Handoff Artifacts:**
- `backend/app/services/stock_service.py` with scan_in() and get_stock_levels()
- Scan-in endpoint on `/api/stock/scan-in`
- `/stock/scan` page with Stock In mode
- Reusable ScanInput and ScanResult components

---

### Phase 4 (Exit)

**Exit Criteria for Phase 4:**
- [ ] StockVerification auto-created on order creation
- [ ] Warehouse can view and confirm verifications
- [ ] Works orders generate only when approved AND verified
- [ ] WO quantity = ordered - verified stock
- [ ] Integration with existing order flow seamless

**Handoff Artifacts:**
- `backend/app/services/stock_verification_service.py`
- Verification endpoints
- Modified `orders.py` and `form_generation_service.py`
- Verification UI at `/stock/verification`

---

### Phase 5 (Exit)

**Exit Criteria for Phase 5:**
- [ ] Scan-out transitions in_stock → picked
- [ ] Partial repack creates new item with correct quantity
- [ ] Yellow label generated for partial boxes
- [ ] Stock Out mode on scanning page functional
- [ ] Order linking on scan-out works

**Handoff Artifacts:**
- `scan_out()` and `partial_repack()` in stock_service.py
- Stock Out mode on scanning page

---

### Phase 6 → Phase 7

**Exit Criteria for Phase 6:**
- [ ] Stock summary endpoint with threshold status
- [ ] Admin dashboard with colour-coded table
- [ ] Warehouse read-only stock lookup
- [ ] Threshold CRUD working (admin only)
- [ ] Drill-down to carton level
- [ ] Movement history on carton detail

**Handoff Artifacts:**
- Summary and detail endpoints
- Dashboard and detail frontend pages
- StockTable, MovementHistory, ThresholdEditor components

---

### Phase 7 (Exit)

**Exit Criteria for Phase 7:**
- [ ] Stocktake session lifecycle (start, scan, complete, cancel)
- [ ] Scan classification correct
- [ ] Discrepancy detection working
- [ ] Auto-adjust option functional
- [ ] Session UI with progress bar

---

### Phase 8 (Exit)

**Exit Criteria for Phase 8:**
- [ ] Raw material CRUD working
- [ ] Receive/use/adjust operations correct
- [ ] current_stock calculated correctly
- [ ] Colour-coded thresholds
- [ ] Movement history on detail page

---

### Phase 9 (Exit — Final)

**Exit Criteria for Phase 9:**
- [ ] All 5 report types generate correctly
- [ ] All reports exportable as .xlsx
- [ ] Reports dashboard UI functional
- [ ] Excel files styled consistently

---

## 5. Testing Strategy

### Unit Tests (Per Phase)

| Phase | Test Focus |
|-------|------------|
| 1 | Model creation, migration, role guards, product CRUD |
| 2 | Barcode ID generation, QR encoding, PDF rendering |
| 3 | Scan-in status transitions, movement recording, stock levels |
| 4 | Verification creation, confirmation, WO generation trigger, quantity adjustment |
| 5 | Scan-out transitions, partial repack logic, label generation |
| 6 | Summary aggregation, threshold logic, search/filter |
| 7 | Session lifecycle, scan classification, discrepancy calculation |
| 8 | Raw material CRUD, receive/use/adjust, stock calculation |
| 9 | Report generation, Excel export, date-based calculations |

### Integration Tests

| Test | Phases | Description |
|------|--------|-------------|
| Full stock lifecycle | 2, 3, 5 | Generate labels → scan in → scan out → verify levels |
| Order integration | 3, 4 | Create order → verify stock → approve → WO with adjusted qty |
| Partial box flow | 3, 5 | Scan in → partial repack → verify new item + yellow label |
| Stocktake flow | 3, 7 | Scan in stock → start stocktake → scan → complete → check discrepancies |
| Raw material lifecycle | 8 | Create material → receive → use → check levels |
| Report accuracy | 3, 5, 9 | Perform stock operations → generate reports → verify data matches |

### End-to-End Demo Test

After all phases, run the full demo scenario:
1. Generate labels for LOCAP2 Black (20 cartons × 500 units)
2. Scan all 20 cartons in
3. Dashboard shows 10,000 units green
4. Order arrives for 12,000 units
5. Verification task created (system stock: 10,000)
6. Warehouse confirms 10,000
7. Sharon approves order
8. Works order generates for 2,000 units (12,000 - 10,000)
9. After production, scan out 20 cartons for the original 10,000
10. Scan out 4 new cartons for the produced 2,000
11. Dashboard shows 0 units
12. Receive raw materials
13. Run quarterly stocktake
14. Generate reports and export

---

## 6. Migration Strategy

### Database Migration
- Single Alembic migration in Phase 1 creates all tables
- Subsequent phases do NOT add new migrations unless schema changes are needed
- If a phase needs to modify the schema (unlikely), create a new migration
- Always test migration up AND down

### Data Migration
- No existing data to migrate — this is a new feature
- Products table gets `is_stockable=true` for all existing products (default)

### Rollback Plan
- Each phase is independently revertable via `alembic downgrade`
- Frontend routes can be removed without affecting existing functionality
- New API routers are additive — removing them doesn't break existing endpoints

---

## 7. Handover Document Template

Each phase produces a handover document at `handovers/handover-phase-N.md`:

```markdown
# Phase N Handover: [Phase Name]

## Completion Status
- Date completed: YYYY-MM-DD
- All exit criteria met: Yes / No (list exceptions)

## What Was Built
- [List of files created/modified with brief description]

## Key Implementation Details
- [Important patterns or decisions made during implementation]
- [Anything that deviated from the phase doc and why]

## State of the Codebase
- [What works]
- [Known issues or technical debt introduced]

## For the Next Phase
- [Specific context the next phase agent needs]
- [Any prerequisites that should be verified before starting]

## Test Results
- [What was tested and outcomes]
```

---

## 8. Success Criteria (Overall)

### Must Have
- [ ] All 8 database tables created and functional
- [ ] Warehouse and admin roles working with correct access control
- [ ] Label generation produces scannable QR codes
- [ ] Stock-in and stock-out scanning works on tablet with Bluetooth scanner
- [ ] Stock verification runs in parallel with order approval
- [ ] Works order quantities adjusted for verified stock
- [ ] Stock dashboard with colour-coded thresholds
- [ ] Stocktake session lifecycle complete
- [ ] Raw material CRUD + receive/use operations
- [ ] All reports generate and export as Excel

### Should Have
- [ ] Audio feedback on scan (success/error tones)
- [ ] Partial box handling with yellow label generation
- [ ] Point-in-time stock on hand report
- [ ] Movement history filtering by all parameters
- [ ] Carton-level drill-down from dashboard

### Nice to Have
- [ ] Scan session summary (count/units per session)
- [ ] Report preview before download
- [ ] Search across barcode IDs

---

*Document created: 2026-02-18*
*Status: Planning*
