# Phase 1 Handover: Database Models & Role System

## Completion Status
- Date completed: 2026-02-18
- All exit criteria met: Yes

## What Was Built

### Files Created
- `backend/app/schemas/stock_schemas.py` — Pydantic request/response models for all stock entities (StockItem, StockMovement, StockThreshold, StockVerification, StocktakeSession, StocktakeScan, RawMaterial, RawMaterialMovement, scan events, stock summary)
- `backend/app/api/stock.py` — Stub router for stock endpoints (prefix: `/api/stock`)
- `backend/app/api/stock_verification.py` — Stub router for verification endpoints (prefix: `/api/stock-verifications`)
- `backend/app/api/raw_materials.py` — Stub router for raw materials (prefix: `/api/raw-materials`)
- `backend/app/api/stocktake.py` — Stub router for stocktake (prefix: `/api/stocktake`)
- `backend/app/api/reports.py` — Stub router for reports (prefix: `/api/reports`)
- `backend/migrations/versions/0c4f7c31295e_add_stock_tracking_tables.py` — Alembic migration creating all 8 tables + `products.is_stockable`
- `docs/plans/stock_tracking/handovers/handover-phase-1.md` — This document

### Files Modified
- `backend/app/core/models.py` — Added 8 new SQLAlchemy models (StockItem, StockMovement, StockThreshold, StockVerification, StocktakeSession, StocktakeScan, RawMaterial, RawMaterialMovement). Added `is_stockable` column to Product. Added `stock_verifications` relationships to Order and OrderLineItem. Updated User role comment to include "warehouse".
- `backend/app/api/products.py` — Added POST `/`, PUT `/{product_code}`, DELETE `/{product_code}` endpoints with `require_role("admin")` guard. Imported `ProductCreate`, `ProductUpdate`, and `require_role`.
- `backend/app/schemas/product_schemas.py` — Added `ProductCreate` and `ProductUpdate` request models. Added `is_stockable` field to `ProductListItem` and `ProductFullResponse`.
- `backend/app/main.py` — Registered 5 new stub routers (stock, stock_verification, raw_materials, stocktake, reports).
- `frontend/src/components/Layout/Header.tsx` — Replaced hardcoded "Orders" nav with role-conditional navigation. Admin sees: Orders, Stock, Products, Raw Materials, Reports. Warehouse sees: Scan, Labels, Stock, Tasks.

## Key Implementation Details
- All models follow existing patterns: UUID primary keys via `func.uuid_generate_v4()`, `created_at`/`updated_at` timestamps
- `StockMovement` has a FK to `stocktake_sessions` — SQLAlchemy handles forward references correctly since both models are in the same file
- `StockItem.parent_stock_item_id` is a self-referential FK for partial repack tracking
- Product DELETE is a soft delete (`is_active=false`), not a hard delete
- The `require_role()` function (auth.py:170) already handles the admin-always-passes pattern, so no changes were needed to auth logic
- Navigation uses `getNavItems(user?.role)` — warehouse role gets simplified tablet-focused nav, all other roles (admin, inspector, viewer) get the full admin nav
- All indexes from MASTER_PLAN.md Section 4.2 are created by the migration

## State of the Codebase
- **What works**: All 8 database tables created and migrated. Product CRUD (create, update, soft-delete) functional with admin role guard. All 5 stub routers registered and loading. Frontend Header renders role-conditional navigation via HMR.
- **Known issues**: None

## For the Next Phase
- Phase 2 (QR Labels) should:
  - Create `backend/app/services/barcode_service.py` using the `StockItem` model for barcode ID generation
  - Add label generation endpoint to `backend/app/api/stock.py` (currently a stub)
  - Build the `/stock/labels` frontend page
  - The `StockItem` model is ready — barcode_id format is `RJ-{PRODUCT_CODE}-{COLOUR_SHORT}-{YYYYMMDD}-{SEQ}`
- Phase 8 (Raw Materials) can start independently:
  - `RawMaterial` and `RawMaterialMovement` models are ready
  - Add endpoints to `backend/app/api/raw_materials.py` stub
  - Schemas already exist in `stock_schemas.py`
- New backend dependencies (`qrcode[pil]`, `Pillow`, `reportlab`) are NOT yet added to requirements.txt — Phase 2 should add them

## Test Results
- All 8 SQLAlchemy models importable from `app.core.models` — PASS
- All 8 database tables created (`stock_items`, `stock_movements`, `stock_thresholds`, `stock_verifications`, `stocktake_sessions`, `stocktake_scans`, `raw_materials`, `raw_material_movements`) — PASS
- `products.is_stockable` column added — PASS
- Alembic migration runs cleanly (upgrade) — PASS
- Product POST creates new product — PASS
- Product PUT updates existing product — PASS
- Product DELETE soft-deletes (sets `is_active=false`) — PASS
- All 3 CRUD endpoints require admin role — PASS
- 5 stub routers registered in main.py (verified via OpenAPI) — PASS
- Frontend Header HMR update with no errors — PASS
- Backend restarts cleanly with all new models — PASS
