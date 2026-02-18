# Phase 9: Reports & Export

## 1. Overview

**Objective**: Build report generation and spreadsheet export — stock valuation, movement history, point-in-time stock on hand, stocktake reports. All reports downloadable as Excel (.xlsx).

**Scope**:
- `services/report_service.py` — report generation logic
- `api/reports.py` — report endpoints + Excel export
- Frontend: `/reports` — report type selector, date range pickers, preview, download

**Does NOT include**:
- Raw material purchase order automation (out of scope)
- Trend analysis or forecasting (future enhancement)

**Dependencies**: Phase 6 (stock dashboard data) + Phase 8 (raw material data)

---

## 2. Report Types

### 2.1 Stock Valuation Report

Current stock × unit price, grouped by product/colour.

**Data source:** `stock_items` (status=in_stock) JOIN `pricing`

**Columns:**
| Column | Source |
|--------|--------|
| Product Code | stock_items.product_code |
| Description | products.product_description |
| Colour | stock_items.colour |
| Cartons | COUNT of in_stock items |
| Total Units | SUM of quantities |
| Unit Price | pricing.unit_price |
| Line Value | Total Units × Unit Price |
| **Total** | SUM of all line values |

### 2.2 Movement History Report

Filterable log of all stock movements.

**Filters:**
- Date range (required)
- Product code (optional)
- Colour (optional)
- Movement type (optional): stock_in, stock_out, adjustment, stocktake_verified, partial_repack

**Columns:**
| Column | Source |
|--------|--------|
| Date/Time | stock_movements.created_at |
| Barcode | stock_items.barcode_id |
| Product | stock_items.product_code |
| Colour | stock_items.colour |
| Movement Type | stock_movements.movement_type |
| Qty Change | stock_movements.quantity_change |
| Reason | stock_movements.reason |
| Performed By | users.first_name + last_name |
| Order | stock_movements.order_id |

### 2.3 Point-in-Time Stock on Hand

Stock levels as of a specified date. Replay movements to calculate.

**Input:** Target date

**Logic:**
1. Get all stock items created before target date
2. Sum movements up to target date for each item
3. Items with net positive quantity on target date = "in stock at that time"
4. Group by product + colour

**Columns:** Same as stock valuation but at the specified date.

### 2.4 Stocktake Report

Summary + detail of a completed stocktake session.

**Sections:**
- Summary: expected, found, missing, unexpected, discrepancy rate
- Missing items list
- Unexpected scans list
- Adjustments made (if auto-adjust was used)

### 2.5 Raw Material Stock Report

Current raw material levels with values.

**Columns:**
| Column | Source |
|--------|--------|
| Material Code | raw_materials.material_code |
| Name | raw_materials.material_name |
| Type | raw_materials.material_type |
| Unit | raw_materials.unit_of_measure |
| Current Stock | raw_materials.current_stock |
| Unit Cost | raw_materials.unit_cost |
| Total Value | current_stock × unit_cost |
| Status | threshold colour |

---

## 3. Report Service

### 3.1 `backend/app/services/report_service.py`

```python
def generate_stock_valuation(db: Session) -> StockValuationReport:
    """Generate current stock valuation grouped by product+colour."""

def generate_movement_history(
    db: Session,
    date_from: date,
    date_to: date,
    product_code: str | None,
    colour: str | None,
    movement_type: str | None,
) -> MovementHistoryReport:
    """Generate filterable movement history."""

def generate_stock_on_hand(db: Session, target_date: date) -> StockOnHandReport:
    """Calculate stock levels at a point in time."""

def generate_stocktake_report(db: Session, session_id: UUID) -> StocktakeReport:
    """Generate stocktake session report."""

def generate_raw_material_report(db: Session) -> RawMaterialReport:
    """Generate raw material stock report."""

def export_to_excel(report_data: dict, report_type: str) -> bytes:
    """Convert any report to .xlsx bytes using openpyxl."""
```

### 3.2 Excel Export

Use `openpyxl` (already installed — used by form_generation_service.py). Follow the same styling patterns:
- Company header row
- Report title
- Date range (if applicable)
- Column headers with blue fill
- Data rows with alternating fills
- Totals row with green fill

---

## 4. API Endpoints

### 4.1 Reports Router

**File:** `backend/app/api/reports.py`, prefix: `/api/reports`

