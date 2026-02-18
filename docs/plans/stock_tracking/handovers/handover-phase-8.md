# Phase 8 Handover: Raw Materials

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Created
- `backend/app/schemas/raw_material_schemas.py` — Dedicated Pydantic schemas for raw materials (RawMaterialCreate, RawMaterialUpdate, RawMaterialResponse, RawMaterialWithStatus, RawMaterialDetailResponse, RawMaterialMovementResponse, request models for receive/use/adjust)
- `backend/app/services/raw_material_service.py` — Business logic: receive_delivery, record_usage, adjust_stock, get_raw_materials_with_status, get_raw_material_detail with threshold computation
- `frontend/src/types/rawMaterials.ts` — TypeScript interfaces for all raw material types
- `frontend/src/services/rawMaterialService.ts` — API client functions for all raw material endpoints
- `frontend/src/hooks/useRawMaterials.ts` — React Query hooks (useRawMaterials, useRawMaterial, useCreateRawMaterial, useUpdateRawMaterial, useDeleteRawMaterial, useReceiveDelivery, useRecordUsage, useAdjustStock)
- `frontend/src/routes/raw-materials/index.tsx` — List page with summary cards (total/critical/low/healthy), search, type filter, create/edit/receive/use dialogs
- `frontend/src/routes/raw-materials/$materialId.tsx` — Detail page with stock level card, thresholds, supplier info, movement history table, receive/use/adjust actions
- `frontend/src/components/raw-materials/RawMaterialTable.tsx` — Colour-coded table with status indicators, type badges, inline actions
- `frontend/src/components/raw-materials/ReceiveForm.tsx` — Dialog form for recording deliveries (pre-fills supplier and cost from material defaults)
- `frontend/src/components/raw-materials/UsageForm.tsx` — Dialog form for recording usage (validates against available stock)

### Files Modified
- `backend/app/api/raw_materials.py` — Replaced Phase 1 stub with full implementation: GET list, GET detail, POST create, PUT update, DELETE soft-delete, POST receive, POST use, POST adjustment

## Key Implementation Details
- All endpoints require admin role via `require_role("admin")` — warehouse users cannot access raw materials
- Schemas are in a dedicated `raw_material_schemas.py` file (separate from the Phase 1 `stock_schemas.py` which also had raw material schemas — the new file has additional fields like `threshold_status` and `performed_by_name`)
- Threshold status computed in service layer: stock >= amber → green, stock >= red → amber, stock < red → red
- Usage validation prevents stock going negative (400 error with clear message)
- Adjustments also prevent resulting negative stock
- Movement history is ordered by created_at descending (most recent first)
- Detail endpoint joins User to provide `performed_by_name` on movements
- Unit cost is updated on the material when a delivery provides a new cost
- Frontend uses debounced search via React Query queryKey changes
- All mutation hooks invalidate both the individual material and the list query on success
- Error messages from the API are surfaced in the frontend (parsed from response body)

## State of the Codebase
- **What works**: Full CRUD for raw materials. Receive delivery increases stock. Record usage decreases stock (with validation). Manual adjustment with mandatory reason. Colour-coded thresholds (green/amber/red) on list and detail views. Search by code/name. Filter by material type. Movement history with performer names on detail page. Soft delete (deactivate). All endpoints admin-only.
- **Known issues**: None

## For the Next Phase
- Phase 9 (Reports & Export) should:
  - Include raw material data in stock valuation reports
  - Include raw material movement history in movement reports
  - Export raw material data as spreadsheets (.xlsx)
  - The `get_raw_materials_with_status()` and `get_raw_material_detail()` service functions can be reused for report data
  - Movement data is available via `RawMaterialMovement` model with `raw_material_id`, `movement_type`, `quantity`, `created_at` fields

## Test Results
- Create raw material with all fields — PASS
- List raw materials with threshold_status computed — PASS (stock=0, red_threshold=100 → status=red)
- Receive delivery increases current_stock — PASS (0 + 1000 = 1000)
- Record usage decreases current_stock — PASS (1000 - 250 = 750)
- Usage rejected when quantity > current_stock — PASS (returns 400 with clear message)
- Manual adjustment with mandatory reason — PASS (750 - 50 = 700)
- Threshold colour logic — PASS (700 >= 500 amber → green)
- Search by code/name works — PASS
- Filter by material_type works — PASS
- Update material fields — PASS
- Soft delete sets is_active=false — PASS
- Detail endpoint returns movement history ordered by date desc — PASS
- Movement history includes performed_by_name — PASS
- Full flow: create → receive → use → adjust → verify stock level — PASS (0 + 1000 - 250 - 50 = 700)
