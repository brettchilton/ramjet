# Phase 1: Database Models & Role System

## 1. Overview

**Objective**: Create all database tables for the stock tracking system and extend the user role system to support warehouse users.

**Scope**:
- All new SQLAlchemy models (stock_items, stock_movements, stock_thresholds, stock_verifications, stocktake_sessions, stocktake_scans, raw_materials, raw_material_movements)
- Add "warehouse" role to User model
- Add `is_stockable` field to Product model
- Role-based route guards (backend endpoint protection)
- Role-based navigation (frontend Header component)
- Alembic migration
- Enhance `api/products.py` with full CRUD

**Does NOT include**:
- Any scanning logic or UI
- Stock service business logic
- Label generation
- Reports

**Dependencies**: None — this is the foundation phase.

---

## 2. Database Models

### 2.1 New Models in `backend/app/core/models.py`

Add all models specified in MASTER_PLAN.md Section 4.1. Each model uses the existing `Base` and follows the established pattern (UUID primary keys via `func.uuid_generate_v4()`, `created_at`/`updated_at` timestamps).

**Models to create:**

| Model | Table | Key Fields |
|-------|-------|------------|
| `StockItem` | `stock_items` | barcode_id, product_code, colour, quantity, box_type, status |
| `StockMovement` | `stock_movements` | stock_item_id, movement_type, quantity_change, performed_by |
| `StockThreshold` | `stock_thresholds` | product_code, colour, red_threshold, amber_threshold |
| `StockVerification` | `stock_verifications` | order_id, order_line_item_id, system_stock_quantity, verified_quantity, status |
| `StocktakeSession` | `stocktake_sessions` | name, status, started_by, total_expected, total_scanned |
| `StocktakeScan` | `stocktake_scans` | session_id, barcode_scanned, stock_item_id, scan_result |
| `RawMaterial` | `raw_materials` | material_code, material_name, material_type, current_stock |
| `RawMaterialMovement` | `raw_material_movements` | raw_material_id, movement_type, quantity, performed_by |

### 2.2 Modifications to Existing Models

**Product model** — add field:
```python
is_stockable = Column(Boolean, default=True)
```

**User model** — update role comment to include "warehouse":
```python
role = Column(String(50), default="inspector")  # inspector, admin, viewer, warehouse
```

No structural change needed to the User model — the role field already accepts any string. The change is documentation and the backend `require_role()` logic already handles it (admin always passes, specific role check otherwise).

### 2.3 Relationships

Add relationships to existing models:

```python
# On Order model
stock_verifications = relationship("StockVerification", back_populates="order")

# On OrderLineItem model
stock_verifications = relationship("StockVerification", back_populates="order_line_item")
```

---

## 3. Alembic Migration

Create a single migration that:
1. Creates all 8 new tables
2. Adds `is_stockable` column to `products` table
3. Creates all indexes specified in MASTER_PLAN.md Section 4.2

**Migration naming:** `add_stock_tracking_tables`

Run and verify:
```bash
docker-compose exec backend alembic revision --autogenerate -m "add_stock_tracking_tables"
docker-compose exec backend alembic upgrade head
```

---

## 4. Backend Role Guards

### 4.1 Existing `require_role()` — No Changes Needed

The existing implementation in `backend/app/core/auth.py:170-181` already works:
```python
def require_role(required_role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(status_code=403, ...)
        return current_user
    return role_checker
```

This means:
- `require_role("warehouse")` → allows warehouse + admin
- `require_role("admin")` → allows admin only

### 4.2 Product CRUD Endpoints

Extend `backend/app/api/products.py` (currently read-only) with:

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| `POST` | `/` | `require_role("admin")` | Create product with specs |
| `PUT` | `/{product_code}` | `require_role("admin")` | Update product |
| `DELETE` | `/{product_code}` | `require_role("admin")` | Soft delete (is_active=false) |

### 4.3 Pydantic Schemas

