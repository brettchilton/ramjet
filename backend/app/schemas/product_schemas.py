from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from decimal import Decimal


# ── List / Search responses ─────────────────────────────────────────────

class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_code: str
    product_description: str
    customer_name: Optional[str] = None
    is_active: bool = True
    is_stockable: bool = True


# ── Nested detail models ────────────────────────────────────────────────

class ManufacturingSpecResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mould_no: Optional[str] = None
    cycle_time_seconds: Optional[int] = None
    shot_weight_grams: Optional[Decimal] = None
    num_cavities: Optional[int] = None
    product_weight_grams: Optional[Decimal] = None
    estimated_running_time_hours: Optional[Decimal] = None
    machine_min_requirements: Optional[str] = None


class MaterialSpecResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    colour: str
    material_grade: Optional[str] = None
    material_type: Optional[str] = None
    colour_no: Optional[str] = None
    colour_supplier: Optional[str] = None
    mb_add_rate: Optional[Decimal] = None
    additive: Optional[str] = None
    additive_add_rate: Optional[Decimal] = None
    additive_supplier: Optional[str] = None


class PackagingSpecResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    qty_per_bag: Optional[int] = None
    bag_size: Optional[str] = None
    qty_per_carton: Optional[int] = None
    carton_size: Optional[str] = None
    cartons_per_pallet: Optional[int] = None
    cartons_per_layer: Optional[int] = None


class PricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    colour: str
    customer_name: Optional[str] = None
    unit_price: Decimal
    currency: str = "AUD"
    effective_date: Optional[date] = None


# ── Full product detail response ────────────────────────────────────────

class ProductFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_code: str
    product_description: str
    customer_name: Optional[str] = None
    is_active: bool = True
    is_stockable: bool = True
    manufacturing: Optional[ManufacturingSpecResponse] = None
    materials: list[MaterialSpecResponse] = []
    packaging: Optional[PackagingSpecResponse] = None
    pricing: list[PricingResponse] = []


# ── Calculation response ────────────────────────────────────────────────

class MaterialRequirements(BaseModel):
    base_material_kg: float
    material_grade: Optional[str] = None
    material_type: Optional[str] = None
    masterbatch_kg: float
    colour_no: Optional[str] = None
    colour_supplier: Optional[str] = None
    additive_kg: float
    additive: Optional[str] = None
    additive_supplier: Optional[str] = None
    total_material_kg: float


class PackagingRequirements(BaseModel):
    bags_needed: int
    bag_size: Optional[str] = None
    cartons_needed: int
    carton_size: Optional[str] = None


class CalculationResponse(BaseModel):
    product_code: str
    colour: str
    quantity: int
    material_requirements: MaterialRequirements
    packaging_requirements: PackagingRequirements
    estimated_cost: float


# ── CRUD request models ────────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_code: str
    product_description: str
    customer_name: Optional[str] = None
    is_stockable: bool = True


class ProductUpdate(BaseModel):
    product_description: Optional[str] = None
    customer_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_stockable: Optional[bool] = None


# ── Fuzzy match response ────────────────────────────────────────────────

class ProductMatch(BaseModel):
    product_code: str
    product_description: str
    customer_name: Optional[str] = None
    confidence: float
    match_type: str
