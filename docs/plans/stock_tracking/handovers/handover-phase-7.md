# Phase 7 Handover: Stocktake Verification

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Backend: Stocktake Service (`backend/app/services/stocktake_service.py`)
- **`start_session(name, user_id, db, notes)`** — Creates a StocktakeSession with status 'in_progress'. Snapshots the count of all in_stock StockItems as `total_expected`.
- **`process_stocktake_scan(session_id, barcode_id, user_id, db, notes)`** — Classifies scans: `found` (in_stock, not yet scanned), `not_in_system` (unknown barcode), `already_scanned` (duplicate), `wrong_status` (exists but not in_stock). Only `found` scans increment `total_scanned`.
- **`get_session_progress(session_id, db)`** — Returns `total_expected`, `total_scanned`, `percentage`.
- **`complete_session(session_id, user_id, auto_adjust, db)`** — Calculates discrepancies (missing items + unexpected scans). If `auto_adjust=true`, marks missing items as 'scrapped' with adjustment movements linked to the session.
- **`cancel_session(session_id, user_id, db)`** — Sets session to 'cancelled'.
- **`get_discrepancies(session_id, db)`** — Returns full discrepancy report: missing items (with last movement info), unexpected scans, and summary totals. Works for both in-progress (live missing) and completed (includes adjusted items) sessions.

### Backend: API Endpoints (`backend/app/api/stocktake.py`)
- **`GET /api/stocktake/sessions`** — List all sessions (admin only), most recent first.
- **`GET /api/stocktake/sessions/{id}`** — Session detail with progress (admin only).
- **`POST /api/stocktake/sessions`** — Start new session (admin only).
- **`POST /api/stocktake/sessions/{id}/scan`** — Record scan (warehouse + admin). Returns scan result + stock item + progress.
- **`POST /api/stocktake/sessions/{id}/complete`** — Complete session with optional auto_adjust (admin only).
- **`POST /api/stocktake/sessions/{id}/cancel`** — Cancel session (admin only).
- **`GET /api/stocktake/sessions/{id}/discrepancies`** — Get discrepancy report (admin only).
- **`GET /api/stocktake/sessions/{id}/scans`** — Get recent scans for session (warehouse + admin).

### Backend: Schemas (`backend/app/schemas/stocktake_schemas.py`)
- `SessionProgress` — Progress data (expected, scanned, percentage)
- `SessionDetailResponse` — Session + progress wrapper
- `StocktakeScanWithProgress` — Scan result with stock item + progress
- `StocktakeCompleteRequest` — Complete with auto_adjust flag
- `MissingItem`, `UnexpectedScan`, `DiscrepancySummary`, `DiscrepancyReport` — Discrepancy report structures
- Re-exports base schemas from `stock_schemas.py`

### Frontend: Service (`frontend/src/services/stocktakeService.ts`)
- `fetchSessions()`, `fetchSessionDetail(id)`, `startSession(name, notes)`
- `recordScan(sessionId, barcode, notes)`, `fetchSessionScans(sessionId, limit)`
- `completeSession(sessionId, autoAdjust)`, `cancelSession(sessionId)`
- `fetchDiscrepancies(sessionId)`

### Frontend: Hooks (`frontend/src/hooks/useStocktake.ts`)
- `useStocktakeSessions()` — Query with 30s stale time
- `useStocktakeSession(id)` — Query with 5s poll interval for live progress
- `useStocktakeScans(id)` — Query with 5s poll for recent scans
- `useDiscrepancies(id, enabled)` — Query for discrepancy report
- `useStartSession()`, `useRecordScan()`, `useCompleteSession()`, `useCancelSession()` — Mutations with cache invalidation

### Frontend: Types (`frontend/src/types/stock.ts`)
- `StocktakeSession`, `SessionProgress`, `SessionDetailResponse`
- `StocktakeScan`, `StocktakeScanWithProgress`
- `MissingItem`, `UnexpectedScan`, `DiscrepancySummary`, `DiscrepancyReport`

