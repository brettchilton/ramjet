"""
Products API — browse catalog, get full specs, calculate material requirements, CRUD.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.models import Product
from app.core.auth import require_role
from app.schemas.product_schemas import (
    ProductListItem,
    ProductFullResponse,
    ManufacturingSpecResponse,
    MaterialSpecResponse,
    PackagingSpecResponse,
    PricingResponse,
    CalculationResponse,
    MaterialRequirements,
    PackagingRequirements,
    ProductMatch,
    ProductCreate,
    ProductUpdate,
)
from app.services.enrichment_service import (
    get_product_full_specs,
    calculate_material_requirements,
    search_products,
    match_product_code,
)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=list[ProductListItem])
def list_products(
    search: Optional[str] = Query(None, description="Search code or description"),
    customer: Optional[str] = Query(None, description="Filter by customer name"),
    db: Session = Depends(get_db),
):
    if search:
        results = search_products(db, search)
        if customer:
            results = [r for r in results if r["customer_name"] and customer.lower() in r["customer_name"].lower()]
        return results

    query = db.query(Product).order_by(Product.product_code)
    if customer:
        query = query.filter(Product.customer_name.ilike(f"%{customer}%"))
    return query.all()


@router.get("/match", response_model=list[ProductMatch])
def match_product(
    code: str = Query(..., description="Extracted product code to match"),
    db: Session = Depends(get_db),
):
    return match_product_code(db, code)


@router.get("/{product_code}", response_model=ProductFullResponse)
def get_product(product_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_code}' not found")

    mfg = product.manufacturing_spec
    return ProductFullResponse(
        product_code=product.product_code,
        product_description=product.product_description,
        customer_name=product.customer_name,
        is_active=product.is_active,
        manufacturing=ManufacturingSpecResponse.model_validate(mfg) if mfg else None,
        materials=[MaterialSpecResponse.model_validate(m) for m in product.material_specs],
        packaging=PackagingSpecResponse.model_validate(product.packaging_spec) if product.packaging_spec else None,
        pricing=[PricingResponse.model_validate(p) for p in product.pricing],
    )


@router.get("/{product_code}/calculate", response_model=CalculationResponse)
def calculate(
    product_code: str,
    quantity: int = Query(..., gt=0, description="Number of units"),
    colour: str = Query(..., description="Colour variant"),
    db: Session = Depends(get_db),
):
    result = calculate_material_requirements(db, product_code, colour, quantity)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No specs found for {product_code}/{colour}",
        )
    return CalculationResponse(
        product_code=result["product_code"],
        colour=result["colour"],
        quantity=result["quantity"],
        material_requirements=MaterialRequirements(**result["material_requirements"]),
        packaging_requirements=PackagingRequirements(**result["packaging_requirements"]),
        estimated_cost=result["estimated_cost"],
    )


# ── CRUD endpoints (admin only) ──────────────────────────────────────

@router.post("/", response_model=ProductListItem, dependencies=[Depends(require_role("admin"))])
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(Product).filter(Product.product_code == payload.product_code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Product '{payload.product_code}' already exists")

    product = Product(
        product_code=payload.product_code,
        product_description=payload.product_description,
        customer_name=payload.customer_name,
        is_stockable=payload.is_stockable,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_code}", response_model=ProductListItem, dependencies=[Depends(require_role("admin"))])
def update_product(
    product_code: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_code}' not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_code}", dependencies=[Depends(require_role("admin"))])
def delete_product(
    product_code: str,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.product_code == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_code}' not found")

    product.is_active = False
    db.commit()
    return {"message": f"Product '{product_code}' deactivated"}
