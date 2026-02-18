# Phase 5: Stock-Out Scanning & Partial Boxes

## 1. Overview

**Objective**: Enable scanning cartons out of stock for order fulfilment, including partial box handling (split, re-label, scan remainder back in).

**Scope**:
- Scan-out logic in `stock_service.py`
- Partial repack logic (consume original, create new partial with yellow label)
- Scan-out and partial-repack endpoints on `api/stock.py`
- "Stock Out" mode on scanning page
- Order linking during scan-out
- Yellow label generation for partial boxes

**Does NOT include**:
- Dashboard (Phase 6)
- Stocktake (Phase 7)
- Reports (Phase 9)

**Dependencies**: Phase 3 (stock_service.py, scanning interface, ScanInput component)

---

## 2. Stock-Out Logic

### 2.1 Scan-Out in `stock_service.py`

```python
def scan_out(
    barcode_id: str,
    user_id: UUID,
    order_id: UUID | None,
    db: Session
) -> ScanResult:
    """
    Process a stock-out scan event.

    1. Look up StockItem by barcode_id
    2. Validate: status must be 'in_stock'
    3. Update StockItem: status → 'picked', scanned_out_at, scanned_out_by, order_id
    4. Create StockMovement: movement_type='stock_out', quantity_change=-quantity
    5. Return result with item details
    """
```

**Status transitions:**
- `in_stock` → `picked` (normal scan-out)
- `pending_scan` → error: "Item not yet scanned in"
- `picked` → error: "Already scanned out"
- `scrapped` / `consumed` → error: "Cannot scan out"
- Barcode not found → error: "Barcode not recognised"

### 2.2 Partial Repack Logic

When picking an order, sometimes only part of a carton is needed. The flow:

```python
def partial_repack(
    barcode_id: str,
    units_taken: int,
    user_id: UUID,
    order_id: UUID | None,
    db: Session
) -> PartialRepackResult:
    """
    Handle partial box scenario.

    1. Look up original StockItem by barcode_id
    2. Validate: status must be 'in_stock', units_taken < quantity
    3. Mark original as 'consumed'
    4. Create StockMovement for original: movement_type='partial_repack', quantity_change=-quantity
    5. Create new StockItem for remainder:
       - New barcode_id (generate via barcode_service)
       - quantity = original.quantity - units_taken
       - box_type = 'partial'
       - status = 'in_stock'
       - parent_stock_item_id = original.id
    6. Create StockMovement for new partial: movement_type='stock_in', quantity_change=+remainder
    7. Generate yellow label PDF for new partial
    8. Return: new partial item details + label PDF URL
    """
```

---

## 3. API Endpoints

### 3.1 Scan-Out

```
POST /api/stock/scan-out
```

**Request:**
```json
{
  "barcode_id": "RJ-LOCAP2-BLK-20260211-001",
  "order_id": "uuid-optional"
}
```

**Response:**
```json
{
  "success": true,
  "stock_item": {
    "barcode_id": "RJ-LOCAP2-BLK-20260211-001",
    "product_code": "LOCAP2",
    "colour": "Black",
    "quantity": 500,
    "status": "picked"
  },
  "message": "Scanned out: LOCAP2 Black — 500 units"
}
```

### 3.2 Partial Repack

```
POST /api/stock/partial-repack
```

**Request:**
```json
{
  "barcode_id": "RJ-LOCAP2-BLK-20260211-001",
  "units_taken": 300,
  "order_id": "uuid-optional"
}
```

**Response:**
```json
{
  "success": true,
  "original_item": {
    "barcode_id": "RJ-LOCAP2-BLK-20260211-001",
    "status": "consumed",
    "quantity": 500
  },
  "new_partial_item": {
    "barcode_id": "RJ-LOCAP2-BLK-20260211-015",
    "quantity": 200,
    "box_type": "partial",
    "status": "in_stock"
  },
  "units_taken": 300,
  "units_remaining": 200,
  "label_url": "/api/stock/labels/single/RJ-LOCAP2-BLK-20260211-015",
  "message": "Partial repack: 300 taken, 200 remaining. Print yellow label."
}
```

### 3.3 Single Label Download

```
GET /api/stock/labels/single/{barcode_id}
```

Returns a single-label PDF for printing (used after partial repack).

