# Phase 1 Handover: Database & Product Data

**Status:** COMPLETE
**Date:** 2026-02-07

---

## What Was Built

Migrated the 57-product SQLite demonstrator database into PostgreSQL, exposed it via a REST API, and built the enrichment/calculation service that later phases depend on.

### Files Created

| File | Purpose |
|------|---------|
| `backend/app/core/models.py` | Added 5 SQLAlchemy models: Product, ManufacturingSpec, MaterialSpec, PackagingSpec, Pricing |
| `backend/app/schemas/__init__.py` | Package init |
| `backend/app/schemas/product_schemas.py` | Pydantic V2 response models for all API endpoints |
| `backend/app/api/products.py` | Products router: list, get, calculate, match |
| `backend/app/services/enrichment_service.py` | Product lookup, fuzzy matching, material/packaging calculations |
| `backend/scripts/seed_products.py` | SQLite → PostgreSQL migration script (idempotent) |
| `backend/tests/__init__.py` | Package init |
| `backend/tests/test_products.py` | 18 integration tests (all passing) |
| `backend/migrations/versions/853ac57bb136_add_product_catalog_tables.py` | Alembic migration for 5 product tables |

### Files Modified

| File | Change |
|------|--------|
| `backend/app/core/models.py` | Added `Numeric`, `Date` imports + 5 new models after existing `User` |
| `backend/app/main.py` | Imported and registered `products` router (2 lines) |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products/` | List all products. Optional `?search=` and `?customer=` filters |
| GET | `/api/products/match?code=X` | Fuzzy match product code (for Phase 3 LLM extraction) |
| GET | `/api/products/{product_code}` | Full product specs with all related data |
| GET | `/api/products/{product_code}/calculate?quantity=N&colour=X` | Material & packaging calculations |

---

## Database Schema

5 new PostgreSQL tables, all with UUID primary keys:

- **products** — product_code (UNIQUE), description, customer_name, is_active
- **manufacturing_specs** — 1:1 with products via product_code FK (mould, cycle time, shot weight, etc.)
- **material_specs** — N:1 with products, UNIQUE(product_code, colour) — material grades, masterbatch rates
- **packaging_specs** — 1:1 with products — bag/carton/pallet specifications
- **pricing** — N:1 with products, UNIQUE(product_code, colour) — unit prices in AUD

---

## Key Data Points

- **57 products** seeded from SQLite demonstrator
- **100 material specs** (some products have multiple colour variants)
- **100 pricing rows** (one per product/colour combination)
- All decimal fields use `Numeric` for precision (not `Float`)

---

## Enrichment Service Functions (for Phase 3)

The following functions in `app/services/enrichment_service.py` are ready for Phase 3 to import:

```python
from app.services.enrichment_service import (
    get_product_full_specs,       # Full JOINed product data
    calculate_material_requirements,  # Material + packaging calc with 5% waste
    search_products,              # ILIKE search on code + description
    match_product_code,           # Fuzzy matching with confidence scores
)
```

### Fuzzy Matching Confidence Levels

| Match Type | Confidence | Strategy |
|------------|------------|----------|
| exact | 1.0 | Exact string match on product_code |
| case_insensitive | 0.9 | Case-insensitive match on product_code |
| partial | 0.6 | ILIKE on code + description (max 5 results) |

---

## Verification Results

All verification criteria met:

- `alembic upgrade head` — succeeded
- Seed script — 57 products inserted
- `GET /api/products/` — returns 57 products
- `GET /api/products/LOCAP2` — returns full specs with manufacturing, materials, packaging, pricing
- `GET /api/products/LOCAP2/calculate?quantity=1000&colour=Black` — matches demonstrator output exactly:
  - total_material_kg: 44.1
  - base_material_kg: 42.56
  - masterbatch_kg: 1.1
  - additive_kg: 0.44
  - estimated_cost: 1320.0
- 18/18 tests passing

---

## Notes for Next Phases

- **Phase 3** should import `match_product_code()` for the LLM extraction pipeline's product resolution step
- **Phase 3** should import `calculate_material_requirements()` for enriching extracted orders
- The `Pricing.customer_name` field is nullable — can be used for customer-specific pricing in later phases
- The seed script is idempotent; re-running it skips if products already exist
