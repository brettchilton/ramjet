# Phase 4: Order Integration & Stock Verification

## 1. Overview

**Objective**: Integrate stock tracking with the order system. When an order is created, automatically generate stock verification tasks. Warehouse verifies stock in parallel with Sharon's approval. Works orders generate only when both are complete, with verified stock deducted from production quantity.

This is the **most architecturally significant phase** — it changes how orders flow from approval to production.

**Scope**:
- Auto-creation of `StockVerification` records when orders are created
- `services/stock_verification_service.py` — verification logic
- `api/stock_verification.py` — verification endpoints
- Warehouse verification UI (`/stock/verification`)
- Modified works order generation: deducts verified stock from WO quantity
- New order flow: pending → approved (Sharon) + verified (warehouse) → works order generated

**Does NOT include**:
- Scan-out (Phase 5)
- Dashboard (Phase 6)
- Reports (Phase 9)

**Dependencies**: Phase 3 (stock_service.py with stock level calculation, stock items in database)

---

## 2. Order Flow Changes

### 2.1 Current Order Flow

```
pending → approved (Sharon) → forms generated immediately
       → rejected
```

### 2.2 New Order Flow

```
pending
├── Sharon reviews → approved (sets approved_by, approved_at)
│                    OR rejected
├── Auto-create StockVerification records (if stock exists)
│   └── Warehouse verifies → verified quantities confirmed
│
└── BOTH complete? → works_order_generated
    Works order qty = ordered qty - verified stock qty
```

**New order statuses:**
| Status | Meaning |
|--------|---------|
| `pending` | Awaiting review (existing) |
| `approved` | Sharon approved; may or may not have stock verification pending |
| `rejected` | Sharon rejected (existing) |
| `error` | Processing error (existing) |
| `works_order_generated` | Both approved + verified; works orders created with adjusted quantities |

### 2.3 When to Generate Works Orders

Works order generation triggers when **all** of these are true:
1. Order status is `approved` (Sharon approved)
2. All StockVerification records for this order are `confirmed` (or none exist)
3. Works orders have not already been generated

**Check function:**
```python
def check_and_generate_works_orders(order_id: UUID, db: Session):
    """
    Called after:
    - Sharon approves an order
    - Warehouse confirms a stock verification

    Checks if all conditions are met, then generates works orders
    with adjusted quantities.
    """
```

---

## 3. Stock Verification Service

### 3.1 `backend/app/services/stock_verification_service.py`

**Auto-create verifications on order creation:**

```python
def create_verifications_for_order(order_id: UUID, db: Session) -> list[StockVerification]:
    """
    Called when an order is created (after extraction).

    For each line item:
    1. Check if product_code + colour has any in_stock items
    2. If stock exists, create a StockVerification record:
       - system_stock_quantity = current stock level for that product+colour
       - status = 'pending'
    3. If no stock exists, skip (no verification needed — full quantity must be produced)

    Returns list of created verifications.
    """
```

**Confirm verification:**

```python
def confirm_verification(
    verification_id: UUID,
    verified_quantity: int,
    user_id: UUID,
    notes: str | None,
    db: Session
) -> StockVerification:
    """
    Warehouse confirms stock count.

    1. Update StockVerification: verified_quantity, verified_by, verified_at, status='confirmed'
    2. Check if all verifications for this order are now confirmed
    3. If yes, AND order is approved → trigger works order generation
    """
```

**Works order quantity adjustment:**

```python
def calculate_adjusted_quantity(ordered_qty: int, verified_qty: int) -> int:
    """
    WO quantity = ordered quantity - confirmed stock quantity.
    If verified >= ordered, return 0 (no production needed).
    """
    return max(0, ordered_qty - verified_qty)
```

---

## 4. Modifications to Existing Code

### 4.1 Order Creation Hook

**File:** `backend/app/api/orders.py` or `backend/app/services/extraction_service.py`

After an order is created (during email extraction processing), call:
```python
from app.services.stock_verification_service import create_verifications_for_order
create_verifications_for_order(order.id, db)
```

This must happen after line items are created and product codes are matched.

### 4.2 Order Approval Modification

**File:** `backend/app/api/orders.py` — `approve_order()` endpoint

Current behaviour: Approves order → immediately generates forms.

New behaviour:
1. Set order status to `approved`, set `approved_by`, `approved_at`
2. Check if stock verifications exist for this order
3. If no verifications → generate works orders immediately (no stock to verify)
4. If verifications exist and all confirmed → generate works orders with adjusted quantities
5. If verifications exist but some pending → do NOT generate yet; return message "Awaiting stock verification"

### 4.3 Works Order Generation Modification

**File:** `backend/app/services/form_generation_service.py` — `generate_works_order()`

Currently generates works orders with the full ordered quantity. Modify to:

1. Accept optional `adjusted_quantity` parameter
2. If `adjusted_quantity` is provided and > 0, use it instead of `line_item.quantity`
3. If `adjusted_quantity` is 0, skip works order generation for that line item
4. Add a note to the works order: "Stock on hand: {verified_qty} — Produce: {adjusted_qty}"

### 4.4 Order Approval Response

Update the approval response to indicate verification status:
```json
{
  "order_id": "uuid",
  "status": "approved",
  "message": "Order approved. Awaiting stock verification for 2 line items.",
  "verification_status": "pending",
  "verifications": [
    {
      "line_item_id": "uuid",
      "product_code": "LOCAP2",
      "colour": "Black",
      "ordered_quantity": 2000,
      "system_stock": 500,
      "verification_status": "pending"
    }
  ]
}
```

