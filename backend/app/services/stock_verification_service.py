"""
Stock verification service — auto-creates verification tasks when orders are created,
confirms warehouse stock counts, and triggers works order generation when both
approval and verification are complete.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Order, OrderLineItem, StockVerification
from app.services.stock_service import get_stock_levels

logger = logging.getLogger(__name__)


def create_verifications_for_order(order_id: UUID, db: Session) -> list[StockVerification]:
    """
    Auto-create StockVerification records when an order is created.

    For each line item with a matched product_code + colour that has stock:
    - Create a verification with system_stock_quantity = current stock level
    - Status = 'pending'

    If no stock exists for a line item, no verification is created
    (full quantity must be produced).
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.error("Cannot create verifications: order %s not found", order_id)
        return []

    verifications = []

    for line_item in order.line_items:
        product_code = line_item.matched_product_code or line_item.product_code
        colour = line_item.colour

        if not product_code or not colour:
            continue

        # Check current stock for this product+colour
        levels = get_stock_levels(db, product_code=product_code, colour=colour)
        if not levels:
            continue

        stock_qty = levels[0]["total_quantity"]
        if stock_qty <= 0:
            continue

        verification = StockVerification(
            order_id=order.id,
            order_line_item_id=line_item.id,
            product_code=product_code,
            colour=colour,
            system_stock_quantity=stock_qty,
            status="pending",
        )
        db.add(verification)
        verifications.append(verification)

        logger.info(
            "Created verification for order %s, line %d: %s %s (%d in stock)",
            order.id, line_item.line_number, product_code, colour, stock_qty,
        )

    if verifications:
        db.flush()

    return verifications


def confirm_verification(
    verification_id: UUID,
    verified_quantity: int,
    user_id: UUID,
    db: Session,
    notes: Optional[str] = None,
) -> dict:
    """
    Warehouse confirms stock count for a verification task.

    1. Update verification: verified_quantity, verified_by, verified_at, status='confirmed'
    2. Check if all verifications for this order are now confirmed
    3. If yes AND order is approved -> trigger works order generation

    Returns dict with verification and whether works orders were triggered.
    """
    verification = (
        db.query(StockVerification)
        .filter(StockVerification.id == verification_id)
        .first()
    )
    if not verification:
        raise ValueError(f"Verification {verification_id} not found")

    if verification.status != "pending":
        raise ValueError(f"Verification is '{verification.status}', must be 'pending'")

    # Update verification
    verification.verified_quantity = verified_quantity
    verification.verified_by = user_id
    verification.verified_at = datetime.now(timezone.utc)
    verification.status = "confirmed"
    if notes:
        verification.notes = notes

    db.flush()

    # Check if we can generate works orders
    works_order_triggered = check_and_generate_works_orders(verification.order_id, db)

    return {
        "verification": verification,
        "works_order_triggered": works_order_triggered,
    }


def expire_verification(
    verification_id: UUID,
    db: Session,
    notes: Optional[str] = None,
) -> StockVerification:
    """
    Expire a pending verification when stock changes after it was created.

    1. Look up verification by ID
    2. Validate: status must be 'pending'
    3. Set status to 'expired', optionally add notes
    """
    verification = (
        db.query(StockVerification)
        .filter(StockVerification.id == verification_id)
        .first()
    )
    if not verification:
        raise ValueError(f"Verification {verification_id} not found")

    if verification.status != "pending":
        raise ValueError(f"Verification is '{verification.status}', must be 'pending' to expire")

    verification.status = "expired"
    if notes:
        verification.notes = notes

    db.flush()

    logger.info(
        "Expired verification %s for order %s (%s %s)",
        verification_id, verification.order_id, verification.product_code, verification.colour,
    )

    return verification


def check_and_generate_works_orders(order_id: UUID, db: Session) -> bool:
    """
    Check if all conditions are met to generate works orders:
    1. Order status is 'approved' (Sharon approved)
    2. All StockVerification records for this order are 'confirmed' (or none exist)
    3. Works orders have not already been generated

    Called after:
    - Sharon approves an order
    - Warehouse confirms a stock verification

    Returns True if works orders were generated.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return False

    # Must be approved (or verified if re-checking)
    if order.status not in ("approved", "verified"):
        return False

    # Check if works orders already generated
    if order.status == "works_order_generated":
        return False

    # Check if any line item already has a works order file (already generated)
    if any(li.works_order_file is not None for li in order.line_items):
        return False

    # Check all verifications are confirmed
    verifications = (
        db.query(StockVerification)
        .filter(StockVerification.order_id == order_id)
        .all()
    )

    pending = [v for v in verifications if v.status == "pending"]
    if pending:
        return False

    # All conditions met — generate works orders with adjusted quantities
    _generate_adjusted_works_orders(order, verifications, db)
    return True


def _generate_adjusted_works_orders(
    order: Order,
    verifications: list[StockVerification],
    db: Session,
) -> None:
    """
    Generate works orders with quantities adjusted for verified stock.

    WO quantity = ordered quantity - verified stock quantity
    If verified >= ordered, skip works order for that line item.
    """
    from app.services.form_generation_service import generate_office_order, generate_works_order

    # Build verification lookup: line_item_id -> verified_quantity
    verification_map: dict[UUID, int] = {}
    for v in verifications:
        if v.status == "confirmed" and v.verified_quantity is not None:
            verification_map[v.order_line_item_id] = v.verified_quantity

    logger.info(
        "Generating adjusted works orders for order %s (%d verifications)",
        order.id, len(verification_map),
    )

    # Mark as verified (approved + all stock verified)
    order.status = "verified"
    db.flush()

    # Generate office order (unchanged)
    office_bytes = generate_office_order(db, order)
    order.office_order_file = office_bytes

    # Generate works orders with adjusted quantities
    for item in order.line_items:
        verified_qty = verification_map.get(item.id, 0)
        adjusted_qty = calculate_adjusted_quantity(item.quantity, verified_qty)

        if adjusted_qty == 0:
            logger.info(
                "Skipping WO for line %d: verified %d >= ordered %d",
                item.line_number, verified_qty, item.quantity,
            )
            continue

        wo_bytes = generate_works_order(
            db, order, item,
            adjusted_quantity=adjusted_qty,
            verified_stock=verified_qty,
        )
        item.works_order_file = wo_bytes
        logger.info(
            "WO for line %d: ordered=%d, verified=%d, produce=%d",
            item.line_number, item.quantity, verified_qty, adjusted_qty,
        )

    # Update order status
    order.status = "works_order_generated"
    db.flush()

    logger.info("All forms generated for order %s (status: works_order_generated)", order.id)


def calculate_adjusted_quantity(ordered_qty: int, verified_qty: int) -> int:
    """
    WO quantity = ordered quantity - confirmed stock quantity.
    If verified >= ordered, return 0 (no production needed).
    """
    return max(0, ordered_qty - verified_qty)


def get_verification_status_for_order(order_id: UUID, db: Session) -> dict:
    """
    Get a summary of verification status for an order.
    Returns dict with total, pending, confirmed counts and list of verifications.
    """
    verifications = (
        db.query(StockVerification)
        .filter(StockVerification.order_id == order_id)
        .all()
    )

    pending = [v for v in verifications if v.status == "pending"]
    confirmed = [v for v in verifications if v.status == "confirmed"]

    return {
        "total": len(verifications),
        "pending": len(pending),
        "confirmed": len(confirmed),
        "all_confirmed": len(pending) == 0,
        "verifications": verifications,
    }
