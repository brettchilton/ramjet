# Phase 3: Stock-In Scanning

## 1. Overview

**Objective**: Build the scan-in workflow — warehouse staff scan QR-labelled cartons to record them as in-stock.

**Scope**:
- `services/stock_service.py` — scan-in logic, stock item status transitions, movement recording
- Scan-in endpoint on `api/stock.py`
- Frontend: `/stock/scan` — scanning interface with "Stock In" mode
- Scanner HID integration (auto-focus, enter-key submission)
- Audio/visual feedback on scan
- Session summary (cartons scanned this session)

**Does NOT include**:
- Stock-out scanning (Phase 5)
- Partial box handling (Phase 5)
- Dashboard (Phase 6)
- Order integration (Phase 4)

**Dependencies**: Phase 2 (barcode service, StockItem records from label generation)

---

## 2. Stock Service

### 2.1 `backend/app/services/stock_service.py`

**Scan-In Logic:**

```python
def scan_in(barcode_id: str, user_id: UUID, db: Session) -> ScanResult:
    """
    Process a stock-in scan event.

    1. Look up StockItem by barcode_id
    2. Validate: item exists, status allows scan-in
    3. Update StockItem: status → 'in_stock', scanned_in_at, scanned_in_by
    4. Create StockMovement: movement_type='stock_in', quantity_change=+quantity
    5. Return result with item details
    """
```

**Status transitions:**
- `pending_scan` → `in_stock` (normal scan-in after label generation)
- Already `in_stock` → error: "Already scanned in"
- `picked` / `scrapped` / `consumed` → error: "Cannot scan in — item has been [status]"
- Barcode not found → error: "Barcode not recognised"

### 2.2 Stock Level Calculation

```python
def get_stock_levels(db: Session, product_code: str = None, colour: str = None) -> list[StockLevel]:
    """
    Calculate current stock levels by aggregating in_stock items.
    Groups by product_code + colour.
    Returns: product_code, colour, carton_count, total_units
    """
```

This function is needed by Phase 4 (verification) and Phase 6 (dashboard) but should be built now as it's foundational.

---

## 3. API Endpoint

### 3.1 Scan-In

Add to `api/stock.py`:

```
POST /api/stock/scan-in
```

**Request body:**
```json
{
  "barcode_id": "RJ-LOCAP2-BLK-20260211-001"
}
```

**Response:**
```json
{
  "success": true,
  "stock_item": {
    "id": "uuid",
    "barcode_id": "RJ-LOCAP2-BLK-20260211-001",
    "product_code": "LOCAP2",
    "product_description": "Louvre End Cap 152mm",
    "colour": "Black",
    "quantity": 500,
    "box_type": "full",
    "status": "in_stock",
    "scanned_in_at": "2026-02-11T10:45:00Z"
  },
  "message": "Scanned in: LOCAP2 Black — 500 units"
}
```

**Error response:**
```json
{
  "success": false,
  "error": "Already scanned in",
  "barcode_id": "RJ-LOCAP2-BLK-20260211-001"
}
```

**Auth:** `require_role("warehouse")` — accessible to warehouse + admin.

---

## 4. Frontend: Scanning Page

### 4.1 Route: `/stock/scan`

**File:** `frontend/src/routes/stock/scan.tsx`

This is the **home page for warehouse users**. It must be optimised for tablet use with the Bluetooth scanner.

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Scan Mode:                                               │
│  ┌──────────┐ ┌──────────┐                                │
│  │ STOCK IN │ │ STOCK OUT│                                │
│  │ (active) │ │          │                                │
│  └──────────┘ └──────────┘                                │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │  [  Scan barcode or enter manually...          ]  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Last Scan Result:                                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │  ✓ SCANNED IN                                     │     │
│  │  LOCAP2 — Louvre End Cap 152mm                    │     │
│  │  Black — 500 units — Full box                     │     │
│  │  RJ-LOCAP2-BLK-20260211-001                       │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Session Summary:                                         │
│  Scanned this session: 15 cartons (7,500 units)           │
│                                                           │
│  Recent Scans:                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 10:45  RJ-LOCAP2-BLK-20260211-001  ✓ In          │     │
│  │ 10:44  RJ-LOCAP2-BLK-20260211-002  ✓ In          │     │
│  │ 10:43  RJ-GLCAPRB-BLK-20260210-005 ✗ Not found   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Key Behaviours

