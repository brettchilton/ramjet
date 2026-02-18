"""
Stocktake API — stocktake session management, scanning, discrepancy reports.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.core.models import User, StocktakeSession, StocktakeScan
from app.services import stocktake_service
from app.schemas.stock_schemas import (
    StocktakeSessionResponse,
    StocktakeSessionCreate,
    StocktakeScanResponse,
    StocktakeScanRequest,
)
from app.schemas.stocktake_schemas import (
    SessionProgress,
    SessionDetailResponse,
    StocktakeScanWithProgress,
    StocktakeCompleteRequest,
    DiscrepancyReport,
)

router = APIRouter(prefix="/api/stocktake", tags=["stocktake"])


# ── List Sessions ────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[StocktakeSessionResponse])
async def list_sessions(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all stocktake sessions, most recent first."""
    sessions = (
        db.query(StocktakeSession)
        .order_by(StocktakeSession.started_at.desc())
        .all()
    )
    return sessions


# ── Get Session Detail ───────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get session detail with progress."""
    session = db.query(StocktakeSession).filter(StocktakeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = stocktake_service.get_session_progress(session_id, db)

    return {
        "session": session,
        "progress": progress,
    }


# ── Start Session ────────────────────────────────────────────────────

@router.post("/sessions", response_model=StocktakeSessionResponse)
async def start_session(
    body: StocktakeSessionCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Start a new stocktake session. Admin only."""
    try:
        session = stocktake_service.start_session(
            name=body.name,
            user_id=current_user.id,
            db=db,
            notes=body.notes,
        )
        db.commit()
        db.refresh(session)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Record Scan ──────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/scan", response_model=StocktakeScanWithProgress)
async def record_scan(
    session_id: UUID,
    body: StocktakeScanRequest,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """Record a scan during a stocktake session. Warehouse + admin."""
    try:
        scan = stocktake_service.process_stocktake_scan(
            session_id=session_id,
            barcode_id=body.barcode_scanned,
            user_id=current_user.id,
            db=db,
            notes=body.notes,
        )
        progress = stocktake_service.get_session_progress(session_id, db)

        db.commit()
        db.refresh(scan)

        # Get stock item detail if found
        stock_item = scan.stock_item if scan.stock_item_id else None

        return {
            "scan": scan,
            "scan_result": scan.scan_result,
            "stock_item": stock_item,
            "session_progress": progress,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Complete Session ─────────────────────────────────────────────────

@router.post("/sessions/{session_id}/complete", response_model=StocktakeSessionResponse)
async def complete_session(
    session_id: UUID,
    body: StocktakeCompleteRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Complete a stocktake session. Admin only."""
    try:
        session = stocktake_service.complete_session(
            session_id=session_id,
            user_id=current_user.id,
            auto_adjust=body.auto_adjust,
            db=db,
        )
        db.commit()
        db.refresh(session)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Cancel Session ───────────────────────────────────────────────────

@router.post("/sessions/{session_id}/cancel", response_model=StocktakeSessionResponse)
async def cancel_session(
    session_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Cancel a stocktake session. Admin only."""
    try:
        session = stocktake_service.cancel_session(
            session_id=session_id,
            user_id=current_user.id,
            db=db,
        )
        db.commit()
        db.refresh(session)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Get Discrepancies ────────────────────────────────────────────────

@router.get("/sessions/{session_id}/discrepancies", response_model=DiscrepancyReport)
async def get_discrepancies(
    session_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get discrepancy report for a session. Admin only."""
    try:
        report = stocktake_service.get_discrepancies(session_id, db)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Get Recent Scans ────────────────────────────────────────────────

@router.get("/sessions/{session_id}/scans", response_model=list[StocktakeScanResponse])
async def get_session_scans(
    session_id: UUID,
    limit: int = 50,
    current_user: User = Depends(require_role("warehouse")),
    db: Session = Depends(get_db),
):
    """Get recent scans for a session."""
    scans = (
        db.query(StocktakeScan)
        .filter(StocktakeScan.session_id == session_id)
        .order_by(StocktakeScan.scanned_at.desc())
        .limit(limit)
        .all()
    )
    return scans
