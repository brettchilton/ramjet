"""
Raw Material Pydantic schemas — CRUD, movements, and list responses with threshold status.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ── Raw Material ──────────────────────────────────────────────────────

class RawMaterialCreate(BaseModel):
    material_code: str
    material_name: str
    material_type: str  # resin | masterbatch | additive | packaging | other
    unit_of_measure: str  # kg | litres | units | rolls
    red_threshold: Decimal = Decimal("0")
    amber_threshold: Decimal = Decimal("0")
    default_supplier: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class RawMaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    material_type: Optional[str] = None
    unit_of_measure: Optional[str] = None
    red_threshold: Optional[Decimal] = None
    amber_threshold: Optional[Decimal] = None
    default_supplier: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RawMaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_code: str
    material_name: str
    material_type: str
    unit_of_measure: str
    current_stock: Decimal
    red_threshold: Decimal
    amber_threshold: Decimal
    default_supplier: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RawMaterialWithStatus(RawMaterialResponse):
    """Response with computed threshold status for list views."""
    threshold_status: str = "green"  # green | amber | red


# ── Raw Material Movement ─────────────────────────────────────────────

class RawMaterialMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_material_id: UUID
    movement_type: str
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    supplier: Optional[str] = None
    delivery_note: Optional[str] = None
    reason: Optional[str] = None
    performed_by: UUID
    performed_by_name: Optional[str] = None
    created_at: datetime


class RawMaterialReceiveRequest(BaseModel):
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    supplier: Optional[str] = None
    delivery_note: Optional[str] = None


class RawMaterialUseRequest(BaseModel):
    quantity: Decimal
    reason: Optional[str] = None


class RawMaterialAdjustmentRequest(BaseModel):
    quantity: Decimal  # positive = in, negative = out
    reason: str  # mandatory for adjustments


# ── Detail (material + movements) ────────────────────────────────────

class RawMaterialDetailResponse(RawMaterialWithStatus):
    """Full detail including movement history."""
    movements: list[RawMaterialMovementResponse] = []