---

## 4. Frontend: Stock Out Mode

### 4.1 Scanning Page Updates

**File:** `frontend/src/routes/stock/scan.tsx`

Add "Stock Out" mode to the existing scanning page:

**Mode selection:** Two large buttons at the top — "STOCK IN" and "STOCK OUT". Active mode highlighted.

**Stock Out mode behaviour:**
1. Optional: select an order to link scan-out against
   - Dropdown of orders with status `works_order_generated`
   - "No order" option for ad-hoc stock-out
2. Scan barcode → API call to `/api/stock/scan-out`
3. On success: show green result card
4. **Partial box prompt:** After a successful scan-out, show a "Partial box?" button
   - If tapped: prompt for units taken (number input)
   - Submit → API call to `/api/stock/partial-repack`
   - On success: show yellow result card with "Print Label" button
   - Print Label → downloads single yellow label PDF

**Layout addition for partial flow:**
```
┌──────────────────────────────────────────────────┐
│  ✓ SCANNED OUT                                    │
│  LOCAP2 — Black — 500 units                      │
│                                                    │
│  [Partial Box? Only took some units]              │
│                                                    │
│  ┌── Partial Box ──────────────────────────────┐  │
│  │  Units taken from this box: [300       ]    │  │
│  │  Remaining: 200 units                       │  │
│  │  [Confirm Partial]                          │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ✓ PARTIAL REPACK COMPLETE                        │
│  New label: RJ-LOCAP2-BLK-20260211-015           │
│  200 units remaining — PARTIAL BOX                │
│  [Print Yellow Label]                             │
└──────────────────────────────────────────────────┘
```

---

## 5. File Structure

```
backend/app/
├── services/
│   └── stock_service.py                ← MODIFY: Add scan_out(), partial_repack()
├── api/
│   └── stock.py                        ← MODIFY: Add scan-out, partial-repack, single-label endpoints
├── schemas/
│   └── stock_schemas.py                ← MODIFY: Add ScanOutRequest, PartialRepackRequest/Response

frontend/src/
├── routes/
│   └── stock/
│       └── scan.tsx                    ← MODIFY: Add Stock Out mode + partial box flow
├── services/
│   └── stockService.ts                 ← MODIFY: Add scanOut(), partialRepack()
├── hooks/
│   └── useStock.ts                     ← MODIFY: Add useScanOut(), usePartialRepack() mutations
```

---

## 6. Testing Requirements

### Unit Tests
- Scan-out transitions `in_stock` → `picked`
- Scan-out creates `stock_out` movement with negative quantity
- Scan-out with order_id links stock item to order
- Partial repack: original → consumed, new partial → in_stock
- Partial repack: correct quantity split
- Partial repack: new barcode generated
- Partial repack: parent_stock_item_id set correctly
- Error: scan-out on non-in_stock item
- Error: partial repack with units_taken >= quantity

### Integration Tests
- Full flow: scan in → scan out → verify stock level reduced
- Full flow: scan in → partial repack → verify two movements + new item
- Yellow label PDF generated for partial box
- Frontend: Stock Out mode → scan → partial prompt → confirm → print label

---

## 7. Exit Criteria

- [ ] Scan-out endpoint working (barcode → picked)
- [ ] StockMovement created for every scan-out
- [ ] Order linking on scan-out works
- [ ] Partial repack creates new stock item with correct quantity
- [ ] Partial repack generates yellow label
- [ ] Original carton marked as consumed after partial repack
- [ ] Single-label download endpoint works
- [ ] Stock Out mode on scanning page functional
- [ ] Partial box flow (prompt → confirm → print label) works on tablet
- [ ] Stock levels correctly updated after scan-out and partial repack
- [ ] Audio/visual feedback consistent with Stock In mode

---

## 8. Handoff to Phase 6

**Artifacts provided:**
- `scan_out()` and `partial_repack()` in `stock_service.py`
- Scan-out and partial-repack endpoints on `/api/stock`
- Single-label download endpoint
- Stock Out mode on scanning page with partial box flow
- Complete stock in/out lifecycle working

**Phase 6 will:**
- Build stock dashboard with aggregated levels
- Add threshold configuration
- Build warehouse read-only stock lookup

---

*Document created: 2026-02-18*
*Status: Planning*
