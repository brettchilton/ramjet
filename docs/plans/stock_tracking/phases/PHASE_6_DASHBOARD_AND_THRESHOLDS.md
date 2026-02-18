# Phase 6: Stock Dashboard & Thresholds

## 1. Overview

**Objective**: Build the stock dashboard with live levels, colour-coded thresholds, search/filter, and drill-down. Provide both the admin full dashboard and the warehouse read-only stock lookup.

**Scope**:
- Stock summary endpoint (aggregated levels per product+colour with thresholds)
- Stock item detail endpoint (individual carton + movement history)
- Threshold CRUD endpoints (admin only)
- Frontend: `/stock` — admin dashboard with colour-coded stock table
- Frontend: `/stock` — warehouse read-only stock lookup (same route, different rendering)
- Frontend: `/stock/$stockItemId` — individual carton detail + movement timeline
- Threshold editor (admin only)
- Search and filter by product, colour, status

**Does NOT include**:
- Stocktake (Phase 7)
- Reports (Phase 9)
- Raw materials (Phase 8)

**Dependencies**: Phase 3 (stock_service.py, stock items in database with movements)

---

## 2. Backend: Stock Summary Endpoint

### 2.1 Summary API

```
GET /api/stock/summary
```

**Query params:**
- `search` — filter by product code or description (optional)
- `colour` — filter by colour (optional)
- `status_filter` — filter by threshold status: `red`, `amber`, `green` (optional)

**Response:**
```json
{
  "summary": {
    "total_skus": 42,
    "total_units": 156000,
    "total_cartons": 312,
    "low_stock_count": 5
  },
  "items": [
    {
      "product_code": "LOCAP2",
      "product_description": "Louvre End Cap 152mm",
      "colour": "Black",
      "carton_count": 12,
      "total_units": 6000,
      "threshold_status": "green",
      "red_threshold": 1000,
      "amber_threshold": 3000
    }
  ]
}
```

**Implementation in `stock_service.py`:**
```python
def get_stock_summary(db: Session, search: str = None, colour: str = None) -> StockSummary:
    """
    Aggregate in_stock items by product_code + colour.
    Join with stock_thresholds to determine colour status.
    Join with products for description.
    """
```

### 2.2 Stock Item Detail

```
GET /api/stock/{stock_item_id}
```

**Response:** Full stock item details + list of all movements for that item (timeline).

### 2.3 Stock Item List

```
GET /api/stock/
```

**Query params:**
- `product_code` — filter by product
- `colour` — filter by colour
- `status` — filter by status (in_stock, picked, scrapped, consumed)
- `search` — search barcode_id

Returns paginated list of individual stock items.

---

## 3. Backend: Threshold CRUD

### 3.1 Threshold Endpoints (admin only)

```
GET    /api/stock/thresholds              — List all thresholds
POST   /api/stock/thresholds              — Create threshold
PUT    /api/stock/thresholds/{id}         — Update threshold
DELETE /api/stock/thresholds/{id}         — Delete threshold
```

**Create/Update request:**
```json
{
  "product_code": "LOCAP2",
  "colour": "Black",
  "red_threshold": 1000,
  "amber_threshold": 3000
}
```

**Colour logic (applied in summary):**
- Stock >= amber_threshold → Green
- Stock >= red_threshold but < amber_threshold → Amber
- Stock < red_threshold → Red
- No threshold configured → no colour (neutral/grey)

---

## 4. Frontend: Stock Dashboard

### 4.1 Route: `/stock`

**File:** `frontend/src/routes/stock/index.tsx`

This page renders differently based on user role:
- **Admin:** Full dashboard with summary cards, colour-coded table, threshold config, export
- **Warehouse:** Read-only stock lookup with search

### 4.2 Admin Dashboard Layout

```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  [Search products...]            [Scan] [Labels]          │
│                                                           │
│  Summary Cards:                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │ Total SKUs │ │ Total Units│ │ Low Stock  │            │
│  │    42      │ │  156,000   │ │  ●● 5      │            │
│  └────────────┘ └────────────┘ └────────────┘            │
│                                                           │
│  Stock Levels:                     [Filter ▾] [Export]    │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Product    │ Colour │ Cartons │ Units  │ Status    │   │
│  │ LOCAP2     │ Black  │ 12      │ 6,000  │ ● Green   │   │
│  │ LOCAP2     │ White  │ 3       │ 1,500  │ ● Amber   │   │
│  │ GLCAPRB    │ Black  │ 0       │ 0      │ ● Red     │   │
│  └────────────────────────────────────────────────────┘   │
│  Click row → /stock?product=LOCAP2&colour=Black           │
│  (drill down to carton list)                              │
│                                                           │
│  Threshold Configuration: (collapsible, admin only)       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Product │ Colour │ Red    │ Amber  │ Actions       │   │
│  │ LOCAP2  │ Black  │ [1000] │ [3000] │ [Save] [Del]  │   │
│  │ [Add new threshold...]                              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 4.3 Warehouse Stock Lookup Layout

```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Stock Lookup                                             │
│                                                           │
│  [Search products...]                                     │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Product    │ Colour │ Cartons │ Units  │ Status    │   │
│  │ LOCAP2     │ Black  │ 12      │ 6,000  │ ● Green   │   │
│  │ LOCAP2     │ White  │ 3       │ 1,500  │ ● Amber   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  (Read-only — no threshold config, no export)             │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 4.4 Carton Drill-Down

