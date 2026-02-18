# Phase 7: Stocktake Verification

## 1. Overview

**Objective**: Build the quarterly stocktake system — admin initiates sessions, warehouse scans cartons during active sessions, system detects discrepancies, admin reconciles.

**Scope**:
- `services/stocktake_service.py` — session management, scan processing, discrepancy calculation
- `api/stocktake.py` — session CRUD, scan recording, completion
- Pydantic schemas for stocktake
- Frontend: `/stock/stocktake` — session list + start new session (admin only)
- Frontend: `/stock/stocktake/$sessionId` — live scanning with progress bar, discrepancy display
- Auto-adjustment option on completion

**Does NOT include**:
- Raw materials (Phase 8)
- Reports (Phase 9 — stocktake reports built there)

**Dependencies**: Phase 6 (stock dashboard, stock item list, reusable components)

---

## 2. Stocktake Service

### 2.1 `backend/app/services/stocktake_service.py`

**Start session:**
```python
def start_session(name: str, user_id: UUID, db: Session) -> StocktakeSession:
    """
    1. Create StocktakeSession with status 'in_progress'
    2. Snapshot all in_stock items: total_expected = count of in_stock StockItems
    3. Return session
    """
```

**Process scan:**
```python
def process_stocktake_scan(
    session_id: UUID,
    barcode_id: str,
    user_id: UUID,
    db: Session
) -> StocktakeScan:
    """
    1. Validate session is 'in_progress'
    2. Look up barcode in stock_items
    3. Classify result:
       - 'found': barcode exists, status is in_stock, not already scanned in this session
       - 'not_in_system': barcode not found in stock_items
       - 'already_scanned': barcode already recorded in this session
       - 'wrong_status': barcode exists but status is not in_stock (picked, scrapped, etc.)
    4. Create StocktakeScan record
    5. Increment session.total_scanned
    6. Return scan record
    """
```

**Complete session:**
```python
def complete_session(
    session_id: UUID,
    user_id: UUID,
    auto_adjust: bool,
    db: Session
) -> StocktakeSession:
    """
    1. Calculate discrepancies:
       - Missing: in_stock items NOT scanned during session
       - Unexpected: barcodes scanned but not in system or wrong status
    2. Set total_discrepancies
    3. If auto_adjust:
       - Mark missing items as 'scrapped' with reason 'stocktake discrepancy'
       - Create adjustment movements
    4. Set session status to 'completed', completed_by, completed_at
    5. Return session with discrepancy summary
    """
```

**Get progress:**
```python
def get_session_progress(session_id: UUID, db: Session) -> SessionProgress:
    """
    Return: total_expected, total_scanned, percentage,
            scanned_items list, missing_items list (not yet scanned)
    """
```

---

## 3. API Endpoints

### 3.1 Stocktake Router

**File:** `backend/app/api/stocktake.py`, prefix: `/api/stocktake`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sessions` | admin | List all stocktake sessions |
| `GET` | `/sessions/{id}` | admin | Session detail + progress |
| `POST` | `/sessions` | admin | Start new stocktake session |
| `POST` | `/sessions/{id}/scan` | warehouse, admin | Record a scan during session |
| `POST` | `/sessions/{id}/complete` | admin | Complete session |
| `POST` | `/sessions/{id}/cancel` | admin | Cancel session |
| `GET` | `/sessions/{id}/discrepancies` | admin | Get discrepancy report |

**Start session request:**
```json
{
  "name": "Q1 2026 Stocktake"
}
```

**Scan request:**
```json
{
  "barcode_id": "RJ-LOCAP2-BLK-20260211-001"
}
```

**Scan response:**
```json
{
  "scan_result": "found",
  "stock_item": { ... },
  "session_progress": {
    "total_expected": 312,
    "total_scanned": 145,
    "percentage": 46.5
  }
}
```

**Complete request:**
```json
{
  "auto_adjust": false
}
```

**Discrepancies response:**
```json
{
  "missing_items": [
    {
      "barcode_id": "RJ-LOCAP2-BLK-20260211-005",
      "product_code": "LOCAP2",
      "colour": "Black",
      "quantity": 500,
      "last_movement": "stock_in",
      "last_movement_date": "2026-02-11T10:45:00Z"
    }
  ],
  "unexpected_scans": [
    {
      "barcode_scanned": "RJ-UNKNOWN-001",
      "scan_result": "not_in_system"
    }
  ],
  "summary": {
    "total_expected": 312,
    "total_found": 308,
    "total_missing": 4,
    "total_unexpected": 1
  }
}
```

---

## 4. Frontend: Stocktake UI

### 4.1 Session List: `/stock/stocktake`

**File:** `frontend/src/routes/stock/stocktake/index.tsx`

Admin only. Lists all stocktake sessions with status.

```
┌──────────────────────────────────────────────────────────┐
│  Stocktake Sessions                    [Start New]       │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Name           │ Status      │ Date       │ Result │   │
│  │ Q1 2026        │ Completed   │ 2026-01-15 │ 4 disc.│   │
│  │ Q4 2025        │ Completed   │ 2025-10-10 │ 0 disc.│   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Active Session: `/stock/stocktake/$sessionId`

