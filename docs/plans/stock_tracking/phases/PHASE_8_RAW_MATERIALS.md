# Phase 8: Raw Materials

## 1. Overview

**Objective**: Build raw material inventory management — admin-only CRUD, receive deliveries, record usage, manual adjustments, colour-coded stock levels with thresholds.

**Scope**:
- `services/raw_material_service.py` — receive, use, adjust, stock level calculation
- `api/raw_materials.py` — full CRUD + movement endpoints
- Pydantic schemas for raw materials
- Frontend: `/raw-materials` — list with colour-coded levels, CRUD, receive/use forms
- Frontend: `/raw-materials/$materialId` — detail + movement history

**Does NOT include**:
- Automatic raw material deduction against works orders (out of scope entirely)
- Raw material assignment to production runs (out of scope entirely)
- Reports (Phase 9)

**Dependencies**: Phase 1 (RawMaterial and RawMaterialMovement models, role guards)

Note: This phase can be built **in parallel** with Phases 3-7 since it only depends on Phase 1's database models.

---

## 2. Raw Material Service

### 2.1 `backend/app/services/raw_material_service.py`

**Receive delivery:**
```python
def receive_delivery(
    material_id: UUID,
    quantity: Decimal,
    supplier: str | None,
    delivery_note: str | None,
    unit_cost: Decimal | None,
    user_id: UUID,
    db: Session
) -> RawMaterialMovement:
    """
    1. Create RawMaterialMovement: type='received', quantity=+qty
    2. Update RawMaterial.current_stock += quantity
    3. If unit_cost provided, update RawMaterial.unit_cost
    4. Return movement record
    """
```

**Record usage:**
```python
def record_usage(
    material_id: UUID,
    quantity: Decimal,
    reason: str | None,
    user_id: UUID,
    db: Session
) -> RawMaterialMovement:
    """
    1. Validate: quantity <= current_stock (cannot go negative)
    2. Create RawMaterialMovement: type='used', quantity=-qty
    3. Update RawMaterial.current_stock -= quantity
    4. Return movement record
    """
```

**Manual adjustment:**
```python
def adjust_stock(
    material_id: UUID,
    quantity: Decimal,  # positive or negative
    reason: str,        # mandatory
    user_id: UUID,
    db: Session
) -> RawMaterialMovement:
    """
    1. Create RawMaterialMovement: type='adjustment', quantity=qty, reason=reason
    2. Update RawMaterial.current_stock += quantity
    3. Return movement record
    """
```

**Stock levels with thresholds:**
```python
def get_raw_materials_with_status(db: Session, search: str = None, material_type: str = None) -> list:
    """
    Return all raw materials with threshold status (green/amber/red).
    Same colour logic as finished goods thresholds.
    """
```

---

## 3. API Endpoints

### 3.1 Raw Materials Router

**File:** `backend/app/api/raw_materials.py`, prefix: `/api/raw-materials`

All endpoints require admin role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List raw materials with threshold status |
| `GET` | `/{id}` | Raw material detail + movement history |
| `POST` | `/` | Create raw material |
| `PUT` | `/{id}` | Update raw material |
| `DELETE` | `/{id}` | Soft delete (is_active=false) |
| `POST` | `/{id}/receive` | Record delivery received |
| `POST` | `/{id}/use` | Record material used |
| `POST` | `/{id}/adjustment` | Manual stock adjustment |

**Create request:**
```json
{
  "material_code": "RM-HDPE-BLACK",
  "material_name": "HDPE Resin - Black",
  "material_type": "resin",
  "unit_of_measure": "kg",
  "red_threshold": 100,
  "amber_threshold": 500,
  "default_supplier": "Qenos",
  "unit_cost": 2.50
}
```

**Receive request:**
```json
{
  "quantity": 1000,
  "supplier": "Qenos",
  "delivery_note": "DN-2026-0142",
  "unit_cost": 2.45
}
```

**Use request:**
```json
{
  "quantity": 250,
  "reason": "Production run LOCAP2 Black"
}
```

**Adjustment request:**
```json
{
  "quantity": -50,
  "reason": "Damaged bag - moisture contamination"
}
```

---

## 4. Frontend: Raw Materials UI

### 4.1 Route: `/raw-materials`

**File:** `frontend/src/routes/raw-materials/index.tsx`

Admin only. Lists all raw materials with CRUD + receive/use actions.