All endpoints require admin role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stock-valuation` | Stock valuation report (JSON) |
| `GET` | `/movement-history` | Movement history with filters (JSON) |
| `GET` | `/stock-on-hand` | Point-in-time stock on hand (JSON) |
| `GET` | `/stocktake/{session_id}` | Stocktake session report (JSON) |
| `GET` | `/raw-materials` | Raw material stock report (JSON) |
| `GET` | `/export/{report_type}` | Download any report as .xlsx |

**Export endpoint params:**
- `report_type`: `stock-valuation`, `movement-history`, `stock-on-hand`, `stocktake`, `raw-materials`
- Query params same as the JSON endpoint for that report type

**Response for export:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

---

## 5. Frontend: Reports Dashboard

### 5.1 Route: `/reports`

**File:** `frontend/src/routes/reports/index.tsx`

Admin only. Report type selector with configuration options.

```
┌──────────────────────────────────────────────────────────┐
│  Reports                                                  │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Stock    │ │ Movement │ │ Stock on │ │ Stocktake│    │
│  │Valuation │ │ History  │ │ Hand     │ │ Report   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│  ┌──────────┐                                             │
│  │ Raw      │                                             │
│  │Materials │                                             │
│  └──────────┘                                             │
│                                                           │
│  Selected: Movement History                               │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Date from: [2026-01-01]  Date to: [2026-02-18]  │     │
│  │ Product:   [All              ▾]                   │     │
│  │ Type:      [All              ▾]                   │     │
│  │                                                    │     │
│  │ [Preview Report]  [Download Excel]                │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  Preview:                                                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Date     │ Barcode │ Product │ Type   │ Qty │ By  │   │
│  │ Feb 18   │ RJ-...  │ LOCAP2  │ In     │ +500│ John│   │
│  │ Feb 17   │ RJ-...  │ LOCAP2  │ Out    │ -500│ Jane│   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Components

| Component | File | Purpose |
|-----------|------|---------|
| `ReportCard` | `components/reports/ReportCard.tsx` | Clickable report type selector card |

### 5.3 Excel Download

Use the `fetch` API to download the Excel file:
```typescript
const downloadExcel = async (reportType: string, params: Record<string, string>) => {
  const query = new URLSearchParams(params).toString();
  const response = await apiClient.get(`/api/reports/export/${reportType}?${query}`, {
    responseType: 'blob',
  });
  // Trigger download via temporary anchor element
};
```

---

## 6. File Structure

```
backend/app/
├── services/
│   └── report_service.py               ← NEW
├── api/
│   └── reports.py                      ← NEW
├── schemas/
│   └── report_schemas.py               ← NEW

frontend/src/
├── routes/
│   └── reports/
│       └── index.tsx                   ← NEW
├── components/
│   └── reports/
│       └── ReportCard.tsx              ← NEW
├── services/
│   └── reportService.ts               ← NEW
├── hooks/
│   └── useReports.ts                   ← NEW
```

---

## 7. Testing Requirements

### Unit Tests
- Stock valuation calculation correct (units × price)
- Movement history filters work (date range, product, type)
- Point-in-time stock replay logic correct
- Stocktake report includes missing + unexpected
- Raw material report includes threshold status
- Excel export produces valid .xlsx file

### Integration Tests
- Generate each report type via API
- Export each report as Excel, verify file is valid
- Frontend preview renders report data
- Download button triggers file download

---

## 8. Exit Criteria

- [ ] Stock valuation report generates correctly
- [ ] Movement history report with all filters working
- [ ] Point-in-time stock on hand calculation correct
- [ ] Stocktake report includes full discrepancy detail
- [ ] Raw material report with threshold status
- [ ] All reports exportable as .xlsx
- [ ] Excel files styled consistently (headers, alternating rows, totals)
- [ ] Reports dashboard UI with report type selection
- [ ] Date range pickers and filter controls working
- [ ] Preview mode shows report data in-page
- [ ] Download button triggers .xlsx download
- [ ] All report endpoints admin-only

---

## 9. Post-Completion

This is the final phase. After completion:

- [ ] All 9 phases implemented and tested
- [ ] Full stock tracking lifecycle working end-to-end
- [ ] Demo scenario achievable: labels → scan in → verify stock → scan out → dashboard → stocktake → reports
- [ ] Update project documentation (`docs/`) to reflect stock tracking feature

---

*Document created: 2026-02-18*
*Status: Planning*
