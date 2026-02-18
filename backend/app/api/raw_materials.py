"""
Raw Materials API — CRUD, receive, use, adjust raw material inventory.
All endpoints require admin role.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.models import RawMaterial, User
from app.core.auth import require_role, get_current_user
from app.schemas.raw_material_schemas import (
    RawMaterialCreate,
    RawMaterialUpdate,
    RawMaterialResponse,
    RawMaterialWithStatus,
    RawMaterialDetailResponse,
    RawMaterialMovementResponse,
    RawMaterialReceiveRequest,
    RawMaterialUseRequest,
    RawMaterialAdjustmentRequest,
)
from app.services.raw_material_service import (
    get_raw_materials_with_status,
    get_raw_material_detail,
    receive_delivery,
    record_usage,
    adjust_stock,
)

router = APIRouter(prefix="/api/raw-materials", tags=["raw-materials"])


# ── List ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[RawMaterialWithStatus], dependencies=[Depends(require_role("admin"))])
def list_raw_materials(
    search: Optional[str] = Query(None, description="Search by code or name"),
    material_type: Optional[str] = Query(None, description="Filter by type"),
    db: Session = Depends(get_db),
):
    return get_raw_materials_with_status(db, search=search, material_type=material_type)


# ── Detail ────────────────────────────────────────────────────────────

@router.get("/{material_id}", response_model=RawMaterialDetailResponse, dependencies=[Depends(require_role("admin"))])
def get_raw_material(
    material_id: UUID,
    db: Session = Depends(get_db),
):
    return get_raw_material_detail(db, material_id)


# ── Create ────────────────────────────────────────────────────────────

@router.post("/", response_model=RawMaterialResponse, dependencies=[Depends(require_role("admin"))])
def create_raw_material(
    payload: RawMaterialCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(RawMaterial).filter(RawMaterial.material_code == payload.material_code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Material '{payload.material_code}' already exists")

    material = RawMaterial(
        material_code=payload.material_code,
        material_name=payload.material_name,
        material_type=payload.material_type,
        unit_of_measure=payload.unit_of_measure,
        red_threshold=payload.red_threshold,
        amber_threshold=payload.amber_threshold,
        default_supplier=payload.default_supplier,
        unit_cost=payload.unit_cost,
        notes=payload.notes,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


# ── Update ────────────────────────────────────────────────────────────

@router.put("/{material_id}", response_model=RawMaterialResponse, dependencies=[Depends(require_role("admin"))])
def update_raw_material(
    material_id: UUID,
    payload: RawMaterialUpdate,
    db: Session = Depends(get_db),
):
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    db.commit()
    db.refresh(material)
    return material


# ── Soft Delete ───────────────────────────────────────────────────────

@router.delete("/{material_id}", dependencies=[Depends(require_role("admin"))])
def delete_raw_material(
    material_id: UUID,
    db: Session = Depends(get_db),
):
    material = db.query(RawMaterial).filter(RawMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    material.is_active = False
    db.commit()
    return {"message": f"Raw material '{material.material_code}' deactivated"}


# ── Receive Delivery ─────────────────────────────────────────────────

@router.post("/{material_id}/receive", response_model=RawMaterialMovementResponse, dependencies=[Depends(require_role("admin"))])
def receive_raw_material(
    material_id: UUID,
    payload: RawMaterialReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movement = receive_delivery(
        material_id=material_id,
        quantity=payload.quantity,
        user_id=current_user.id,
        db=db,
        supplier=payload.supplier,
        delivery_note=payload.delivery_note,
        unit_cost=payload.unit_cost,
    )
    return movement


# ── Record Usage ─────────────────────────────────────────────────────

@router.post("/{material_id}/use", response_model=RawMaterialMovementResponse, dependencies=[Depends(require_role("admin"))])
def use_raw_material(
    material_id: UUID,
    payload: RawMaterialUseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movement = record_usage(
        material_id=material_id,
        quantity=payload.quantity,
        user_id=current_user.id,
        db=db,
        reason=payload.reason,
    )
    return movement


# ── Manual Adjustment ─────────────────────────────────────────────────

@router.post("/{material_id}/adjustment", response_model=RawMaterialMovementResponse, dependencies=[Depends(require_role("admin"))])
def adjust_raw_material(
    material_id: UUID,
    payload: RawMaterialAdjustmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movement = adjust_stock(
        material_id=material_id,
        quantity=payload.quantity,
        reason=payload.reason,
        user_id=current_user.id,
        db=db,
    )
    return movement