---

## 5. API Endpoints

### 5.1 Stock Verification Router

**File:** `backend/app/api/stock_verification.py`, prefix: `/api/stock-verifications`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/pending` | warehouse, admin | List all pending verification tasks |
| `GET` | `/order/{order_id}` | warehouse, admin | Get verifications for a specific order |
| `POST` | `/{id}/confirm` | warehouse, admin | Confirm/adjust stock count |

**Confirm request:**
```json
{
  "verified_quantity": 20,
  "notes": "Counted 20 cartons of LOCAP2 Black"
}
```

**Confirm response:**
```json
{
  "verification_id": "uuid",
  "status": "confirmed",
  "verified_quantity": 20,
  "works_order_triggered": true,
  "message": "Stock verified. Works orders generated."
}
```

---

## 6. Frontend: Verification UI

### 6.1 Route: `/stock/verification`

**File:** `frontend/src/routes/stock/verification.tsx`

This page is visible to **warehouse + admin** users. It shows pending verification tasks.

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ Header                                                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Stock Verification Tasks                                 │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Order: PO-2026-0142 — ABC Plastics              │     │
│  │  Created: 2026-02-11                              │     │
│  │                                                    │     │
│  │  LOCAP2 — Black                                   │     │
│  │  Ordered: 2,000 units                             │     │
│  │  System stock: 500 units (10 cartons)             │     │
│  │                                                    │     │
│  │  Verified quantity: [500          ]               │     │
│  │  Notes: [Confirmed 10 cartons in bay 3     ]      │     │
│  │                                                    │     │
│  │  [Confirm Stock]                                   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Order: PO-2026-0143 — XYZ Corp                  │     │
│  │  ...                                               │     │
│  └──────────────────────────────────────────────────┘     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Behaviour:**
- Lists all pending verifications, grouped by order
- Pre-fills `verified_quantity` with `system_stock_quantity` (warehouse confirms or adjusts)
- Warehouse physically goes to check stock, then comes back and confirms
- On confirm: POST to `/api/stock-verifications/{id}/confirm`
- If this was the last pending verification for an order, show "Works orders generated" message
- Large touch targets for tablet use

### 6.2 Service + Hook

**File:** `frontend/src/services/stockVerificationService.ts`
- `getPendingVerifications()` — GET `/api/stock-verifications/pending`
- `confirmVerification(id, data)` — POST `/api/stock-verifications/{id}/confirm`

**File:** `frontend/src/hooks/useStockVerification.ts`
- `usePendingVerifications()` — query hook
- `useConfirmVerification()` — mutation hook

---

## 7. File Structure

```
backend/app/
├── services/
│   ├── stock_verification_service.py   ← NEW
│   └── form_generation_service.py      ← MODIFY: Accept adjusted_quantity
├── api/
│   ├── stock_verification.py           ← NEW
│   └── orders.py                       ← MODIFY: Hook verification creation + conditional WO generation
├── schemas/
│   └── stock_verification_schemas.py   ← NEW

frontend/src/
├── routes/
│   └── stock/
│       └── verification.tsx            ← NEW
├── components/
│   └── stock/
│       └── VerificationTaskCard.tsx    ← NEW
├── services/
│   └── stockVerificationService.ts     ← NEW
├── hooks/
│   └── useStockVerification.ts         ← NEW
```

---

## 8. Testing Requirements

### Unit Tests
- Order creation triggers StockVerification records for line items with stock
- No verification created for line items with zero stock
- Verification confirm updates status and quantity
- `check_and_generate_works_orders` triggers when all verifications confirmed AND order approved
- Works order quantity correctly adjusted: ordered - verified
- Works order skipped when verified >= ordered
- Approval without pending verifications generates works orders immediately

### Integration Tests
- Full flow: create order → verify stock → approve → works orders generated with adjusted qty
- Full flow: approve first → then verify → works orders generated
- Order with no stock: approve → works orders generated immediately (no verification needed)
- Partial verification: approve + verify 1 of 2 → no works orders yet
- Edge case: verified_quantity = 0 (warehouse says no stock actually exists)

---

## 9. Exit Criteria

- [ ] StockVerification records auto-created when orders are processed
- [ ] Verification only created for line items with existing stock
- [ ] Warehouse can view pending verification tasks
- [ ] Warehouse can confirm/adjust stock quantities
- [ ] Works orders generate only when BOTH approved AND verified
- [ ] Works order quantity = ordered - verified stock
- [ ] Line items with verified >= ordered skip works order generation
- [ ] Approval without verifications generates works orders immediately
- [ ] Order status transitions work correctly
- [ ] Verification UI accessible to warehouse users on tablet
- [ ] Integration with existing order approval flow is seamless
- [ ] form_generation_service.py modified to accept adjusted quantities

---

## 10. Handoff to Phase 5

**Artifacts provided:**
- `stock_verification_service.py` — verification creation and confirmation
- `stock_verification.py` API router — verification endpoints
- Modified `orders.py` — hooks for verification + conditional WO generation
- Modified `form_generation_service.py` — adjusted quantity support
- Verification UI at `/stock/verification`
- Complete order integration flow working end-to-end

**Phase 5 will:**
- Add scan-out logic to `stock_service.py`
- Add Stock Out mode to `/stock/scan`
- Link scan-out to orders
- Handle partial boxes

---

*Document created: 2026-02-18*
*Status: Planning*