```
┌──────────────────────────────────────────────────────────┐
│  Raw Materials                          [Add Material]    │
│                                                           │
│  [Search...]  [Filter by type ▾]                         │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Code        │ Name           │ Type │ Stock │ Unit │   │
│  │ RM-HDPE-BLK │ HDPE Black     │ Resin│ ● 850 │ kg  │   │
│  │ RM-PP-NAT   │ PP Natural     │ Resin│ ● 1200│ kg  │   │
│  │ RM-MB-BLK   │ Masterbatch Blk│ MB   │ ● 50  │ kg  │   │
│  └────────────────────────────────────────────────────┘   │
│  Click row → /raw-materials/{id}                          │
│                                                           │
│  Quick Actions (per row):                                 │
│  [Receive] [Use] [Edit]                                   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Route: `/raw-materials/$materialId`

**File:** `frontend/src/routes/raw-materials/$materialId.tsx`

Detail page with full info + movement history.

```
┌──────────────────────────────────────────────────────────┐
│  RM-HDPE-BLK — HDPE Resin - Black                       │
│                                                           │
│  Type: Resin                                              │
│  Unit: kg                                                 │
│  Current stock: 850 kg  ● Green                          │
│  Thresholds: Red < 100, Amber < 500                      │
│  Default supplier: Qenos                                  │
│  Unit cost: $2.45/kg                                      │
│                                                           │
│  [Receive Delivery] [Record Usage] [Adjust] [Edit]       │
│                                                           │
│  Movement History:                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Date       │ Type     │ Qty   │ By    │ Notes     │   │
│  │ 2026-02-15 │ Received │ +1000 │ Admin │ DN-0142   │   │
│  │ 2026-02-14 │ Used     │ -150  │ Admin │ LOCAP2 run│   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 4.3 Forms

**ReceiveForm component** — modal/dialog for recording deliveries:
- Quantity (number input)
- Supplier (text, pre-filled from default_supplier)
- Delivery note reference (text)
- Unit cost (number, pre-filled from current)

**UsageForm component** — modal/dialog for recording usage:
- Quantity (number input, validated against current_stock)
- Reason (text, optional)

**AdjustmentForm** — modal/dialog for manual adjustments:
- Quantity (number, positive or negative)
- Reason (text, mandatory)

---

## 5. File Structure

```
backend/app/
├── services/
│   └── raw_material_service.py         ← NEW
├── api/
│   └── raw_materials.py                ← NEW
├── schemas/
│   └── raw_material_schemas.py         ← NEW

frontend/src/
├── routes/
│   └── raw-materials/
│       ├── index.tsx                   ← NEW
│       └── $materialId.tsx             ← NEW
├── components/
│   └── raw-materials/
│       ├── RawMaterialTable.tsx         ← NEW
│       ├── ReceiveForm.tsx             ← NEW
│       └── UsageForm.tsx               ← NEW
├── services/
│   └── rawMaterialService.ts           ← NEW
├── hooks/
│   └── useRawMaterials.ts              ← NEW
├── types/
│   └── rawMaterials.ts                 ← NEW
```

---

## 6. Testing Requirements

### Unit Tests
- Create raw material with all fields
- Receive delivery increases current_stock
- Record usage decreases current_stock
- Usage rejected when quantity > current_stock
- Manual adjustment with mandatory reason
- Threshold colour logic (green/amber/red)
- Soft delete sets is_active=false
- Movement history ordered by date desc

### Integration Tests
- Full flow: create material → receive → use → verify stock level
- Manual adjustment flow
- Search and filter work correctly
- Movement history appears on detail page

---

## 7. Exit Criteria

- [ ] Raw material CRUD working (create, read, update, soft delete)
- [ ] Receive delivery endpoint and UI working
- [ ] Record usage endpoint and UI working
- [ ] Manual adjustment with mandatory reason
- [ ] current_stock calculated correctly after all operations
- [ ] Colour-coded thresholds (green/amber/red) on list view
- [ ] Search by material code/name
- [ ] Filter by material type
- [ ] Movement history on detail page
- [ ] All endpoints admin-only (require_role("admin"))
- [ ] Raw materials nav item visible to admin only

---

## 8. Handoff to Phase 9

**Artifacts provided:**
- Raw material service with full CRUD + movement operations
- Raw material API router
- Frontend list and detail pages
- Raw material types and interfaces

**Phase 9 will:**
- Include raw material data in stock valuation reports
- Include raw material movement history in reports
- Export raw material data as spreadsheets

---

*Document created: 2026-02-18*
*Status: Planning*
