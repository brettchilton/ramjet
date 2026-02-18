"""
Stock API — stock items, scan events, movements, thresholds, label generation.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.core.models import User, Product, StockItem, StockThreshold
from app.schemas.stock_schemas import (
    LabelGenerateRequest,
    LabelGenerateResponse,
    PartialRepackRequest,
    PartialRepackResponse,
    ScanInRequest,
    ScanOutRequest,
    ScanResponse,
    StockAdjustmentRequest,
    StockItemResponse,
    StockItemDetailResponse,
    StockItemListResponse,
    StockMovementResponse,
    StockMovementDetailResponse,
    StockSummaryItem,
    StockSummaryResponse,
    StockThresholdResponse,
    StockThresholdCreate,
    StockThresholdUpdate,
)
from app.services.barcode_service import generate_labels, generate_single_label_pdf
from app.services.stock_service import (
    scan_in, scan_out, partial_repack, adjustment,
    get_stock_levels, get_stock_summary, get_stock_item_detail, get_stock_items,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock", tags=["stock"])


# ── Scan-In ──────────────────────────────────────────────────────────

@router.post("/scan-in", response_model=ScanResponse)
async def stock_scan_in(
    payload: ScanInRequest,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """
    Process a stock-in scan event.

    Looks up the barcode, transitions the stock item from pending_scan to in_stock,
    and creates a stock_in movement record.
    """
    try:
        result = scan_in(
            barcode_id=payload.barcode_id,
            user_id=current_user.id,
            db=db,
            notes=payload.notes,
        )
        db.commit()
        db.refresh(result["stock_item"])
        db.refresh(result["movement"])

        # Fetch product description for the response
        product = db.query(Product).filter(
            Product.product_code == result["stock_item"].product_code
        ).first()
        product_desc = product.product_description if product else result["stock_item"].product_code

        item = result["stock_item"]
        message = f"Scanned in: {item.product_code} {item.colour} — {item.quantity} units"

        return ScanResponse(
            success=True,
            stock_item=StockItemResponse.model_validate(item),
            movement=StockMovementResponse.model_validate(result["movement"]),
            message=message,
            barcode_id=payload.barcode_id,
            product_description=product_desc,
        )
    except ValueError as e:
        return ScanResponse(
            success=False,
            message=str(e),
            error=str(e),
            barcode_id=payload.barcode_id,
        )


# ── Scan-Out ─────────────────────────────────────────────────────────

@router.post("/scan-out", response_model=ScanResponse)
async def stock_scan_out(
    payload: ScanOutRequest,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """
    Process a stock-out scan event.

    Transitions a stock item from in_stock to picked and creates a stock_out movement.
    """
    try:
        result = scan_out(
            barcode_id=payload.barcode_id,
            user_id=current_user.id,
            db=db,
            order_id=payload.order_id,
            notes=payload.notes,
        )
        db.commit()
        db.refresh(result["stock_item"])
        db.refresh(result["movement"])

        # Fetch product description
        product = db.query(Product).filter(
            Product.product_code == result["stock_item"].product_code
        ).first()
        product_desc = product.product_description if product else result["stock_item"].product_code

        item = result["stock_item"]
        message = f"Scanned out: {item.product_code} {item.colour} — {item.quantity} units"

        return ScanResponse(
            success=True,
            stock_item=StockItemResponse.model_validate(item),
            movement=StockMovementResponse.model_validate(result["movement"]),
            message=message,
            barcode_id=payload.barcode_id,
            product_description=product_desc,
        )
    except ValueError as e:
        return ScanResponse(
            success=False,
            message=str(e),
            error=str(e),
            barcode_id=payload.barcode_id,
        )


# ── Partial Repack ───────────────────────────────────────────────────

@router.post("/partial-repack", response_model=PartialRepackResponse)
async def stock_partial_repack(
    payload: PartialRepackRequest,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """
    Handle partial box scenario.

    Consumes the original carton, creates a new partial item with the remainder,
    and generates a yellow label for the new partial box.
    """
    try:
        result = partial_repack(
            barcode_id=payload.barcode_id,
            units_taken=payload.units_taken,
            user_id=current_user.id,
            db=db,
            order_id=payload.order_id,
        )
        db.commit()
        db.refresh(result["original_item"])
        db.refresh(result["new_partial_item"])

        new_barcode = result["new_barcode_id"]
        label_url = f"/api/stock/labels/single/{new_barcode}"

        return PartialRepackResponse(
            success=True,
            original_item=StockItemResponse.model_validate(result["original_item"]),
            new_partial_item=StockItemResponse.model_validate(result["new_partial_item"]),
            units_taken=result["units_taken"],
            units_remaining=result["units_remaining"],
            label_url=label_url,
            message=f"Partial repack: {result['units_taken']} taken, {result['units_remaining']} remaining. Print yellow label.",
        )
    except ValueError as e:
        return PartialRepackResponse(
            success=False,
            message=str(e),
            error=str(e),
        )


# ── Stock Adjustment ────────────────────────────────────────────────

@router.post("/adjustment", response_model=ScanResponse)
async def stock_adjustment(
    payload: StockAdjustmentRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Manual stock adjustment for scrapped/damaged cartons.

    Admin-only. Adjusts quantity and creates an adjustment movement record.
    If quantity reaches 0, the item is marked as scrapped.
    """
    try:
        result = adjustment(
            stock_item_id=payload.stock_item_id,
            quantity_change=payload.quantity_change,
            reason=payload.reason,
            user_id=current_user.id,
            db=db,
        )
        db.commit()
        db.refresh(result["stock_item"])
        db.refresh(result["movement"])

        product = db.query(Product).filter(
            Product.product_code == result["stock_item"].product_code
        ).first()
        product_desc = product.product_description if product else result["stock_item"].product_code

        item = result["stock_item"]
        message = f"Adjusted: {item.product_code} {item.colour} — {payload.quantity_change:+d} units (now {item.quantity})"

        return ScanResponse(
            success=True,
            stock_item=StockItemResponse.model_validate(item),
            movement=StockMovementResponse.model_validate(result["movement"]),
            message=message,
            product_description=product_desc,
        )
    except ValueError as e:
        return ScanResponse(
            success=False,
            message=str(e),
            error=str(e),
        )


