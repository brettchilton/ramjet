from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ── KPI Metrics ──────────────────────────────────────────────────────

class KPIMetrics(BaseModel):
    total_revenue: Decimal
    total_orders: int
    approved_orders: int
    avg_order_value: Decimal
    total_units: int
    avg_processing_hours: Optional[float] = None
    avg_confidence: Optional[float] = None
    review_rate: float  # percentage of line items needing review


# ── Chart Data Points ────────────────────────────────────────────────

class RevenueTrendPoint(BaseModel):
    date: str  # ISO date string
    revenue: Decimal
    order_count: int


class StatusBreakdown(BaseModel):
    status: str
    count: int
    percentage: float


class CustomerMetric(BaseModel):
    customer_name: str
    revenue: Decimal
    order_count: int
    unit_count: int


class ProductMetric(BaseModel):
    product_code: str
    description: Optional[str] = None
    revenue: Decimal
    quantity: int


class ConfidenceBucket(BaseModel):
    bucket: str  # e.g. "90-100%"
    count: int


class RecentOrder(BaseModel):
    id: str
    customer_name: Optional[str] = None
    po_number: Optional[str] = None
    status: str
    total: Decimal
    created_at: Optional[datetime] = None


# ── Dashboard Response ───────────────────────────────────────────────

class DashboardResponse(BaseModel):
    period: str
    period_start: str
    period_end: str
    kpi: KPIMetrics
    revenue_trend: list[RevenueTrendPoint]
    status_breakdown: list[StatusBreakdown]
    top_customers: list[CustomerMetric]
    top_products: list[ProductMetric]
    confidence_distribution: list[ConfidenceBucket]
    recent_orders: list[RecentOrder]
