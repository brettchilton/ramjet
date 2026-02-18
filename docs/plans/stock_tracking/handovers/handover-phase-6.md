# Phase 6 Handover: Stock Dashboard & Thresholds

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Backend: Stock Service (`backend/app/services/stock_service.py`)
- **`get_stock_summary(db, search, colour, status_filter)`** — Aggregates in_stock items by product_code+colour, joins with products for descriptions and stock_thresholds for colour status. Returns `{ summary: { total_skus, total_units, total_cartons, low_stock_count }, items: [...] }`. Supports search by product code/description, colour filter, and threshold status filter (red/amber/green).
- **`get_stock_item_detail(db, stock_item_id)`** — Returns full stock item with movement history and product description.
- **`get_stock_items(db, product_code, colour, status, search, limit, offset)`** — Paginated list of individual stock items with filters.
- **`_resolve_threshold_status(total_quantity, red, amber)`** — Helper to determine green/amber/red status. Threshold lookup falls back from exact (product+colour) to product-only (colour=None).

### Backend: API Endpoints (`backend/app/api/stock.py`)
- **`GET /api/stock/summary`** — Dashboard summary with threshold status. Query params: `search`, `colour`, `status_filter`. Auth: warehouse+admin.
- **`GET /api/stock/items`** — Paginated stock item list. Query params: `product_code`, `colour`, `status`, `search`, `limit`, `offset`. Auth: warehouse+admin.
- **`GET /api/stock/items/{stock_item_id}`** — Individual stock item detail with movement history. Auth: warehouse+admin.
- **`GET /api/stock/thresholds`** — List all thresholds. Auth: admin only.
- **`POST /api/stock/thresholds`** — Create threshold. Auth: admin only.
- **`PUT /api/stock/thresholds/{id}`** — Update threshold. Auth: admin only.
- **`DELETE /api/stock/thresholds/{id}`** — Delete threshold. Auth: admin only.

### Backend: Schemas (`backend/app/schemas/stock_schemas.py`)
- `StockSummaryItem` — Updated: added `product_description`, renamed `total_quantity` → `total_units`
- `StockSummaryTotals` — New: totals for dashboard cards
- `StockSummaryResponse` — New: wraps summary + items
- `StockMovementDetailResponse` — New: movement with all fields for detail view
- `StockItemDetailResponse` — New: item + movements + product_description
- `StockItemListResponse` — New: paginated list with total

### Frontend: Services (`frontend/src/services/stockService.ts`)
- `fetchStockSummary(params)` — Dashboard summary API call
- `fetchStockItems(params)` — Stock item list API call
- `fetchStockItemDetail(id)` — Item detail API call
- `fetchThresholds()` / `createThreshold()` / `updateThreshold()` / `deleteThreshold()` — Threshold CRUD

### Frontend: Hooks (`frontend/src/hooks/useStock.ts`)
- `useStockSummary(params)` — React Query hook with 30s refetch interval
- `useStockItems(params)` — React Query hook, enabled only with filters
- `useStockItemDetail(id)` — React Query hook for detail page
- `useThresholds()` / `useCreateThreshold()` / `useUpdateThreshold()` / `useDeleteThreshold()` — Threshold CRUD hooks with cache invalidation

### Frontend: Types (`frontend/src/types/stock.ts`)
- `StockSummaryResponse`, `StockSummaryTotals`, `StockItemDetail`, `StockItemListResponse`
- `StockThreshold`, `StockThresholdCreate`, `StockThresholdUpdate`
- Updated `StockSummaryItem` with `product_description` and `total_units`

### Frontend: Components
- **`StockLevelCards`** (`components/stock/StockLevelCard.tsx`) — Three summary cards: Total SKUs, Total Units, Low Stock count. Uses Card from shadcn/ui with Lucide icons.
- **`StockTable`** (`components/stock/StockTable.tsx`) — Colour-coded stock level table with threshold badges (green/amber/red/neutral). Clickable rows for drill-down.
- **`MovementHistory`** (`components/stock/MovementHistory.tsx`) — Timeline view of stock movements with colour-coded icons per movement type (stock_in=green, stock_out=red, adjustment=amber, etc).
- **`ThresholdEditor`** (`components/stock/ThresholdEditor.tsx`) — Inline threshold CRUD table. Edit existing thresholds in-place, add new ones with product selector dropdown.

### Frontend: Pages
- **`/stock`** (`routes/stock/index.tsx`) — Role-conditional dashboard:
  - **Admin**: Summary cards + search + status filter buttons + colour-coded stock table + collapsible threshold config section
  - **Warehouse**: Search + read-only stock table (no threshold config, no summary cards, no filter buttons)
  - **Drill-down**: Clicking a row shows individual cartons for that product+colour. Clicking a carton navigates to detail page.
- **`/stock/$stockItemId`** (`routes/stock/$stockItemId.tsx`) — Individual carton detail with:
  - Header with barcode ID, product info, status badge
  - Two-column layout: carton details (left) + movement history timeline (right)
  - Details include: product, colour, quantity, box type, status, production date, scan timestamps

## Key Implementation Details

- **Threshold fallback logic**: When determining threshold status for a product+colour combination, the system first looks for an exact match (product_code + colour). If not found, it falls back to a product-only threshold (colour=NULL), which acts as a default for all colours of that product.
- **Search combines product code and description**: If search text doesn't match any product codes, it also tries matching against product descriptions in the products table.
- **Summary endpoint replaces old one**: The old `GET /api/stock/summary` which returned `list[StockSummaryItem]` has been replaced with a new response shape `StockSummaryResponse` that includes both totals and items. The `StockSummaryItem` schema field was renamed from `total_quantity` to `total_units` for clarity.
- **Route tree auto-generated**: Both `/stock/` and `/stock/$stockItemId` are registered in `routeTree.gen.ts`.

## State of the Codebase
- **What works**: Full dashboard with summary → drill-down → carton detail flow. Threshold CRUD. Role-conditional rendering. Search and filter.
- **Known issues**: None.

## For the Next Phase

### Phase 7 (Stocktake Verification) should:
- Use `GET /api/stock/items` to build the expected items list for stocktake sessions
- Reuse `ScanInput` component from Phase 3 for stocktake scanning
- Reuse `MovementHistory` component for displaying stocktake-related movements
- Build stocktake session management at `/stock/stocktake/`
- The `StockMovement` model already supports `stocktake_session_id` and `stocktake_verified` movement type

### Phase 9 (Reports & Export) should:
- Use `get_stock_summary()` as a basis for stock-on-hand reports
- The summary endpoint already provides the aggregated data needed for valuation reports
- Movement history queries can be adapted from `get_stock_item_detail()` for cross-item reports

## Test Results
- `get_stock_summary()` aggregates correctly by product_code+colour — PASS
- Threshold colour logic: green, amber, red, no threshold — PASS (unit tested via `_resolve_threshold_status`)
- Threshold CRUD endpoints: create, update, delete — PASS
- Search by product code and description — PASS
- Status filter (red/amber/green) — PASS
- Stock item detail returns item + movement history — PASS
- Stock item list with filters returns correct results — PASS
- Admin sees full dashboard with threshold config — PASS
- Warehouse sees read-only lookup without thresholds — PASS
- Drill-down from summary → carton list → individual carton — PASS
- Route tree generation includes both new routes — PASS
- TypeScript compilation passes (no new errors) — PASS
