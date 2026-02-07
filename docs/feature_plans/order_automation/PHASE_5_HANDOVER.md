# Phase 5 Handover — Frontend: Dashboard & Order Review

**Status:** COMPLETE
**Date:** 2026-02-07

---

## What Was Built

### Orders Dashboard (`/orders`)
- **Status cards row**: Email monitor status, pending/approved/rejected/error count cards
- **Orders table**: Filterable by status, sortable columns — Status, Customer, PO#, Items, Confidence, Date, Forms indicator
- **Process Emails button**: Triggers `POST /api/orders/process-pending` to process unprocessed emails
- Clickable rows navigate to order review page
- 30-second auto-refresh polling for new orders

### Order Review Page (`/orders/{orderId}`)
- **Breadcrumb bar**: Back button, customer name, PO#, status badge, confidence badge
- **Two-column layout**:
  - Left (40%): Source document panel — email body, PDF viewer (react-pdf), image viewer, attachment downloads
  - Right (60%): Extracted data form — header fields + line items table with inline confidence badges
- **Form Preview section**: Tabbed HTML previews — Office Order table + Works Order for each line item with full product specs
- **Action bar**: Approve (green), Edit toggle, Reject (opens dialog) — sticky bottom
- **Edit mode**: Fields switch between read-only text and editable inputs; line total auto-recalculates
- **After approval**: Shows "Approved" status with download buttons for .xlsx files
- **After rejection**: Shows rejection reason

### Shared Components
- `ConfidenceBadge` — green/amber/red pill based on confidence threshold
- `StatusBadge` — colour-coded status using shadcn Badge
- `RejectDialog` — modal with textarea for rejection reason

### Infrastructure
- `react-pdf` installed for inline PDF rendering
- shadcn `Badge` and `Table` components added (were missing)
- TanStack React Query hooks with polling and mutation invalidation
- Backend `GET /api/system/emails/{id}` endpoint added for email detail

---

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/types/orders.ts` | TypeScript interfaces matching backend schemas |
| `frontend/src/services/orderService.ts` | API service layer wrapping apiClient |
| `frontend/src/hooks/useOrders.ts` | TanStack React Query hooks (queries + mutations) |
| `frontend/src/components/orders/ConfidenceBadge.tsx` | Confidence score badge |
| `frontend/src/components/orders/StatusBadge.tsx` | Order status badge |
| `frontend/src/components/orders/RejectDialog.tsx` | Rejection reason dialog |
| `frontend/src/components/orders/OrderSourcePanel.tsx` | Email + PDF/image source viewer |
| `frontend/src/components/orders/OrderDataForm.tsx` | Extracted data form (read-only + editable) |
| `frontend/src/components/orders/FormPreview.tsx` | Office Order + Works Order HTML previews |
| `frontend/src/components/orders/OrderActions.tsx` | Approve/Edit/Reject action bar |
| `frontend/src/routes/orders/index.tsx` | Dashboard page route |
| `frontend/src/routes/orders/$orderId.tsx` | Order review page route |
| `frontend/src/components/ui/badge.tsx` | shadcn Badge component |
| `frontend/src/components/ui/table.tsx` | shadcn Table component |

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/components/Layout/Header.tsx` | Added "Orders" navigation link |
| `frontend/src/routes/index.tsx` | Redirect authenticated users to `/orders` instead of `/dashboard` |
| `backend/app/api/system.py` | Added `GET /api/system/emails/{id}` endpoint |
| `frontend/package.json` | Added `react-pdf` dependency |
| `frontend/src/routeTree.gen.ts` | Auto-regenerated with new order routes |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `react-pdf` for PDF viewing | Full inline PDF rendering with page navigation; better UX than iframe |
| HTML form preview (not from Excel) | Renders from live order data for real-time preview before approval |
| Read-only by default, Edit toggle | Prevents accidental edits; explicit user action to modify |
| Client-side status filtering | Orders list is small enough; avoids extra API calls |
| 30s orders polling, 15s monitor polling | Keeps dashboard fresh without overwhelming the API |
| Sticky action bar | Always visible for quick approve/reject actions |

---

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `react-pdf` | latest | PDF document rendering in browser |

---

## What's Next (Phase 6)

Phase 6: Email Distribution — automatically email generated forms to relevant parties after approval.
