"""
Orders API — list orders, get details, trigger extraction processing,
approve/reject, update, and download generated forms.
"""

import asyncio
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Order, OrderLineItem, IncomingEmail, EmailAttachment
from app.schemas.order_schemas import (
    ApproveResponse,
    LineItemUpdateRequest,
    OrderDetail,
    OrderLineItemResponse,
    OrderSummary,
    OrderUpdateRequest,
    ProcessEmailsResponse,
    ProcessSingleResponse,
    RejectRequest,
    RejectResponse,
)
from app.services.extraction_service import (
    process_unprocessed_emails,
    process_single_email,
)
from app.services.form_generation_service import generate_all_forms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ── Helpers ───────────────────────────────────────────────────────────

def _get_order_or_404(db: Session, order_id: UUID) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


def _require_pending(order: Order) -> None:
    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Order is '{order.status}', must be 'pending'",
        )


# ── List / Detail ─────────────────────────────────────────────────────

@router.get("/", response_model=list[OrderSummary])
def list_orders(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, error)"),
    db: Session = Depends(get_db),
):
    """List orders with optional status filter."""
    query = db.query(Order).order_by(Order.created_at.desc())

    if status:
        query = query.filter(Order.status == status)

    orders = query.all()

    return [
        OrderSummary(
            id=order.id,
            status=order.status,
            customer_name=order.customer_name,
            po_number=order.po_number,
            extraction_confidence=order.extraction_confidence,
            line_item_count=len(order.line_items),
            has_forms=order.office_order_file is not None,
            created_at=order.created_at,
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderDetail)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    """Get full order detail with line items."""
    order = _get_order_or_404(db, order_id)
    # Build response manually to populate has_office_order
    return OrderDetail(
        id=order.id,
        email_id=order.email_id,
        status=order.status,
        customer_name=order.customer_name,
        po_number=order.po_number,
        po_date=order.po_date,
        delivery_date=order.delivery_date,
        special_instructions=order.special_instructions,
        extraction_confidence=order.extraction_confidence,
        extraction_raw_json=order.extraction_raw_json,
        approved_by=order.approved_by,
        approved_at=order.approved_at,
        rejected_reason=order.rejected_reason,
        has_office_order=order.office_order_file is not None,
        created_at=order.created_at,
        updated_at=order.updated_at,
        line_items=[OrderLineItemResponse.model_validate(li) for li in order.line_items],
    )


# ── Update order / line items ─────────────────────────────────────────

@router.put("/{order_id}", response_model=OrderDetail)
def update_order(order_id: UUID, body: OrderUpdateRequest, db: Session = Depends(get_db)):
    """Update order header fields. Pending orders only."""
    order = _get_order_or_404(db, order_id)
    _require_pending(order)

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return get_order(order_id, db)


@router.put("/{order_id}/line-items/{item_id}", response_model=OrderLineItemResponse)
def update_line_item(
    order_id: UUID,
    item_id: UUID,
    body: LineItemUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a line item and recalculate line_total. Pending orders only."""
    order = _get_order_or_404(db, order_id)
    _require_pending(order)

    item = (
        db.query(OrderLineItem)
        .filter(OrderLineItem.id == item_id, OrderLineItem.order_id == order_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Line item {item_id} not found on order {order_id}")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(item, field, value)

    # Recalculate line_total
    if item.quantity is not None and item.unit_price is not None:
        item.line_total = item.quantity * item.unit_price

    db.commit()
    db.refresh(item)
    return item


# ── Approve / Reject ──────────────────────────────────────────────────

@router.post("/{order_id}/approve", response_model=ApproveResponse)
async def approve_order(order_id: UUID, db: Session = Depends(get_db)):
    """Approve an order and generate all forms."""
    order = _get_order_or_404(db, order_id)
    _require_pending(order)

    if not order.line_items:
        raise HTTPException(status_code=400, detail="Order has no line items")

    # Generate forms (CPU-bound, run in executor)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, generate_all_forms, db, order)

    # Update status
    order.status = "approved"
    order.approved_at = datetime.now(timezone.utc)
    db.commit()

    return ApproveResponse(
        order_id=order.id,
        status=order.status,
        message="Order approved and forms generated",
        office_order_generated=order.office_order_file is not None,
        works_orders_generated=len([li for li in order.line_items if li.works_order_file is not None]),
    )


@router.post("/{order_id}/reject", response_model=RejectResponse)
def reject_order(order_id: UUID, body: RejectRequest, db: Session = Depends(get_db)):
    """Reject an order with a reason."""
    order = _get_order_or_404(db, order_id)
    _require_pending(order)

    order.status = "rejected"
    order.rejected_reason = body.reason
    db.commit()

    return RejectResponse(
        order_id=order.id,
        status=order.status,
        message="Order rejected",
    )


# ── Form downloads ────────────────────────────────────────────────────

@router.get("/{order_id}/forms/office-order")
def download_office_order(order_id: UUID, db: Session = Depends(get_db)):
    """Download the generated Office Order .xlsx file."""
    order = _get_order_or_404(db, order_id)

    if not order.office_order_file:
        raise HTTPException(status_code=404, detail="Office order not yet generated")

    filename = f"Office_Order_{order.po_number or order_id}.xlsx"
    return StreamingResponse(
        BytesIO(order.office_order_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{order_id}/forms/works-order/{item_id}")
def download_works_order(order_id: UUID, item_id: UUID, db: Session = Depends(get_db)):
    """Download a generated Works Order .xlsx file for a specific line item."""
    order = _get_order_or_404(db, order_id)

    item = (
        db.query(OrderLineItem)
        .filter(OrderLineItem.id == item_id, OrderLineItem.order_id == order_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Line item {item_id} not found on order {order_id}")

    if not item.works_order_file:
        raise HTTPException(status_code=404, detail="Works order not yet generated")

    filename = f"Works_Order_WO-{order.po_number or order_id}-{item.line_number}.xlsx"
    return StreamingResponse(
        BytesIO(item.works_order_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{order_id}/source-pdf/{attachment_id}")
def download_source_attachment(order_id: UUID, attachment_id: int, db: Session = Depends(get_db)):
    """Download an original email attachment (source PDF/document)."""
    order = _get_order_or_404(db, order_id)

    if not order.email_id:
        raise HTTPException(status_code=404, detail="Order has no linked email")

    attachment = (
        db.query(EmailAttachment)
        .filter(
            EmailAttachment.id == attachment_id,
            EmailAttachment.email_id == order.email_id,
        )
        .first()
    )
    if not attachment:
        raise HTTPException(status_code=404, detail=f"Attachment {attachment_id} not found")

    if not attachment.file_data:
        raise HTTPException(status_code=404, detail="Attachment has no file data")

    return StreamingResponse(
        BytesIO(attachment.file_data),
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment.filename or "attachment"}"'},
    )


# ── Extraction processing ────────────────────────────────────────────

@router.post("/process-pending", response_model=ProcessEmailsResponse)
async def process_pending_emails(db: Session = Depends(get_db)):
    """Process all unprocessed emails and create orders."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, process_unprocessed_emails, db)
    return ProcessEmailsResponse(**result)


@router.post("/process-email/{email_id}", response_model=ProcessSingleResponse)
async def process_single_email_endpoint(email_id: int, db: Session = Depends(get_db)):
    """Process a single email by ID."""
    email = db.query(IncomingEmail).filter(IncomingEmail.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

    if email.processed:
        # Check if there's already an order for this email
        existing = db.query(Order).filter(Order.email_id == email_id).first()
        if existing:
            return ProcessSingleResponse(
                order_id=existing.id,
                message=f"Email already processed — order {existing.id} exists",
            )

    loop = asyncio.get_event_loop()
    order = await loop.run_in_executor(None, process_single_email, db, email)

    if order:
        return ProcessSingleResponse(
            order_id=order.id,
            message=f"Order created with status '{order.status}'",
        )
    return ProcessSingleResponse(
        order_id=None,
        message="Failed to process email",
    )


@router.post("/{order_id}/reprocess", response_model=ProcessSingleResponse)
async def reprocess_order(order_id: UUID, db: Session = Depends(get_db)):
    """Re-extract order data from the source email."""
    order = _get_order_or_404(db, order_id)

    if not order.email_id:
        raise HTTPException(status_code=400, detail="Order has no linked email")

    email = db.query(IncomingEmail).filter(IncomingEmail.id == order.email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Source email not found")

    # Delete existing line items and reset order
    db.query(OrderLineItem).filter(OrderLineItem.order_id == order.id).delete()
    db.delete(order)
    db.commit()

    # Re-process
    email.processed = False
    db.commit()

    loop = asyncio.get_event_loop()
    new_order = await loop.run_in_executor(None, process_single_email, db, email)

    if new_order:
        return ProcessSingleResponse(
            order_id=new_order.id,
            message=f"Reprocessed — new order created with status '{new_order.status}'",
        )
    return ProcessSingleResponse(
        order_id=None,
        message="Failed to reprocess email",
    )
