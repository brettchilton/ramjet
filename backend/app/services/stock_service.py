"""
Stock service — scan-in/out logic, status transitions, stock level calculation,
stock summary with thresholds, and threshold CRUD.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.models import StockItem, StockMovement, StockThreshold, Product
from app.services.barcode_service import generate_barcode_ids, generate_single_label_pdf

logger = logging.getLogger(__name__)


# ── Scan-In ──────────────────────────────────────────────────────────

def scan_in(
    barcode_id: str,
    user_id: UUID,
    db: Session,
    notes: Optional[str] = None,
) -> dict:
    """
    Process a stock-in scan event.

    1. Look up StockItem by barcode_id
    2. Validate: item exists, status allows scan-in
    3. Update StockItem: status -> 'in_stock', scanned_in_at, scanned_in_by
    4. Create StockMovement: movement_type='stock_in', quantity_change=+quantity
    5. Return result dict with item and movement
    """
    # Look up by barcode
    stock_item = (
        db.query(StockItem)
        .filter(StockItem.barcode_id == barcode_id)
        .first()
    )

    if not stock_item:
        raise ValueError(f"Barcode not recognised: {barcode_id}")

    # Validate status transition
    if stock_item.status == "in_stock":
        raise ValueError("Already scanned in")
    if stock_item.status in ("picked", "scrapped", "consumed"):
        raise ValueError(f"Cannot scan in — item has been {stock_item.status}")

    # Only pending_scan items can be scanned in
    if stock_item.status != "pending_scan":
        raise ValueError(f"Unexpected status: {stock_item.status}")

    # Transition to in_stock
    now = datetime.now(timezone.utc)
    stock_item.status = "in_stock"
    stock_item.scanned_in_at = now
    stock_item.scanned_in_by = user_id
    if notes:
        stock_item.notes = notes

    # Create movement record
    movement = StockMovement(
        stock_item_id=stock_item.id,
        movement_type="stock_in",
        quantity_change=stock_item.quantity,
        performed_by=user_id,
    )
    db.add(movement)
    db.flush()

    logger.info(
        "Scanned in: %s (%s %s, %d units)",
        barcode_id, stock_item.product_code, stock_item.colour, stock_item.quantity,
    )

    return {
        "stock_item": stock_item,
        "movement": movement,
    }


# ── Stock Level Calculation ──────────────────────────────────────────

def get_stock_levels(
    db: Session,
    product_code: Optional[str] = None,
    colour: Optional[str] = None,
) -> list[dict]:
    """
    Calculate current stock levels by aggregating in_stock items.
    Groups by product_code + colour.
    Returns list of dicts: product_code, colour, carton_count, total_quantity
    """
    query = (
        db.query(
            StockItem.product_code,
            StockItem.colour,
            func.count(StockItem.id).label("carton_count"),
            func.sum(StockItem.quantity).label("total_quantity"),
        )
        .filter(StockItem.status == "in_stock")
        .group_by(StockItem.product_code, StockItem.colour)
    )

    if product_code:
        query = query.filter(StockItem.product_code == product_code)
    if colour:
        query = query.filter(StockItem.colour == colour)

    rows = query.all()

    return [
        {
            "product_code": row.product_code,
            "colour": row.colour,
            "carton_count": row.carton_count,
            "total_quantity": row.total_quantity or 0,
        }
        for row in rows
    ]


# ── Scan-Out ─────────────────────────────────────────────────────────

def scan_out(
    barcode_id: str,
    user_id: UUID,
    db: Session,
    order_id: Optional[UUID] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Process a stock-out scan event.

    1. Look up StockItem by barcode_id
    2. Validate: status must be 'in_stock'
    3. Update StockItem: status → 'picked', scanned_out_at, scanned_out_by, order_id
    4. Create StockMovement: movement_type='stock_out', quantity_change=-quantity
    5. Return result with item details
    """
    stock_item = (
        db.query(StockItem)
        .filter(StockItem.barcode_id == barcode_id)
        .first()
    )

    if not stock_item:
        raise ValueError(f"Barcode not recognised: {barcode_id}")

    # Validate status transition
    if stock_item.status == "pending_scan":
        raise ValueError("Item not yet scanned in")
    if stock_item.status == "picked":
        raise ValueError("Already scanned out")
    if stock_item.status in ("scrapped", "consumed"):
        raise ValueError(f"Cannot scan out — item has been {stock_item.status}")
    if stock_item.status != "in_stock":
        raise ValueError(f"Unexpected status: {stock_item.status}")

    # Transition to picked
    now = datetime.now(timezone.utc)
    stock_item.status = "picked"
    stock_item.scanned_out_at = now
    stock_item.scanned_out_by = user_id
    if order_id:
        stock_item.order_id = order_id
    if notes:
        stock_item.notes = notes

    # Create movement record
    movement = StockMovement(
        stock_item_id=stock_item.id,
        movement_type="stock_out",
        quantity_change=-stock_item.quantity,
        order_id=order_id,
        performed_by=user_id,
    )
    db.add(movement)
    db.flush()

    logger.info(
        "Scanned out: %s (%s %s, %d units)",
        barcode_id, stock_item.product_code, stock_item.colour, stock_item.quantity,
    )

    return {
        "stock_item": stock_item,
        "movement": movement,
    }