**Auto-focus input:**
- Input field auto-focuses on page load
- After each scan (success or error), input clears and re-focuses
- Use `useRef` + `useEffect` for focus management
- Prevent virtual keyboard on tablet (input type considerations)

**Scanner HID integration:**
- Zebra DS22 sends QR content as keystrokes followed by Enter
- Listen for Enter key (or form submit) to trigger scan
- Debounce rapid scans (prevent double-submit)

**Audio feedback:**
- Success: short beep tone (use Web Audio API)
- Error: different error tone
- Can use simple oscillator-based tones, no audio files needed

**Visual feedback:**
- Success: green flash/border on result card
- Error: red flash/border
- Animate with CSS transitions

**Session tracking:**
- Track scans in local React state (not persisted to backend)
- Count: total cartons scanned, total units
- Recent scans list (most recent first, capped at ~20)
- Session resets on page reload

### 4.3 ScanInput Component

**File:** `frontend/src/components/stock/ScanInput.tsx`

Reusable component for all scanning modes (Stock In, Stock Out, Stocktake). Takes props:
- `onScan(barcodeId: string)` — callback when barcode submitted
- `isProcessing: boolean` — disable input during API call
- `placeholder?: string`

### 4.4 ScanResult Component

**File:** `frontend/src/components/stock/ScanResult.tsx`

Displays the result of the last scan. Takes props:
- `result: ScanResult | null` — success/error data
- Shows product details on success, error message on failure
- Green/red colour coding

---

## 5. File Structure

```
backend/app/
├── services/
│   └── stock_service.py                ← NEW
├── api/
│   └── stock.py                        ← MODIFY: Add scan-in endpoint

frontend/src/
├── routes/
│   └── stock/
│       └── scan.tsx                    ← NEW
├── components/
│   └── stock/
│       ├── ScanInput.tsx               ← NEW
│       └── ScanResult.tsx              ← NEW
├── services/
│   └── stockService.ts                 ← MODIFY: Add scanIn()
├── hooks/
│   └── useStock.ts                     ← MODIFY: Add useScanIn() mutation
├── types/
│   └── stock.ts                        ← NEW: TypeScript interfaces
```

---

## 6. Testing Requirements

### Unit Tests
- Scan-in transitions stock item from `pending_scan` to `in_stock`
- Scan-in creates a `stock_in` movement record
- Duplicate scan-in returns error
- Unknown barcode returns error
- Stock level calculation aggregates correctly

### Integration Tests
- Generate labels → scan in → verify stock levels updated
- Scan same barcode twice → second attempt returns error
- Frontend: scan input auto-focuses, form submits on Enter

---

## 7. Exit Criteria

- [ ] `stock_service.py` handles scan-in with correct status transitions
- [ ] StockMovement records created on every scan-in
- [ ] Scan-in API endpoint works correctly
- [ ] Error handling for duplicate scans, unknown barcodes
- [ ] Scanning page renders on tablet with large touch targets
- [ ] Auto-focus input works (re-focuses after each scan)
- [ ] Audio feedback on success/error
- [ ] Visual feedback (green/red) on scan result
- [ ] Session summary counts cartons and units
- [ ] Recent scans list updates in real-time
- [ ] Stock level calculation function works correctly
- [ ] Stock Out mode button visible but can be a placeholder (Phase 5)

---

## 8. Handoff to Phase 4

**Artifacts provided:**
- `stock_service.py` with scan-in logic and stock level calculation
- Scan-in endpoint on `/api/stock/scan-in`
- Scanning interface at `/stock/scan` (Stock In mode working)
- `ScanInput` and `ScanResult` reusable components
- Stock items in `in_stock` status in database

**Phase 4 will:**
- Add stock verification auto-creation when orders are created
- Build warehouse verification UI
- Modify works order generation to deduct verified stock

**Phase 5 will (can run in parallel with Phase 4):**
- Add scan-out logic to `stock_service.py`
- Add Stock Out mode to the scanning page
- Add partial box handling

---

*Document created: 2026-02-18*
*Status: Planning*
