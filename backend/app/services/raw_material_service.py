"""
Raw Material Service — receive deliveries, record usage, adjust stock, query with threshold status.
"""

from decimal import Decimal
from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException

from app.core.models import RawMaterial, RawMaterialMovement


def _threshold_status(material: RawMaterial) -> str:
    """Compute green/amber/red status from current_stock vs thresholds."""
    stock = material.current_stock or Decimal("0")
    if stock < material.red_threshold:
        return "red"
    if stock < material.amber_threshold:
        return "amber"
    return "green"


def get_raw_materials_with_status(
    db: Session,
    search: Optional[str] = None,
    material_type: Optional[str] = None,
    include_inactive: bool = False,
) -> list[dict]:
    """Return all raw materials with computed threshold_status."""
    query = db.query(RawMaterial)

    if not include_inactive:
        query = query.filter(RawMaterial.is_active == True)

    if material_type:
        query = query.filter(RawMaterial.material_type == material_type)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                RawMaterial.material_code.ilike(term),
                RawMaterial.material_name.ilike(term),
            )
        )

    materials = query.order_by(RawMaterial.material_name).all()

    results = []
    for m in materials:
        data = {
            "id": m.id,
            "material_code": m.material_code,
            "material_name": m.material_name,
            "material_type": m.material_type,
            "unit_of_measure": m.unit_of_measure,
            "current_stock": m.current_stock,
            "red_threshold": m.red_threshold,
            "amber_threshold": m.amber_threshold,
            "default_supplier": m.default_supplier,
            "unit_cost": m.unit_cost,
            "is_active": m.is_active,
            "notes": m.notes,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "threshold_status": _threshold_status(m),
        }
        results.append(data)
    return results


def get_raw_material_detail(db: Session, material_id: UUID) -> dict:
    """Return a single raw material with movement history."""
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    movements = (
        db.query(RawMaterialMovement)
        .filter(RawMaterialMovement.raw_material_id == material_id)
        .order_by(RawMaterialMovement.created_at.desc())
        .all()
    )

    movement_list = []
    for mv in movements:
        performer = mv.performer
        movement_list.append({
            "id": mv.id,
            "raw_material_id": mv.raw_material_id,
            "movement_type": mv.movement_type,
            "quantity": mv.quantity,
            "unit_cost": mv.unit_cost,
            "supplier": mv.supplier,
            "delivery_note": mv.delivery_note,
            "reason": mv.reason,
            "performed_by": mv.performed_by,
            "performed_by_name": f"{performer.first_name} {performer.last_name}" if performer else None,
            "created_at": mv.created_at,
        })

    return {
        "id": material.id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "material_type": material.material_type,
        "unit_of_measure": material.unit_of_measure,
        "current_stock": material.current_stock,
        "red_threshold": material.red_threshold,
        "amber_threshold": material.amber_threshold,
        "default_supplier": material.default_supplier,
        "unit_cost": material.unit_cost,
        "is_active": material.is_active,
        "notes": material.notes,
        "created_at": material.created_at,
        "updated_at": material.updated_at,
        "threshold_status": _threshold_status(material),
        "movements": movement_list,
    }


def receive_delivery(
    material_id: UUID,
    quantity: Decimal,
    user_id: UUID,
    db: Session,
    supplier: Optional[str] = None,
    delivery_note: Optional[str] = None,
    unit_cost: Optional[Decimal] = None,
) -> RawMaterialMovement:
    """Record a delivery received — increases current_stock."""
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    movement = RawMaterialMovement(
        raw_material_id=material_id,
        movement_type="received",
        quantity=quantity,
        unit_cost=unit_cost,
        supplier=supplier,
        delivery_note=delivery_note,
        performed_by=user_id,
    )
    db.add(movement)

    material.current_stock = (material.current_stock or Decimal("0")) + quantity
    if unit_cost is not None:
        material.unit_cost = unit_cost

    db.commit()
    db.refresh(movement)
    return movement


def record_usage(
    material_id: UUID,
    quantity: Decimal,
    user_id: UUID,
    db: Session,
    reason: Optional[str] = None,
) -> RawMaterialMovement:
    """Record material used — decreases current_stock. Cannot go negative."""
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    if quantity > (material.current_stock or Decimal("0")):
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {material.current_stock}, requested: {quantity}",
        )

    movement = RawMaterialMovement(
        raw_material_id=material_id,
        movement_type="used",
        quantity=-quantity,  # negative for usage
        reason=reason,
        performed_by=user_id,
    )
    db.add(movement)

    material.current_stock = (material.current_stock or Decimal("0")) - quantity

    db.commit()
    db.refresh(movement)
    return movement


def adjust_stock(
    material_id: UUID,
    quantity: Decimal,
    reason: str,
    user_id: UUID,
    db: Session,
) -> RawMaterialMovement:
    """Manual stock adjustment — reason is mandatory."""
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    new_stock = (material.current_stock or Decimal("0")) + quantity
    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment would result in negative stock ({new_stock})",
        )

    movement = RawMaterialMovement(
        raw_material_id=material_id,
        movement_type="adjustment",
        quantity=quantity,
        reason=reason,
        performed_by=user_id,
    )
    db.add(movement)

    material.current_stock = new_stock

    db.commit()
    db.refresh(movement)
    return movement
