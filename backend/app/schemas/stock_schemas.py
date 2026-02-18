from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ── Stock Item ────────────────────────────────────────────────────────

class StockItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    barcode_id: str
    product_code: str
    colour: str
    quantity: int
    box_type: str
    status: str
    production_date: Optional[date] = None
    scanned_in_at: Optional[datetime] = None
    scanned_out_at: Optional[datetime] = None
    order_id: Optional[UUID] = None
    parent_stock_item_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockItemCreate(BaseModel):
    barcode_id: str
    product_code: str
    colour: str
    quantity: int
    box_type: str = "full"
    production_date: Optional[date] = None
    notes: Optional[str] = None


# ── Stock Movement ────────────────────────────────────────────────────

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_item_id: UUID
    movement_type: str
    quantity_change: int
    reason: Optional[str] = None
    order_id: Optional[UUID] = None
    stocktake_session_id: Optional[UUID] = None
    performed_by: UUID
    created_at: datetime


class StockAdjustmentRequest(BaseModel):
    stock_item_id: UUID
    quantity_change: int
    reason: str  # mandatory for adjustments


# ── Stock Threshold ───────────────────────────────────────────────────

class StockThresholdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str
    colour: Optional[str] = None
    red_threshold: int
    amber_threshold: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockThresholdCreate(BaseModel):
    product_code: str
    colour: Optional[str] = None
    red_threshold: int = 0
    amber_threshold: int = 0


class StockThresholdUpdate(BaseModel):
    red_threshold: Optional[int] = None
    amber_threshold: Optional[int] = None


# ── Stock Verification ────────────────────────────────────────────────

class StockVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    order_line_item_id: UUID
    product_code: str
    colour: str
    system_stock_quantity: int
    verified_quantity: Optional[int] = None
    status: str
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockVerificationConfirm(BaseModel):
    verified_quantity: int
    notes: Optional[str] = None


class ExpireVerificationRequest(BaseModel):
    notes: Optional[str] = None


# ── Stocktake Session ─────────────────────────────────────────────────

class StocktakeSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: Optional[str] = None
    status: str
    started_by: UUID
    completed_by: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_expected: Optional[int] = None
    total_scanned: Optional[int] = None
    total_discrepancies: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StocktakeSessionCreate(BaseModel):
    name: str
    notes: Optional[str] = None


class StocktakeScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    barcode_scanned: str
    stock_item_id: Optional[UUID] = None
    scan_result: str
    scanned_by: UUID
    scanned_at: datetime
    notes: Optional[str] = None


class StocktakeScanRequest(BaseModel):
    barcode_scanned: str
    notes: Optional[str] = None


# ── Label Generation ──────────────────────────────────────────────────

class LabelGenerateRequest(BaseModel):
    product_code: str
    colour: str
    quantity_per_carton: int
    number_of_labels: int
    box_type: str = "full"  # full | partial
    production_date: Optional[date] = None


class LabelGenerateResponse(BaseModel):
    barcode_ids: list[str]
    stock_item_count: int
    message: str


# ── Scan Events ───────────────────────────────────────────────────────

class ScanInRequest(BaseModel):
    barcode_id: str
    notes: Optional[str] = None


class ScanOutRequest(BaseModel):
    barcode_id: str
    order_id: Optional[UUID] = None
    notes: Optional[str] = None


class PartialRepackRequest(BaseModel):
    barcode_id: str
    units_taken: int
    order_id: Optional[UUID] = None


class PartialRepackResponse(BaseModel):
    success: bool
    original_item: Optional[StockItemResponse] = None
    new_partial_item: Optional[StockItemResponse] = None
    units_taken: int = 0
    units_remaining: int = 0
    label_url: Optional[str] = None
    message: str
    error: Optional[str] = None


class ScanResponse(BaseModel):
    success: bool
    stock_item: Optional[StockItemResponse] = None
    movement: Optional[StockMovementResponse] = None
    message: str
    error: Optional[str] = None
    barcode_id: Optional[str] = None
    product_description: Optional[str] = None


# ── Stock Summary ─────────────────────────────────────────────────────

class StockSummaryItem(BaseModel):
    product_code: str
    product_description: Optional[str] = None
    colour: str
    total_units: int = 0
    carton_count: int = 0
    threshold_status: Optional[str] = None  # green | amber | red
    red_threshold: Optional[int] = None
    amber_threshold: Optional[int] = None


class StockSummaryTotals(BaseModel):
    total_skus: int = 0
    total_units: int = 0
    total_cartons: int = 0
    low_stock_count: int = 0


class StockSummaryResponse(BaseModel):
    summary: StockSummaryTotals
    items: list[StockSummaryItem]


# ── Stock Item Detail ─────────────────────────────────────────────────

class StockMovementDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_item_id: UUID
    movement_type: str
    quantity_change: int
    reason: Optional[str] = None
    order_id: Optional[UUID] = None
    stocktake_session_id: Optional[UUID] = None
    performed_by: UUID
    created_at: datetime


class StockItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    barcode_id: str
    product_code: str
    product_description: Optional[str] = None
    colour: str
    quantity: int
    box_type: str
    status: str
    production_date: Optional[date] = None
    scanned_in_at: Optional[datetime] = None
    scanned_in_by: Optional[UUID] = None
    scanned_out_at: Optional[datetime] = None
    scanned_out_by: Optional[UUID] = None
    order_id: Optional[UUID] = None
    parent_stock_item_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    movements: list[StockMovementDetailResponse] = []


# ── Stock Item List ───────────────────────────────────────────────────

class StockItemListResponse(BaseModel):
    items: list[StockItemResponse]
    total: int