# ── Partial Repack ───────────────────────────────────────────────────

def partial_repack(
    barcode_id: str,
    units_taken: int,
    user_id: UUID,
    db: Session,
    order_id: Optional[UUID] = None,
) -> dict:
    """
    Handle partial box scenario.

    1. Look up original StockItem by barcode_id
    2. Validate: status must be 'in_stock', units_taken < quantity
    3. Mark original as 'consumed'
    4. Create StockMovement for original: movement_type='partial_repack', quantity_change=-quantity
    5. Create new StockItem for remainder with new barcode, box_type='partial', status='in_stock'
    6. Create StockMovement for new partial: movement_type='stock_in', quantity_change=+remainder
    7. Generate yellow label PDF for new partial
    8. Return: original item, new partial item, label PDF bytes
    """
    original = (
        db.query(StockItem)
        .filter(StockItem.barcode_id == barcode_id)
        .first()
    )

    if not original:
        raise ValueError(f"Barcode not recognised: {barcode_id}")

    if original.status != "in_stock":
        raise ValueError(f"Cannot repack — item status is '{original.status}'")

    if units_taken <= 0:
        raise ValueError("Units taken must be greater than zero")

    if units_taken >= original.quantity:
        raise ValueError(
            f"Units taken ({units_taken}) must be less than box quantity ({original.quantity}). "
            "Use scan-out for the whole box."
        )

    remaining = original.quantity - units_taken
    now = datetime.now(timezone.utc)

    # 1. Mark original as consumed
    original.status = "consumed"
    original.scanned_out_at = now
    original.scanned_out_by = user_id
    if order_id:
        original.order_id = order_id

    # 2. Movement for original (full quantity out)
    original_movement = StockMovement(
        stock_item_id=original.id,
        movement_type="partial_repack",
        quantity_change=-original.quantity,
        order_id=order_id,
        performed_by=user_id,
    )
    db.add(original_movement)

    # 3. Generate new barcode for partial
    new_barcode_ids = generate_barcode_ids(
        db=db,
        product_code=original.product_code,
        colour=original.colour,
        count=1,
    )
    new_barcode_id = new_barcode_ids[0]

    # 4. Create new partial stock item
    partial_item = StockItem(
        barcode_id=new_barcode_id,
        product_code=original.product_code,
        colour=original.colour,
        quantity=remaining,
        box_type="partial",
        status="in_stock",
        production_date=original.production_date,
        scanned_in_at=now,
        scanned_in_by=user_id,
        parent_stock_item_id=original.id,
    )
    db.add(partial_item)
    db.flush()  # assign ID to partial_item

    # 5. Movement for new partial (remainder in)
    partial_movement = StockMovement(
        stock_item_id=partial_item.id,
        movement_type="stock_in",
        quantity_change=remaining,
        performed_by=user_id,
    )
    db.add(partial_movement)
    db.flush()

    # 6. Generate yellow label PDF
    label_pdf = generate_single_label_pdf(
        barcode_id=new_barcode_id,
        product_code=original.product_code,
        colour=original.colour,
        quantity=remaining,
        production_date=original.production_date,
        box_type="partial",
    )

    logger.info(
        "Partial repack: %s → %s (%d taken, %d remaining)",
        barcode_id, new_barcode_id, units_taken, remaining,
    )

    return {
        "original_item": original,
        "new_partial_item": partial_item,
        "units_taken": units_taken,
        "units_remaining": remaining,
        "new_barcode_id": new_barcode_id,
        "label_pdf": label_pdf,
    }


