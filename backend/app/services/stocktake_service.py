"""
Stocktake service — session management, scan processing, discrepancy calculation.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.models import StocktakeSession, StocktakeScan, StockItem, StockMovement

logger = logging.getLogger(__name__)


# ── Start Session ────────────────────────────────────────────────────

def start_session(
    name: str,
    user_id: UUID,
    db: Session,
    notes: Optional[str] = None,
) -> StocktakeSession:
    """
    Start a new stocktake session.
    1. Create StocktakeSession with status 'in_progress'
    2. Snapshot all in_stock items: total_expected = count of in_stock StockItems
    3. Return session
    """
    # Count expected in_stock items
    total_expected = (
        db.query(func.count(StockItem.id))
        .filter(StockItem.status == "in_stock")
        .scalar()
    ) or 0

    session = StocktakeSession(
        name=name,
        status="in_progress",
        started_by=user_id,
        total_expected=total_expected,
        total_scanned=0,
        total_discrepancies=0,
        notes=notes,
    )
    db.add(session)
    db.flush()

    logger.info(
        "Stocktake session started: %s (expected %d items)",
        name, total_expected,
    )

    return session


# ── Process Scan ─────────────────────────────────────────────────────

def process_stocktake_scan(
    session_id: UUID,
    barcode_id: str,
    user_id: UUID,
    db: Session,
    notes: Optional[str] = None,
) -> StocktakeScan:
    """
    Record a scan during a stocktake session.

    Classification:
    - 'found': barcode exists, status is in_stock, not already scanned in this session
    - 'not_in_system': barcode not found in stock_items
    - 'already_scanned': barcode already recorded in this session
    - 'wrong_status': barcode exists but status is not in_stock
    """
    # Validate session
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise ValueError("Stocktake session not found")
    if session.status != "in_progress":
        raise ValueError(f"Session is not in progress (status: {session.status})")

    # Look up the stock item
    stock_item = (
        db.query(StockItem)
        .filter(StockItem.barcode_id == barcode_id)
        .first()
    )

    # Check if already scanned in this session
    already_scanned = (
        db.query(StocktakeScan)
        .filter(
            StocktakeScan.session_id == session_id,
            StocktakeScan.barcode_scanned == barcode_id,
        )
        .first()
    )

    # Classify the scan
    if already_scanned:
        scan_result = "already_scanned"
        stock_item_id = stock_item.id if stock_item else None
    elif not stock_item:
        scan_result = "not_in_system"
        stock_item_id = None
    elif stock_item.status != "in_stock":
        scan_result = "wrong_status"
        stock_item_id = stock_item.id
    else:
        scan_result = "found"
        stock_item_id = stock_item.id

    # Create scan record
    scan = StocktakeScan(
        session_id=session_id,
        barcode_scanned=barcode_id,
        stock_item_id=stock_item_id,
        scan_result=scan_result,
        scanned_by=user_id,
        notes=notes,
    )
    db.add(scan)

    # Increment total_scanned only for 'found' scans (unique valid items)
    if scan_result == "found":
        session.total_scanned = (session.total_scanned or 0) + 1

    db.flush()

    logger.info(
        "Stocktake scan: %s → %s (session %s)",
        barcode_id, scan_result, session_id,
    )

    return scan


# ── Get Session Progress ─────────────────────────────────────────────

def get_session_progress(session_id: UUID, db: Session) -> dict:
    """
    Return progress for a stocktake session.
    """
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise ValueError("Stocktake session not found")

    total_expected = session.total_expected or 0
    total_scanned = session.total_scanned or 0
    percentage = (total_scanned / total_expected * 100) if total_expected > 0 else 0.0

    return {
        "total_expected": total_expected,
        "total_scanned": total_scanned,
        "percentage": round(percentage, 1),
    }


# ── Complete Session ─────────────────────────────────────────────────

def complete_session(
    session_id: UUID,
    user_id: UUID,
    auto_adjust: bool,
    db: Session,
) -> StocktakeSession:
    """
    Complete a stocktake session:
    1. Calculate discrepancies (missing + unexpected)
    2. If auto_adjust: mark missing items as 'scrapped' with adjustment movements
    3. Set session status to 'completed'
    """
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise ValueError("Stocktake session not found")
    if session.status != "in_progress":
        raise ValueError(f"Session is not in progress (status: {session.status})")

    # Get all 'found' scan barcodes for this session
    found_barcodes = set(
        row[0] for row in
        db.query(StocktakeScan.barcode_scanned)
        .filter(
            StocktakeScan.session_id == session_id,
            StocktakeScan.scan_result == "found",
        )
        .all()
    )

    # Get all in_stock items (expected)
    in_stock_items = (
        db.query(StockItem)
        .filter(StockItem.status == "in_stock")
        .all()
    )

    # Missing = in_stock items not scanned
    missing_items = [
        item for item in in_stock_items
        if item.barcode_id not in found_barcodes
    ]

    # Unexpected = scans that are not_in_system or wrong_status
    unexpected_count = (
        db.query(func.count(StocktakeScan.id))
        .filter(
            StocktakeScan.session_id == session_id,
            StocktakeScan.scan_result.in_(["not_in_system", "wrong_status"]),
        )
        .scalar()
    ) or 0

    total_discrepancies = len(missing_items) + unexpected_count

    # Auto-adjust: mark missing items as scrapped
    if auto_adjust and missing_items:
        now = datetime.now(timezone.utc)
        for item in missing_items:
            item.status = "scrapped"
            item.notes = (item.notes or "") + f" [Stocktake adjustment: {session.name}]"

            # Create adjustment movement
            movement = StockMovement(
                stock_item_id=item.id,
                movement_type="adjustment",
                quantity_change=-item.quantity,
                reason=f"Stocktake discrepancy — item not found during {session.name}",
                stocktake_session_id=session_id,
                performed_by=user_id,
            )
            db.add(movement)

        logger.info(
            "Auto-adjusted %d missing items for session %s",
            len(missing_items), session.name,
        )

    # Update session
    session.status = "completed"
    session.completed_by = user_id
    session.completed_at = datetime.now(timezone.utc)
    session.total_discrepancies = total_discrepancies

    db.flush()

    logger.info(
        "Stocktake session completed: %s (%d discrepancies, auto_adjust=%s)",
        session.name, total_discrepancies, auto_adjust,
    )

    return session


# ── Cancel Session ───────────────────────────────────────────────────

def cancel_session(
    session_id: UUID,
    user_id: UUID,
    db: Session,
) -> StocktakeSession:
    """Cancel a stocktake session."""
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise ValueError("Stocktake session not found")
    if session.status != "in_progress":
        raise ValueError(f"Session is not in progress (status: {session.status})")

    session.status = "cancelled"
    session.completed_by = user_id
    session.completed_at = datetime.now(timezone.utc)
    db.flush()

    logger.info("Stocktake session cancelled: %s", session.name)

    return session


# ── Get Discrepancies ────────────────────────────────────────────────

def get_discrepancies(session_id: UUID, db: Session) -> dict:
    """
    Get the discrepancy report for a completed session.
    Returns missing items and unexpected scans.
    """
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise ValueError("Stocktake session not found")

    # Get all 'found' scan barcodes
    found_barcodes = set(
        row[0] for row in
        db.query(StocktakeScan.barcode_scanned)
        .filter(
            StocktakeScan.session_id == session_id,
            StocktakeScan.scan_result == "found",
        )
        .all()
    )

    # Missing items: items that were in_stock at session start but not scanned
    # For completed sessions where auto_adjust was applied, these items are now 'scrapped'
    # We need to check the original expected set
    # Use the movements to find items that were adjusted by this session
    adjusted_item_ids = set(
        row[0] for row in
        db.query(StockMovement.stock_item_id)
        .filter(StockMovement.stocktake_session_id == session_id)
        .all()
    )

    # For active sessions, missing = in_stock items not scanned
    # For completed sessions, also include items adjusted by this stocktake
    if session.status == "completed":
        # Items adjusted by this stocktake (they were missing)
        adjusted_items = (
            db.query(StockItem)
            .filter(StockItem.id.in_(adjusted_item_ids))
            .all()
        ) if adjusted_item_ids else []

        # Plus any still-in_stock items not scanned (if auto_adjust was not used)
        still_in_stock_missing = (
            db.query(StockItem)
            .filter(
                StockItem.status == "in_stock",
                ~StockItem.barcode_id.in_(found_barcodes) if found_barcodes else True,
            )
            .all()
        )

        # Combine, deduplicate
        missing_item_ids = set()
        missing_items = []
        for item in adjusted_items + still_in_stock_missing:
            if item.id not in missing_item_ids and item.barcode_id not in found_barcodes:
                missing_item_ids.add(item.id)
                # Get last movement for context
                last_movement = (
                    db.query(StockMovement)
                    .filter(
                        StockMovement.stock_item_id == item.id,
                        StockMovement.stocktake_session_id != session_id,
                    )
                    .order_by(StockMovement.created_at.desc())
                    .first()
                )
                missing_items.append({
                    "stock_item_id": str(item.id),
                    "barcode_id": item.barcode_id,
                    "product_code": item.product_code,
                    "colour": item.colour,
                    "quantity": item.quantity,
                    "last_movement": last_movement.movement_type if last_movement else None,
                    "last_movement_date": last_movement.created_at if last_movement else None,
                })
    else:
        # In-progress session: missing = in_stock not yet scanned
        in_stock_items = (
            db.query(StockItem)
            .filter(StockItem.status == "in_stock")
            .all()
        )
        missing_items = []
        for item in in_stock_items:
            if item.barcode_id not in found_barcodes:
                last_movement = (
                    db.query(StockMovement)
                    .filter(StockMovement.stock_item_id == item.id)
                    .order_by(StockMovement.created_at.desc())
                    .first()
                )
                missing_items.append({
                    "stock_item_id": str(item.id),
                    "barcode_id": item.barcode_id,
                    "product_code": item.product_code,
                    "colour": item.colour,
                    "quantity": item.quantity,
                    "last_movement": last_movement.movement_type if last_movement else None,
                    "last_movement_date": last_movement.created_at if last_movement else None,
                })

    # Unexpected scans
    unexpected_scans_rows = (
        db.query(StocktakeScan)
        .filter(
            StocktakeScan.session_id == session_id,
            StocktakeScan.scan_result.in_(["not_in_system", "wrong_status"]),
        )
        .order_by(StocktakeScan.scanned_at.desc())
        .all()
    )

    unexpected_scans = [
        {
            "barcode_scanned": scan.barcode_scanned,
            "scan_result": scan.scan_result,
            "scanned_at": scan.scanned_at,
        }
        for scan in unexpected_scans_rows
    ]

    total_found = len(found_barcodes)

    return {
        "missing_items": missing_items,
        "unexpected_scans": unexpected_scans,
        "summary": {
            "total_expected": session.total_expected or 0,
            "total_found": total_found,
            "total_missing": len(missing_items),
            "total_unexpected": len(unexpected_scans),
        },
    }