Create `backend/app/schemas/stock_schemas.py` with request/response models for all stock-related endpoints. Follow the patterns in `backend/app/schemas/order_schemas.py`.

Create `backend/app/schemas/product_schemas.py` (or extend existing) with:
- `ProductCreate` — request model for creating a product
- `ProductUpdate` — request model for updating a product
- `ProductDetail` — response model with all specs

---

## 5. Frontend Role-Based Navigation

### 5.1 Modify Header Component

**File:** `frontend/src/components/Layout/Header.tsx`

The current Header has a hardcoded "Orders" nav link. Replace with role-conditional navigation.

**Implementation approach:**
1. Get `user.role` from `useUnifiedAuth()` (already available)
2. Define nav items per role
3. Render conditionally

```tsx
// Pseudocode for nav items
const adminNav = [
  { label: 'Orders', path: '/orders' },
  { label: 'Stock', path: '/stock' },
  { label: 'Products', path: '/products' },
  { label: 'Raw Materials', path: '/raw-materials' },
  { label: 'Reports', path: '/reports' },
];

const warehouseNav = [
  { label: 'Scan', path: '/stock/scan' },
  { label: 'Labels', path: '/stock/labels' },
  { label: 'Stock', path: '/stock' },
  { label: 'Tasks', path: '/stock/verification' },
];

const navItems = user?.role === 'warehouse' ? warehouseNav : adminNav;
```

### 5.2 Create Route Guard Component

Create a reusable `RequireRole` wrapper component that redirects if the user doesn't have the required role. Use in route definitions.

---

## 6. File Structure

```
backend/app/
├── core/
│   └── models.py                       ← MODIFY: Add 8 new models + Product.is_stockable
├── api/
│   └── products.py                     ← MODIFY: Add POST, PUT, DELETE endpoints
├── schemas/
│   ├── stock_schemas.py                ← NEW: Stock Pydantic models
│   └── product_schemas.py              ← NEW or MODIFY: Product CRUD schemas
├── migrations/versions/
│   └── xxxx_add_stock_tracking_tables.py ← NEW: Alembic migration

frontend/src/
├── components/
│   └── Layout/
│       └── Header.tsx                  ← MODIFY: Role-conditional navigation
```

---

## 7. Testing Requirements

### Unit Tests
- All new SQLAlchemy models can be instantiated
- Migration runs forward and backward cleanly
- `require_role("warehouse")` allows warehouse and admin, blocks others
- `require_role("admin")` allows admin only, blocks warehouse
- Product CRUD: create, read, update, soft delete
- Role-based nav renders correct items for each role

### Integration Tests
- Create a warehouse user, verify they can authenticate and their role is returned
- Create a product via API, verify it appears in list
- Soft delete a product, verify `is_active=false`

---

## 8. Exit Criteria

- [ ] All 8 new SQLAlchemy models defined in `models.py`
- [ ] `is_stockable` field added to Product model
- [ ] Alembic migration created and runs cleanly (upgrade + downgrade)
- [ ] All indexes created as specified
- [ ] Product CRUD endpoints working (POST, PUT, DELETE)
- [ ] `require_role("warehouse")` tested and working
- [ ] Header component renders role-conditional navigation
- [ ] Warehouse user sees: Scan, Labels, Stock, Tasks
- [ ] Admin user sees: Orders, Stock, Products, Raw Materials, Reports
- [ ] All Pydantic schemas created for stock models
- [ ] New routers registered in `main.py` (even if endpoints are empty stubs)

---

## 9. Handoff to Phase 2

**Artifacts provided:**
- All database tables created and migrated
- SQLAlchemy models importable from `app.core.models`
- Role-based auth working on endpoints
- Product CRUD endpoints functional
- Frontend nav rendering by role

**Phase 2 will:**
- Create `barcode_service.py` that generates barcodes referencing `StockItem` model
- Create label generation endpoint on the stock router
- Build the `/stock/labels` frontend page

---

*Document created: 2026-02-18*
*Status: Planning*
