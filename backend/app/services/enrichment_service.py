"""
Product enrichment service — replicates the demonstrator's product_lookup.py
using SQLAlchemy queries against PostgreSQL.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.models import Product, ManufacturingSpec, MaterialSpec, PackagingSpec, Pricing


def get_product_full_specs(db: Session, product_code: str, colour: Optional[str] = None) -> Optional[dict]:
    """
    Get all specifications for a product.
    If colour is None, returns all colour variants.
    """
    product = (
        db.query(Product)
        .options(
            joinedload(Product.manufacturing_spec),
            joinedload(Product.material_specs),
            joinedload(Product.packaging_spec),
            joinedload(Product.pricing),
        )
        .filter(Product.product_code == product_code)
        .first()
    )

    if not product:
        return None

    materials = product.material_specs
    pricing_list = product.pricing

    if colour:
        materials = [m for m in materials if m.colour == colour]
        pricing_list = [p for p in pricing_list if p.colour == colour]

    if not materials:
        return None

    mfg = product.manufacturing_spec
    pkg = product.packaging_spec

    results = []
    for mat in materials:
        price_row = next((p for p in pricing_list if p.colour == mat.colour), None)
        results.append({
            "product_code": product.product_code,
            "product_description": product.product_description,
            "customer": product.customer_name,
            "mould_no": mfg.mould_no if mfg else None,
            "cycle_time_seconds": mfg.cycle_time_seconds if mfg else None,
            "shot_weight_grams": float(mfg.shot_weight_grams) if mfg and mfg.shot_weight_grams else None,
            "num_cavities": mfg.num_cavities if mfg else None,
            "product_weight_grams": float(mfg.product_weight_grams) if mfg and mfg.product_weight_grams else None,
            "estimated_running_time_hours": float(mfg.estimated_running_time_hours) if mfg and mfg.estimated_running_time_hours else None,
            "machine_min_requirements": mfg.machine_min_requirements if mfg else None,
            "packaging": {
                "qty_per_bag": pkg.qty_per_bag if pkg else None,
                "bag_size": pkg.bag_size if pkg else None,
                "qty_per_carton": pkg.qty_per_carton if pkg else None,
                "carton_size": pkg.carton_size if pkg else None,
                "cartons_per_pallet": pkg.cartons_per_pallet if pkg else None,
                "cartons_per_layer": pkg.cartons_per_layer if pkg else None,
            },
            "material": {
                "colour": mat.colour,
                "material_grade": mat.material_grade,
                "material_type": mat.material_type,
                "colour_no": mat.colour_no,
                "colour_supplier": mat.colour_supplier,
                "mb_add_rate": float(mat.mb_add_rate) if mat.mb_add_rate is not None else 0.0,
                "additive": mat.additive,
                "additive_add_rate": float(mat.additive_add_rate) if mat.additive_add_rate is not None else 0.0,
                "additive_supplier": mat.additive_supplier,
            },
            "unit_cost": float(price_row.unit_price) if price_row else None,
        })

    return results if len(results) > 1 else results[0]


def calculate_material_requirements(
    db: Session, product_code: str, colour: str, quantity: int
) -> Optional[dict]:
    """
    Calculate material requirements for a given quantity.
    Replicates demonstrator logic exactly: 5 % waste factor, ceiling-division packaging.
    """
    specs = get_product_full_specs(db, product_code, colour)

    if not specs:
        return None

    # If multiple results came back (shouldn't with colour filter), take first
    if isinstance(specs, list):
        specs = specs[0]

    product_weight = specs["product_weight_grams"] or 0.0
    total_product_weight_kg = (product_weight * quantity) / 1000

    waste_factor = 1.05
    total_material_required_kg = total_product_weight_kg * waste_factor

    mb_rate = specs["material"]["mb_add_rate"] / 100
    mb_required_kg = total_material_required_kg * mb_rate

    add_rate = specs["material"]["additive_add_rate"] / 100
    additive_required_kg = total_material_required_kg * add_rate

    base_material_kg = total_material_required_kg - mb_required_kg - additive_required_kg

    pkg = specs["packaging"]
    qty_per_carton = pkg["qty_per_carton"] or 1
    qty_per_bag = pkg["qty_per_bag"] or 1
    cartons_needed = (quantity + qty_per_carton - 1) // qty_per_carton
    bags_needed = (quantity + qty_per_bag - 1) // qty_per_bag

    unit_cost = specs["unit_cost"] or 0.0

    return {
        "product_code": product_code,
        "colour": colour,
        "quantity": quantity,
        "material_requirements": {
            "base_material_kg": round(base_material_kg, 2),
            "material_grade": specs["material"]["material_grade"],
            "material_type": specs["material"]["material_type"],
            "masterbatch_kg": round(mb_required_kg, 2),
            "colour_no": specs["material"]["colour_no"],
            "colour_supplier": specs["material"]["colour_supplier"],
            "additive_kg": round(additive_required_kg, 2),
            "additive": specs["material"]["additive"],
            "additive_supplier": specs["material"]["additive_supplier"],
            "total_material_kg": round(total_material_required_kg, 2),
        },
        "packaging_requirements": {
            "bags_needed": bags_needed,
            "bag_size": pkg["bag_size"],
            "cartons_needed": cartons_needed,
            "carton_size": pkg["carton_size"],
        },
        "estimated_cost": round(unit_cost * quantity, 2),
    }


def search_products(db: Session, search_term: str) -> list[dict]:
    """
    Search products by code or description (case-insensitive ILIKE).
    """
    pattern = f"%{search_term}%"
    rows = (
        db.query(Product)
        .filter(
            or_(
                Product.product_code.ilike(pattern),
                Product.product_description.ilike(pattern),
            )
        )
        .order_by(Product.product_code)
        .all()
    )
    return [
        {
            "product_code": r.product_code,
            "product_description": r.product_description,
            "customer_name": r.customer_name,
        }
        for r in rows
    ]


def match_product_code(db: Session, extracted_code: str) -> list[dict]:
    """
    Fuzzy-match an extracted product code against the catalog.
    Returns candidates with confidence scores. Used by Phase 3 LLM extraction.

    Strategy (in order):
      1. Exact match          -> confidence 1.0
      2. Case-insensitive     -> confidence 0.9
      3. Partial (ILIKE)      -> confidence 0.6
    """
    if not extracted_code or not extracted_code.strip():
        return []

    code = extracted_code.strip()

    # 1. Exact match
    exact = db.query(Product).filter(Product.product_code == code).first()
    if exact:
        return [
            {
                "product_code": exact.product_code,
                "product_description": exact.product_description,
                "customer_name": exact.customer_name,
                "confidence": 1.0,
                "match_type": "exact",
            }
        ]

    # 2. Case-insensitive match
    ci = db.query(Product).filter(Product.product_code.ilike(code)).first()
    if ci:
        return [
            {
                "product_code": ci.product_code,
                "product_description": ci.product_description,
                "customer_name": ci.customer_name,
                "confidence": 0.9,
                "match_type": "case_insensitive",
            }
        ]

    # 3. Partial match on code or description
    pattern = f"%{code}%"
    partials = (
        db.query(Product)
        .filter(
            or_(
                Product.product_code.ilike(pattern),
                Product.product_description.ilike(pattern),
            )
        )
        .order_by(Product.product_code)
        .limit(5)
        .all()
    )

    return [
        {
            "product_code": p.product_code,
            "product_description": p.product_description,
            "customer_name": p.customer_name,
            "confidence": 0.6,
            "match_type": "partial",
        }
        for p in partials
    ]
