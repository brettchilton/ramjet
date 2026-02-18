"""
Stocktake-specific schemas — session lifecycle, scan responses with progress, discrepancy reports.
Re-exports base schemas from stock_schemas for convenience.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# ── Re-exports from stock_schemas (already defined there) ─────────────
from app.schemas.stock_schemas import (
    StocktakeSessionResponse,
    StocktakeSessionCreate,
    StocktakeScanResponse,
    StocktakeScanRequest,
    StockItemResponse,
)


# ── Session Progress ─────────────────────────────────────────────────

class SessionProgress(BaseModel):
    total_expected: int = 0
    total_scanned: int = 0
    percentage: float = 0.0


class SessionDetailResponse(BaseModel):
    """Session detail with progress info."""
    session: StocktakeSessionResponse
    progress: SessionProgress


# ── Scan with Progress ───────────────────────────────────────────────

class StocktakeScanWithProgress(BaseModel):
    """Scan result returned after recording a stocktake scan."""
    scan: StocktakeScanResponse
    scan_result: str
    stock_item: Optional[StockItemResponse] = None
    session_progress: SessionProgress


# ── Complete Session ─────────────────────────────────────────────────

class StocktakeCompleteRequest(BaseModel):
    auto_adjust: bool = False


# ── Discrepancy Report ───────────────────────────────────────────────

class MissingItem(BaseModel):
    stock_item_id: str
    barcode_id: str
    product_code: str
    colour: str
    quantity: int
    last_movement: Optional[str] = None
    last_movement_date: Optional[datetime] = None


class UnexpectedScan(BaseModel):
    barcode_scanned: str
    scan_result: str
    scanned_at: Optional[datetime] = None


class DiscrepancySummary(BaseModel):
    total_expected: int = 0
    total_found: int = 0
    total_missing: int = 0
    total_unexpected: int = 0


class DiscrepancyReport(BaseModel):
    missing_items: list[MissingItem] = []
    unexpected_scans: list[UnexpectedScan] = []
    summary: DiscrepancySummary