**File:** `frontend/src/routes/stock/stocktake/$sessionId.tsx`

Admin starts the session. Warehouse + admin scan during the session.

```
┌──────────────────────────────────────────────────────────┐
│  Q1 2026 Stocktake                   [Complete] [Cancel] │
│                                                           │
│  Progress:                                                │
│  ████████████░░░░░░░░░  145 / 312 (46.5%)               │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │  [  Scan barcode...                            ]  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Last Scan: ✓ Found — LOCAP2 Black (500 units)          │
│                                                           │
│  Recent Scans:                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 10:45  RJ-LOCAP2-BLK-20260211-001  ✓ Found       │   │
│  │ 10:44  RJ-UNKNOWN-001              ✗ Not in system│   │
│  │ 10:43  RJ-LOCAP2-BLK-20260211-002  ✓ Found       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  Discrepancies (admin only, after completion):            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Missing (4):                                      │   │
│  │  RJ-LOCAP2-BLK-20260211-005 — 500 units          │   │
│  │  ...                                               │   │
│  │                                                    │   │
│  │  [Auto-Adjust Stock] [Export Discrepancy Report]   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Key behaviours:**
- Reuses `ScanInput` component from Phase 3
- Progress bar updates after each scan
- Audio/visual feedback consistent with stock scanning
- Multiple warehouse staff can scan simultaneously (concurrent sessions)
- Only admin can complete or cancel session
- Discrepancy section appears after completion

### 4.3 Components

| Component | File | Purpose |
|-----------|------|---------|
| `StocktakeProgress` | `components/stock/StocktakeProgress.tsx` | Progress bar with count and percentage |
| `DiscrepancyTable` | `components/stock/DiscrepancyTable.tsx` | Missing items + unexpected scans table |

---

## 5. File Structure

```
backend/app/
├── services/
│   └── stocktake_service.py            ← NEW
├── api/
│   └── stocktake.py                    ← NEW
├── schemas/
│   └── stocktake_schemas.py            ← NEW

frontend/src/
├── routes/
│   └── stock/
│       └── stocktake/
│           ├── index.tsx               ← NEW
│           └── $sessionId.tsx          ← NEW
├── components/
│   └── stock/
│       ├── StocktakeProgress.tsx       ← NEW
│       └── DiscrepancyTable.tsx        ← NEW
├── services/
│   └── stocktakeService.ts            ← NEW
├── hooks/
│   └── useStocktake.ts                ← NEW
```

---

## 6. Testing Requirements

### Unit Tests
- Start session snapshots correct expected count
- Scan classification: found, not_in_system, already_scanned, wrong_status
- Duplicate scan detected correctly
- Complete session calculates discrepancies
- Auto-adjust marks missing items as scrapped
- Cancel session sets status correctly

### Integration Tests
- Full stocktake flow: start → scan all → complete → zero discrepancies
- Stocktake with missing items: start → scan partial → complete → discrepancies listed
- Concurrent scanning (two scan requests to same session)
- Auto-adjust creates stock movements

---

## 7. Exit Criteria

- [ ] Stocktake session CRUD working (start, complete, cancel)
- [ ] Scan processing classifies correctly (found, not_in_system, already_scanned, wrong_status)
- [ ] Progress tracking (scanned vs expected with percentage)
- [ ] Discrepancy detection: missing items and unexpected scans
- [ ] Auto-adjust option reconciles stock
- [ ] Session list page (admin only)
- [ ] Active session page with live scanning and progress bar
- [ ] Discrepancy table renders after completion
- [ ] ScanInput component reused from Phase 3
- [ ] Audio/visual feedback consistent with stock scanning
- [ ] Multiple simultaneous scanners supported

---

## 8. Handoff to Phase 8

**Artifacts provided:**
- Stocktake service with full session lifecycle
- Stocktake API router
- Session list and active session frontend pages
- StocktakeProgress and DiscrepancyTable components

**Phase 8 will:**
- Build raw materials inventory (independent from stocktake)
- Potentially reuse colour-coded threshold pattern from stock dashboard

---

*Document created: 2026-02-18*
*Status: Planning*
