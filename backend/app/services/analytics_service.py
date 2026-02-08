from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session

from app.core.models import Order, OrderLineItem


def resolve_period(
    period: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> tuple[date, date]:
    """Convert a period keyword into (start, end) date range."""
    today = date.today()

    if period == "custom" and start_date and end_date:
        return start_date, end_date

    if period == "ytd":
        return date(today.year, 1, 1), today

    if period == "wtd":
        # Monday = 0
        start = today - timedelta(days=today.weekday())
        return start, today

    # Default: mtd
    return date(today.year, today.month, 1), today


def get_dashboard_data(
    db: Session,
    period_start: date,
    period_end: date,
    period: str,
) -> dict:
    """Run all aggregation queries and return the full dashboard payload."""

    # Convert dates to datetimes for filtering
    dt_start = datetime.combine(period_start, datetime.min.time())
    dt_end = datetime.combine(period_end, datetime.max.time())

    # ── KPI Metrics ──────────────────────────────────────────────────

    # Total orders in period
    total_orders = (
        db.query(func.count(Order.id))
        .filter(Order.created_at.between(dt_start, dt_end))
        .scalar()
    ) or 0

    # Approved orders in period
    approved_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.status == "approved",
            Order.created_at.between(dt_start, dt_end),
        )
        .scalar()
    ) or 0

    # Revenue from approved orders (sum of line_total)
    total_revenue = (
        db.query(func.coalesce(func.sum(OrderLineItem.line_total), 0))
        .join(Order, OrderLineItem.order_id == Order.id)
        .filter(
            Order.status == "approved",
            Order.created_at.between(dt_start, dt_end),
        )
        .scalar()
    ) or Decimal("0")

    # Avg order value
    avg_order_value = (
        Decimal(str(total_revenue)) / Decimal(str(approved_orders))
        if approved_orders > 0
        else Decimal("0")
    )

    # Total units
    total_units = (
        db.query(func.coalesce(func.sum(OrderLineItem.quantity), 0))
        .join(Order, OrderLineItem.order_id == Order.id)
        .filter(Order.created_at.between(dt_start, dt_end))
        .scalar()
    ) or 0

    # Avg processing time (approved_at - created_at) in hours
    avg_processing = (
        db.query(
            func.avg(
                extract("epoch", Order.approved_at - Order.created_at) / 3600
            )
        )
        .filter(
            Order.status == "approved",
            Order.approved_at.isnot(None),
            Order.created_at.between(dt_start, dt_end),
        )
        .scalar()
    )
    avg_processing_hours = round(float(avg_processing), 1) if avg_processing else None

    # Avg extraction confidence
    avg_confidence = (
        db.query(func.avg(Order.extraction_confidence))
        .filter(
            Order.extraction_confidence.isnot(None),
            Order.created_at.between(dt_start, dt_end),
        )
        .scalar()
    )
    avg_confidence_val = round(float(avg_confidence), 2) if avg_confidence else None

    # Review rate (% of line items needing review)
    total_line_items = (
        db.query(func.count(OrderLineItem.id))
        .join(Order, OrderLineItem.order_id == Order.id)
        .filter(Order.created_at.between(dt_start, dt_end))
        .scalar()
    ) or 0

    review_items = (
        db.query(func.count(OrderLineItem.id))
        .join(Order, OrderLineItem.order_id == Order.id)
        .filter(
            OrderLineItem.needs_review == True,
            Order.created_at.between(dt_start, dt_end),
        )
        .scalar()
    ) or 0

    review_rate = round((review_items / total_line_items * 100), 1) if total_line_items > 0 else 0.0

    kpi = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "approved_orders": approved_orders,
        "avg_order_value": avg_order_value,
        "total_units": total_units,
        "avg_processing_hours": avg_processing_hours,
        "avg_confidence": avg_confidence_val,
        "review_rate": review_rate,
    }

    # ── Revenue Trend ────────────────────────────────────────────────

    # Use day granularity for MTD/WTD, month for YTD
    if period == "ytd":
        trunc_unit = "month"
    else:
        trunc_unit = "day"

    trend_rows = (
        db.query(
            func.date_trunc(trunc_unit, Order.created_at).label("period_date"),
            func.coalesce(func.sum(OrderLineItem.line_total), 0).label("revenue"),
            func.count(func.distinct(Order.id)).label("order_count"),
        )
        .join(OrderLineItem, OrderLineItem.order_id == Order.id)
        .filter(
            Order.status == "approved",
            Order.created_at.between(dt_start, dt_end),
        )
        .group_by("period_date")
        .order_by("period_date")
        .all()
    )

    revenue_trend = [
        {
            "date": row.period_date.strftime("%Y-%m-%d") if row.period_date else "",
            "revenue": row.revenue or Decimal("0"),
            "order_count": row.order_count or 0,
        }
        for row in trend_rows
    ]

    # ── Status Breakdown ─────────────────────────────────────────────

    status_rows = (
        db.query(Order.status, func.count(Order.id).label("cnt"))
        .filter(Order.created_at.between(dt_start, dt_end))
        .group_by(Order.status)
        .all()
    )

    status_breakdown = []
    for row in status_rows:
        pct = round((row.cnt / total_orders * 100), 1) if total_orders > 0 else 0.0
        status_breakdown.append({
            "status": row.status,
            "count": row.cnt,
            "percentage": pct,
        })

    # ── Top 10 Customers ─────────────────────────────────────────────

    customer_rows = (
        db.query(
            Order.customer_name,
            func.coalesce(func.sum(OrderLineItem.line_total), 0).label("revenue"),
            func.count(func.distinct(Order.id)).label("order_count"),
            func.coalesce(func.sum(OrderLineItem.quantity), 0).label("unit_count"),
        )
        .join(OrderLineItem, OrderLineItem.order_id == Order.id)
        .filter(
            Order.customer_name.isnot(None),
            Order.created_at.between(dt_start, dt_end),
        )
        .group_by(Order.customer_name)
        .order_by(func.sum(OrderLineItem.line_total).desc())
        .limit(10)
        .all()
    )

    top_customers = [
        {
            "customer_name": row.customer_name or "Unknown",
            "revenue": row.revenue or Decimal("0"),
            "order_count": row.order_count or 0,
            "unit_count": row.unit_count or 0,
        }
        for row in customer_rows
    ]

    # ── Top 10 Products ──────────────────────────────────────────────

    product_rows = (
        db.query(
            OrderLineItem.product_code,
            OrderLineItem.product_description,
            func.coalesce(func.sum(OrderLineItem.line_total), 0).label("revenue"),
            func.coalesce(func.sum(OrderLineItem.quantity), 0).label("quantity"),
        )
        .join(Order, OrderLineItem.order_id == Order.id)
        .filter(
            OrderLineItem.product_code.isnot(None),
            Order.created_at.between(dt_start, dt_end),
        )
        .group_by(OrderLineItem.product_code, OrderLineItem.product_description)
        .order_by(func.sum(OrderLineItem.line_total).desc())
        .limit(10)
        .all()
    )

    top_products = [
        {
            "product_code": row.product_code or "Unknown",
            "description": row.product_description,
            "revenue": row.revenue or Decimal("0"),
            "quantity": row.quantity or 0,
        }
        for row in product_rows
    ]

    # ── Confidence Distribution ──────────────────────────────────────

    confidence_case = case(
        (Order.extraction_confidence >= Decimal("0.90"), "90-100%"),
        (Order.extraction_confidence >= Decimal("0.80"), "80-90%"),
        (Order.extraction_confidence >= Decimal("0.70"), "70-80%"),
        (Order.extraction_confidence >= Decimal("0.60"), "60-70%"),
        else_="< 60%",
    )

    confidence_rows = (
        db.query(
            confidence_case.label("bucket"),
            func.count(Order.id).label("cnt"),
        )
        .filter(
            Order.extraction_confidence.isnot(None),
            Order.created_at.between(dt_start, dt_end),
        )
        .group_by("bucket")
        .order_by(confidence_case.desc())
        .all()
    )

    # Ensure all buckets exist in a consistent order
    bucket_order = ["90-100%", "80-90%", "70-80%", "60-70%", "< 60%"]
    bucket_map = {row.bucket: row.cnt for row in confidence_rows}
    confidence_distribution = [
        {"bucket": b, "count": bucket_map.get(b, 0)}
        for b in bucket_order
    ]

    # ── Recent 10 Orders ─────────────────────────────────────────────

    recent_rows = (
        db.query(
            Order.id,
            Order.customer_name,
            Order.po_number,
            Order.status,
            func.coalesce(func.sum(OrderLineItem.line_total), 0).label("total"),
            Order.created_at,
        )
        .outerjoin(OrderLineItem, OrderLineItem.order_id == Order.id)
        .filter(Order.created_at.between(dt_start, dt_end))
        .group_by(Order.id, Order.customer_name, Order.po_number, Order.status, Order.created_at)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    recent_orders = [
        {
            "id": str(row.id),
            "customer_name": row.customer_name,
            "po_number": row.po_number,
            "status": row.status,
            "total": row.total or Decimal("0"),
            "created_at": row.created_at,
        }
        for row in recent_rows
    ]

    # ── Assemble Response ────────────────────────────────────────────

    return {
        "period": period,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "kpi": kpi,
        "revenue_trend": revenue_trend,
        "status_breakdown": status_breakdown,
        "top_customers": top_customers,
        "top_products": top_products,
        "confidence_distribution": confidence_distribution,
        "recent_orders": recent_orders,
    }
