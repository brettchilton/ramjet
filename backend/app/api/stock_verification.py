"""
Stock Verification API — verification tasks for order stock confirmation.

Warehouse staff use these endpoints to view pending verification tasks and
confirm/adjust stock counts. Confirming the last pending verification for an
approved order triggers works order generation with adjusted quantities.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_role, get_current_user
from app.core.database import get_db
from app.core.models import User, StockVerification, Order, OrderLineItem
from app.schemas.stock_schemas import StockVerificationConfirm, StockVerificationResponse, ExpireVerificationRequest
from app.services.stock_verification_service import confirm_verification, expire_verification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock-verifications", tags=["stock-verifications"])


# ── Pending Verifications ────────────────────────────────────────────

@router.get("/pending")
async def get_pending_verifications(
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """
    List all pending verification tasks, grouped by order.
    Returns order context alongside each verification for display.
    """
    verifications = (
        db.query(StockVerification)
        .filter(StockVerification.status == "pending")
        .order_by(StockVerification.created_at.asc())
        .all()
    )

    # Group by order and enrich with order context
    orders_map: dict[str, dict] = {}
    for v in verifications:
        order_key = str(v.order_id)
        if order_key not in orders_map:
            order = db.query(Order).filter(Order.id == v.order_id).first()
            orders_map[order_key] = {
                "order_id": str(v.order_id),
                "customer_name": order.customer_name if order else None,
                "po_number": order.po_number if order else None,
                "order_status": order.status if order else None,
                "created_at": order.created_at.isoformat() if order and order.created_at else None,
                "verifications": [],
            }

        # Get line item context
        line_item = (
            db.query(OrderLineItem)
            .filter(OrderLineItem.id == v.order_line_item_id)
            .first()
        )

        orders_map[order_key]["verifications"].append({
            "id": str(v.id),
            "order_line_item_id": str(v.order_line_item_id),
            "product_code": v.product_code,
            "colour": v.colour,
            "system_stock_quantity": v.system_stock_quantity,
            "verified_quantity": v.verified_quantity,
            "status": v.status,
            "line_number": line_item.line_number if line_item else None,
            "ordered_quantity": line_item.quantity if line_item else None,
            "product_description": line_item.product_description if line_item else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    return list(orders_map.values())


# ── Verifications for Order ──────────────────────────────────────────

@router.get("/order/{order_id}")
async def get_order_verifications(
    order_id: UUID,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """Get all verification tasks for a specific order."""
    verifications = (
        db.query(StockVerification)
        .filter(StockVerification.order_id == order_id)
        .order_by(StockVerification.created_at.asc())
        .all()
    )

    result = []
    for v in verifications:
        line_item = (
            db.query(OrderLineItem)
            .filter(OrderLineItem.id == v.order_line_item_id)
            .first()
        )
        result.append({
            "id": str(v.id),
            "order_id": str(v.order_id),
            "order_line_item_id": str(v.order_line_item_id),
            "product_code": v.product_code,
            "colour": v.colour,
            "system_stock_quantity": v.system_stock_quantity,
            "verified_quantity": v.verified_quantity,
            "status": v.status,
            "verified_by": str(v.verified_by) if v.verified_by else None,
            "verified_at": v.verified_at.isoformat() if v.verified_at else None,
            "notes": v.notes,
            "line_number": line_item.line_number if line_item else None,
            "ordered_quantity": line_item.quantity if line_item else None,
            "product_description": line_item.product_description if line_item else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    return result


# ── Confirm Verification ─────────────────────────────────────────────

@router.post("/{verification_id}/confirm")
async def confirm_stock_verification(
    verification_id: UUID,
    body: StockVerificationConfirm,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """
    Confirm/adjust stock count for a verification task.

    If this is the last pending verification for an approved order,
    works orders are generated with adjusted quantities.
    """
    try:
        result = confirm_verification(
            verification_id=verification_id,
            verified_quantity=body.verified_quantity,
            user_id=current_user.id,
            db=db,
            notes=body.notes,
        )
        db.commit()

        verification = result["verification"]
        db.refresh(verification)

        message = f"Stock verified: {verification.product_code} {verification.colour} — {body.verified_quantity} units"
        if result["works_order_triggered"]:
            message += ". Works orders generated."

        return {
            "verification_id": str(verification.id),
            "status": verification.status,
            "verified_quantity": verification.verified_quantity,
            "works_order_triggered": result["works_order_triggered"],
            "message": message,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Expire Verification ─────────────────────────────────────────────

@router.post("/{verification_id}/expire")
async def expire_stock_verification(
    verification_id: UUID,
    body: ExpireVerificationRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Expire a pending verification when stock has changed.

    Admin-only. Sets the verification status to 'expired'.
    """
    try:
        verification = expire_verification(
            verification_id=verification_id,
            db=db,
            notes=body.notes,
        )
        db.commit()
        db.refresh(verification)

        return {
            "verification_id": str(verification.id),
            "status": verification.status,
            "message": f"Verification expired for {verification.product_code} {verification.colour}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