# ── Stock Summary (with thresholds) ─────────────────────────────────

def _resolve_threshold_status(total_quantity: int, red: Optional[int], amber: Optional[int]) -> Optional[str]:
    """Determine threshold colour status for a given quantity."""
    if red is None and amber is None:
        return None
    red = red or 0
    amber = amber or 0
    if total_quantity >= amber:
        return "green"
    if total_quantity >= red:
        return "amber"
    return "red"


def get_stock_summary(
    db: Session,
    search: Optional[str] = None,
    colour: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> dict:
    """
    Aggregate in_stock items by product_code + colour.
    Join with products for description and stock_thresholds for colour status.
    Returns dict with 'summary' (totals) and 'items' (per product+colour).
    """
    # Base aggregation query
    query = (
        db.query(
            StockItem.product_code,
            StockItem.colour,
            func.count(StockItem.id).label("carton_count"),
            func.coalesce(func.sum(StockItem.quantity), 0).label("total_units"),
        )
        .filter(StockItem.status == "in_stock")
        .group_by(StockItem.product_code, StockItem.colour)
    )

    if colour:
        query = query.filter(StockItem.colour.ilike(f"%{colour}%"))

    if search:
        # Filter by product_code matching — we'll also filter by description below
        query = query.filter(StockItem.product_code.ilike(f"%{search}%"))

    rows = query.all()

    # Build a lookup of product descriptions
    product_codes = list({r.product_code for r in rows})
    products = {}
    if product_codes:
        for p in db.query(Product).filter(Product.product_code.in_(product_codes)).all():
            products[p.product_code] = p.product_description

    # If search was provided and didn't match product_code, also try description
    if search and not rows:
        matching_codes = [
            p.product_code
            for p in db.query(Product)
            .filter(Product.product_description.ilike(f"%{search}%"))
            .all()
        ]
        if matching_codes:
            query = (
                db.query(
                    StockItem.product_code,
                    StockItem.colour,
                    func.count(StockItem.id).label("carton_count"),
                    func.coalesce(func.sum(StockItem.quantity), 0).label("total_units"),
                )
                .filter(StockItem.status == "in_stock")
                .filter(StockItem.product_code.in_(matching_codes))
                .group_by(StockItem.product_code, StockItem.colour)
            )
            if colour:
                query = query.filter(StockItem.colour.ilike(f"%{colour}%"))
            rows = query.all()
            for p in db.query(Product).filter(Product.product_code.in_(matching_codes)).all():
                products[p.product_code] = p.product_description

    # Build threshold lookup
    thresholds = {}
    for t in db.query(StockThreshold).all():
        key = (t.product_code, t.colour)
        thresholds[key] = t

    # Build items with threshold status
    items = []
    low_stock_count = 0
    total_units = 0
    total_cartons = 0

    for row in rows:
        total_units += row.total_units
        total_cartons += row.carton_count

        # Look up threshold: first try exact (product+colour), then product-only (colour=None)
        threshold = thresholds.get((row.product_code, row.colour))
        if not threshold:
            threshold = thresholds.get((row.product_code, None))

        red_val = threshold.red_threshold if threshold else None
        amber_val = threshold.amber_threshold if threshold else None
        status = _resolve_threshold_status(row.total_units, red_val, amber_val)

        if status in ("red", "amber"):
            low_stock_count += 1

        items.append({
            "product_code": row.product_code,
            "product_description": products.get(row.product_code, row.product_code),
            "colour": row.colour,
            "carton_count": row.carton_count,
            "total_units": row.total_units,
            "threshold_status": status,
            "red_threshold": red_val,
            "amber_threshold": amber_val,
        })

    # Apply status_filter after threshold calculation
    if status_filter:
        items = [i for i in items if i["threshold_status"] == status_filter]

    return {
        "summary": {
            "total_skus": len(set((r.product_code, r.colour) for r in rows)),
            "total_units": total_units,
            "total_cartons": total_cartons,
            "low_stock_count": low_stock_count,
        },
        "items": items,
    }


# ── Stock Item Detail ────────────────────────────────────────────────

def get_stock_item_detail(db: Session, stock_item_id: UUID) -> Optional[dict]:
    """
    Get full details for a single stock item including its movement history
    and product description.
    """
    item = db.query(StockItem).filter(StockItem.id == stock_item_id).first()
    if not item:
        return None

    # Get movements ordered by date
    movements = (
        db.query(StockMovement)
        .filter(StockMovement.stock_item_id == stock_item_id)
        .order_by(StockMovement.created_at.desc())
        .all()
    )

    # Get product description
    product = db.query(Product).filter(Product.product_code == item.product_code).first()

    return {
        "stock_item": item,
        "movements": movements,
        "product_description": product.product_description if product else item.product_code,
    }


# ── Stock Item List ──────────────────────────────────────────────────

def get_stock_items(
    db: Session,
    product_code: Optional[str] = None,
    colour: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    List individual stock items with optional filters.
    Returns dict with 'items' and 'total'.
    """
    query = db.query(StockItem)

    if product_code:
        query = query.filter(StockItem.product_code == product_code)
    if colour:
        query = query.filter(StockItem.colour == colour)
    if status:
        query = query.filter(StockItem.status == status)
    if search:
        query = query.filter(StockItem.barcode_id.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(StockItem.created_at.desc()).offset(offset).limit(limit).all()

    return {"items": items, "total": total}


# ── Stock Adjustment ────────────────────────────────────────────────

def adjustment(
    stock_item_id: UUID,
    quantity_change: int,
    reason: str,
    user_id: UUID,
    db: Session,
) -> dict:
    """
    Manual stock adjustment (scrapped/damaged cartons).

    1. Look up StockItem by ID
    2. Validate: status must be 'in_stock'
    3. Update quantity (may go to 0)
    4. Create StockMovement with movement_type='adjustment'
    5. If quantity reaches 0, set status to 'scrapped'
    """
    stock_item = db.query(StockItem).filter(StockItem.id == stock_item_id).first()

    if not stock_item:
        raise ValueError(f"Stock item not found: {stock_item_id}")

    if stock_item.status != "in_stock":
        raise ValueError(f"Cannot adjust — item status is '{stock_item.status}'")

    new_quantity = stock_item.quantity + quantity_change
    if new_quantity < 0:
        raise ValueError(
            f"Adjustment would result in negative quantity "
            f"(current: {stock_item.quantity}, change: {quantity_change})"
        )

    stock_item.quantity = new_quantity

    if new_quantity == 0:
        stock_item.status = "scrapped"

    # Create movement record
    movement = StockMovement(
        stock_item_id=stock_item.id,
        movement_type="adjustment",
        quantity_change=quantity_change,
        reason=reason,
        performed_by=user_id,
    )
    db.add(movement)
    db.flush()

    logger.info(
        "Stock adjustment: %s (%s %s) %+d units → %d (reason: %s)",
        stock_item.barcode_id, stock_item.product_code, stock_item.colour,
        quantity_change, new_quantity, reason,
    )

    return {
        "stock_item": stock_item,
        "movement": movement,
    }