# ── Single Label Download ────────────────────────────────────────────

@router.get(
    "/labels/single/{barcode_id}",
    response_class=StreamingResponse,
    dependencies=[Depends(require_role("warehouse"))],
)
async def download_single_label(
    barcode_id: str,
    db: Session = Depends(get_db),
):
    """
    Download a single-label PDF for a specific barcode ID.
    Used after partial repack to print a yellow label for the new partial box.
    """
    stock_item = (
        db.query(StockItem)
        .filter(StockItem.barcode_id == barcode_id)
        .first()
    )
    if not stock_item:
        raise HTTPException(status_code=404, detail=f"Stock item not found: {barcode_id}")

    pdf_bytes = generate_single_label_pdf(
        barcode_id=stock_item.barcode_id,
        product_code=stock_item.product_code,
        colour=stock_item.colour,
        quantity=stock_item.quantity,
        production_date=stock_item.production_date,
        box_type=stock_item.box_type,
    )

    filename = f"label-{barcode_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Stock Summary (Dashboard) ────────────────────────────────────────

@router.get("/summary", response_model=StockSummaryResponse)
async def stock_summary(
    search: Optional[str] = Query(None, description="Search by product code or description"),
    colour: Optional[str] = Query(None, description="Filter by colour"),
    status_filter: Optional[str] = Query(None, description="Filter by threshold status: red, amber, green"),
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """Get aggregated stock levels with threshold status for the dashboard."""
    result = get_stock_summary(db, search=search, colour=colour, status_filter=status_filter)
    return result


# ── Stock Item List ──────────────────────────────────────────────────

@router.get("/items", response_model=StockItemListResponse)
async def list_stock_items(
    product_code: Optional[str] = Query(None),
    colour: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by barcode ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """List individual stock items with optional filters."""
    result = get_stock_items(
        db, product_code=product_code, colour=colour,
        status=status, search=search, limit=limit, offset=offset,
    )
    return StockItemListResponse(
        items=[StockItemResponse.model_validate(i) for i in result["items"]],
        total=result["total"],
    )


# ── Stock Item Detail ────────────────────────────────────────────────

@router.get("/items/{stock_item_id}", response_model=StockItemDetailResponse)
async def get_stock_item(
    stock_item_id: UUID,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """Get full details for a single stock item including movement history."""
    result = get_stock_item_detail(db, stock_item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Stock item not found")

    item = result["stock_item"]
    return StockItemDetailResponse(
        id=item.id,
        barcode_id=item.barcode_id,
        product_code=item.product_code,
        product_description=result["product_description"],
        colour=item.colour,
        quantity=item.quantity,
        box_type=item.box_type,
        status=item.status,
        production_date=item.production_date,
        scanned_in_at=item.scanned_in_at,
        scanned_in_by=item.scanned_in_by,
        scanned_out_at=item.scanned_out_at,
        scanned_out_by=item.scanned_out_by,
        order_id=item.order_id,
        parent_stock_item_id=item.parent_stock_item_id,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
        movements=[StockMovementDetailResponse.model_validate(m) for m in result["movements"]],
    )


# ── Threshold CRUD ───────────────────────────────────────────────────

@router.get("/thresholds", response_model=list[StockThresholdResponse])
async def list_thresholds(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all stock thresholds."""
    thresholds = db.query(StockThreshold).order_by(StockThreshold.product_code).all()
    return [StockThresholdResponse.model_validate(t) for t in thresholds]


@router.post("/thresholds", response_model=StockThresholdResponse, status_code=201)
async def create_threshold(
    payload: StockThresholdCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new stock threshold."""
    # Check for existing threshold with same product+colour
    existing = db.query(StockThreshold).filter(
        StockThreshold.product_code == payload.product_code,
        StockThreshold.colour == payload.colour,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Threshold already exists for {payload.product_code}/{payload.colour or 'all colours'}",
        )

    threshold = StockThreshold(
        product_code=payload.product_code,
        colour=payload.colour,
        red_threshold=payload.red_threshold,
        amber_threshold=payload.amber_threshold,
    )
    db.add(threshold)
    db.commit()
    db.refresh(threshold)
    return StockThresholdResponse.model_validate(threshold)


@router.put("/thresholds/{threshold_id}", response_model=StockThresholdResponse)
async def update_threshold(
    threshold_id: UUID,
    payload: StockThresholdUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update a stock threshold."""
    threshold = db.query(StockThreshold).filter(StockThreshold.id == threshold_id).first()
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    if payload.red_threshold is not None:
        threshold.red_threshold = payload.red_threshold
    if payload.amber_threshold is not None:
        threshold.amber_threshold = payload.amber_threshold

    db.commit()
    db.refresh(threshold)
    return StockThresholdResponse.model_validate(threshold)


@router.delete("/thresholds/{threshold_id}", status_code=204)
async def delete_threshold(
    threshold_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Delete a stock threshold."""
    threshold = db.query(StockThreshold).filter(StockThreshold.id == threshold_id).first()
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    db.delete(threshold)
    db.commit()


# ── Label Generation ─────────────────────────────────────────────────

@router.post(
    "/labels/generate",
    response_class=StreamingResponse,
    dependencies=[Depends(require_role("warehouse"))],
)
def generate_stock_labels(
    payload: LabelGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate QR code labels for stock cartons.

    Creates StockItem records (status: pending_scan) and returns a PDF
    with printable QR code labels.
    """
    try:
        pdf_bytes, barcode_ids = generate_labels(
            db=db,
            product_code=payload.product_code,
            colour=payload.colour,
            quantity_per_carton=payload.quantity_per_carton,
            number_of_labels=payload.number_of_labels,
            box_type=payload.box_type,
            production_date=payload.production_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"labels-{payload.product_code}-{payload.colour}-{payload.number_of_labels}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Label-Count": str(len(barcode_ids)),
            "X-First-Barcode": barcode_ids[0] if barcode_ids else "",
            "X-Last-Barcode": barcode_ids[-1] if barcode_ids else "",
        },
    )
