from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User
from app.schemas.analytics_schemas import DashboardResponse
from app.services.analytics_service import resolve_period, get_dashboard_data

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    period: str = Query("mtd", description="ytd | mtd | wtd | custom"),
    start_date: Optional[date] = Query(None, description="Custom period start (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Custom period end (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    period_start, period_end = resolve_period(period, start_date, end_date)
    return get_dashboard_data(db, period_start, period_end, period)
