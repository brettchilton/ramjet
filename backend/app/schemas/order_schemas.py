from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ── Line item response ─────────────────────────────────────────────────

class OrderLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    line_number: int
    product_code: Optional[str] = None
    matched_product_code: Optional[str] = None
    product_description: Optional[str] = None
    colour: Optional[str] = None
    quantity: int
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    confidence: Optional[Decimal] = None
    needs_review: bool = False
    created_at: Optional[datetime] = None


# ── Order summary (list view) ──────────────────────────────────────────

class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    customer_name: Optional[str] = None
    po_number: Optional[str] = None
    extraction_confidence: Optional[Decimal] = None
    line_item_count: int = 0
    has_forms: bool = False
    created_at: Optional[datetime] = None


# ── Order detail (with line items) ─────────────────────────────────────

class OrderDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email_id: Optional[int] = None
    status: str
    customer_name: Optional[str] = None
    po_number: Optional[str] = None
    po_date: Optional[date] = None
    delivery_date: Optional[date] = None
    special_instructions: Optional[str] = None
    extraction_confidence: Optional[Decimal] = None
    extraction_raw_json: Optional[dict] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    has_office_order: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    line_items: list[OrderLineItemResponse] = []


# ── Processing responses ───────────────────────────────────────────────

class ProcessEmailsResponse(BaseModel):
    orders_created: int
    errors: int
    message: str


class ProcessSingleResponse(BaseModel):
    order_id: Optional[UUID] = None
    message: str


# ── Update requests ───────────────────────────────────────────────────

class OrderUpdateRequest(BaseModel):
    customer_name: Optional[str] = None
    po_number: Optional[str] = None
    po_date: Optional[date] = None
    delivery_date: Optional[date] = None
    special_instructions: Optional[str] = None


class LineItemUpdateRequest(BaseModel):
    product_code: Optional[str] = None
    matched_product_code: Optional[str] = None
    product_description: Optional[str] = None
    colour: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None


# ── Approve / Reject ──────────────────────────────────────────────────

class RejectRequest(BaseModel):
    reason: str


class ApproveResponse(BaseModel):
    order_id: UUID
    status: str
    message: str
    office_order_generated: bool
    works_orders_generated: int


class RejectResponse(BaseModel):
    order_id: UUID
    status: str
    message: str