When a row in the stock table is clicked, show the individual cartons for that product+colour:

```
┌──────────────────────────────────────────────────────────┐
│  LOCAP2 — Black (12 cartons, 6,000 units)                │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Barcode ID                    │ Qty │ Type │ Date  │   │
│  │ RJ-LOCAP2-BLK-20260211-001   │ 500 │ Full │ Feb 11│   │
│  │ RJ-LOCAP2-BLK-20260211-002   │ 500 │ Full │ Feb 11│   │
│  │ RJ-LOCAP2-BLK-20260212-001   │ 200 │ Part │ Feb 12│   │
│  └────────────────────────────────────────────────────┘   │
│  Click row → /stock/{stockItemId}                         │
└──────────────────────────────────────────────────────────┘
```

### 4.5 Individual Carton Detail

**Route:** `/stock/$stockItemId`

**File:** `frontend/src/routes/stock/$stockItemId.tsx`

Shows full details for a single carton + movement history timeline:

```
┌──────────────────────────────────────────────────────────┐
│  RJ-LOCAP2-BLK-20260211-001                              │
│                                                           │
│  Product: LOCAP2 — Louvre End Cap 152mm                   │
│  Colour: Black                                            │
│  Quantity: 500 units                                      │
│  Box type: Full                                           │
│  Status: In Stock                                         │
│  Production date: 2026-02-11                              │
│                                                           │
│  Movement History:                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 2026-02-11 10:45  stock_in    +500   John Smith   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  [Adjust Stock] (admin only)                              │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Components

### 5.1 New Components

| Component | File | Purpose |
|-----------|------|---------|
| `StockLevelCard` | `components/stock/StockLevelCard.tsx` | Summary card (Total SKUs, Total Units, Low Stock) |
| `StockTable` | `components/stock/StockTable.tsx` | Searchable/filterable stock table with colour-coded status |
| `MovementHistory` | `components/stock/MovementHistory.tsx` | Timeline of movements for a stock item |
| `ThresholdEditor` | `components/stock/ThresholdEditor.tsx` | Inline threshold configuration (admin only) |

---

## 6. File Structure

```
backend/app/
├── services/
│   └── stock_service.py                ← MODIFY: Add get_stock_summary(), threshold logic
├── api/
│   └── stock.py                        ← MODIFY: Add summary, detail, threshold endpoints
├── schemas/
│   └── stock_schemas.py                ← MODIFY: Add summary/threshold schemas

frontend/src/
├── routes/
│   └── stock/
│       ├── index.tsx                   ← NEW: Dashboard / lookup
│       └── $stockItemId.tsx            ← NEW: Carton detail
├── components/
│   └── stock/
│       ├── StockLevelCard.tsx          ← NEW
│       ├── StockTable.tsx              ← NEW
│       ├── MovementHistory.tsx         ← NEW
│       └── ThresholdEditor.tsx         ← NEW
├── services/
│   └── stockService.ts                 ← MODIFY: Add summary, detail, threshold API calls
├── hooks/
│   └── useStock.ts                     ← MODIFY: Add useStockSummary(), useStockItem(), threshold hooks
```

---

## 7. Testing Requirements

### Unit Tests
- Stock summary aggregation correct (cartons, units, per product+colour)
- Threshold colour logic: green, amber, red, no threshold
- Threshold CRUD operations
- Search/filter on summary endpoint

### Integration Tests
- Scan in stock → dashboard shows updated levels
- Configure threshold → colour status changes
- Drill down from summary → carton list → individual carton
- Warehouse user sees read-only view (no threshold config)
- Admin user sees full dashboard

---

## 8. Exit Criteria

- [ ] Stock summary endpoint returns aggregated levels with threshold status
- [ ] Stock item detail endpoint returns item + movement history
- [ ] Threshold CRUD endpoints working (admin only)
- [ ] Admin dashboard renders with summary cards, colour-coded table, search/filter
- [ ] Warehouse read-only stock lookup works
- [ ] Drill-down from summary → carton list → individual carton
- [ ] Movement history timeline renders on carton detail page
- [ ] Threshold editor (admin only) allows inline configuration
- [ ] Search by product code/description works
- [ ] Filter by threshold status (red/amber/green) works
- [ ] Colour coding is correct (green/amber/red/neutral)

---

## 9. Handoff to Phase 7

**Artifacts provided:**
- Stock summary endpoint with threshold status
- Stock dashboard (admin + warehouse views)
- Individual carton detail with movement history
- Threshold CRUD
- Reusable StockTable and MovementHistory components

**Phase 7 will:**
- Use the stock item list to build stocktake expected items
- Reuse ScanInput component for stocktake scanning
- Build stocktake session management UI

---

*Document created: 2026-02-18*
*Status: Planning*