### Frontend: Components
- **`StocktakeProgress`** (`components/stock/StocktakeProgress.tsx`) — Progress bar with scanned/expected count and percentage.
- **`DiscrepancyTable`** (`components/stock/DiscrepancyTable.tsx`) — Summary cards (expected/found/missing/unexpected) + missing items table + unexpected scans list. Shows "No Discrepancies Found" when clean.
- **`Progress`** (`components/ui/progress.tsx`) — New shadcn/ui-style progress bar component (was missing from the component library).

### Frontend: Pages
- **`/stock/stocktake`** (`routes/stock/stocktake/index.tsx`) — Admin-only session list page. Table shows name, status badge, date, expected/scanned/discrepancy counts. "Start New" button with inline name input. Click row to navigate to session detail.
- **`/stock/stocktake/$sessionId`** (`routes/stock/stocktake/$sessionId.tsx`) — Active session page with:
  - Session header with name, start time, back navigation
  - Progress bar (uses local state for responsiveness, polls server for accuracy)
  - ScanInput component (reused from Phase 3) for stocktake scanning
  - Colour-coded scan result card (green=found, amber=already_scanned, red=not_in_system/wrong_status)
  - Complete/Cancel buttons with confirmation dialogs
  - Auto-adjust checkbox on completion
  - Discrepancy report section (shown after completion)
  - Recent scans list with icons and timestamps

## Key Implementation Details

- **Scan classification logic**: The service checks in order: already_scanned (duplicate in this session) → not_in_system (barcode unknown) → wrong_status (exists but not in_stock) → found (valid). Only `found` scans increment the scanned count.
- **Auto-adjust on completion**: When enabled, missing items are marked as 'scrapped' and get adjustment movements with `stocktake_session_id` set. This makes them traceable and distinguishable from manual adjustments.
- **Discrepancy report for completed sessions**: Handles both auto-adjusted (items now scrapped) and non-adjusted (items still in_stock but weren't scanned) cases by combining adjusted items + still-missing items.
- **Local progress state**: The session page maintains local progress state updated on each scan for immediate UI feedback, while also polling the server every 5 seconds for accuracy (handles concurrent scanners).
- **ScanInput reuse**: The Phase 3 ScanInput component is reused unchanged for stocktake scanning, maintaining the same auto-focus, debounce, and keyboard/scanner HID behaviour.
- **Route tree**: Both `/stock/stocktake/` and `/stock/stocktake/$sessionId` are registered in `routeTree.gen.ts`.

## State of the Codebase
- **What works**: Full stocktake lifecycle — start session → scan items → view progress → complete with optional auto-adjust → view discrepancy report. Cancel flow. Session list with status badges. All API endpoints tested.
- **Known issues**: None.

## For the Next Phase

### Phase 8 (Raw Materials) should:
- Build raw materials CRUD independently (no dependencies on stocktake)
- Can reuse the colour-coded threshold pattern from the stock dashboard (Phase 6)

### Phase 9 (Reports & Export) should:
- Use `get_discrepancies()` for stocktake report data
- The stocktake session model has `total_expected`, `total_scanned`, `total_discrepancies` for summary reports
- Stocktake scans can be queried by session for detailed reports

## Test Results
- Start session snapshots correct expected count (0 items currently) — PASS
- Scan classification: `not_in_system` for unknown barcode — PASS
- Scan classification: `already_scanned` for duplicate scan — PASS
- Complete session calculates discrepancies correctly — PASS
- Cancel session sets status to 'cancelled' — PASS
- Session detail returns session + progress — PASS
- Discrepancy report shows missing items and unexpected scans — PASS
- Session list returns all sessions ordered by date — PASS
- TypeScript compilation passes (no new errors) — PASS
- Route tree generation includes both new routes — PASS
- Backend imports and router registration verified in Docker — PASS
