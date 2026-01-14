"""
Analytics API endpoints.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_financial_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int | None = Query(None, description="Year for filtering. If None, returns all-time data."),
    include_unreconciled: bool = Query(True),
):
    """Get financial summary. If year is None, returns all-time data."""
    service = AnalyticsService(db, current_user.organization_id)
    
    if year is None:
        # All-time query
        start_date = date(2000, 1, 1)
        end_date = date(2100, 12, 31)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    
    return await service.get_financial_summary(start_date, end_date, include_unreconciled)


@router.get("/trends/monthly")
async def get_monthly_trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int | None = Query(None),
):
    """
    Get monthly income vs expense trends for a specific year.
    Defaults to current year.
    """
    if not year:
        year = date.today().year
        
    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_monthly_trends(year)


@router.get("/breakdown/category")
async def get_category_breakdown(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    year: int | None = Query(None),
):
    """Get expense breakdown by category."""
    if year:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    elif not start_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
    
    if not end_date:
        end_date = date.today()

    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_details_by_category(start_date, end_date)


@router.get("/breakdown/contractors")
async def get_contractor_spend(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    year: int | None = Query(None),
):
    """Get spending breakdown by contractor."""
    if year:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    elif not start_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
    
    if not end_date:
        end_date = date.today()

    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_contractor_spend(start_date, end_date)


@router.get("/forecast")
async def get_cashflow_forecast(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    months: int = Query(3, ge=1, le=12),
    year: int | None = Query(None),
):
    """Get cashflow projections for next few months."""
    ref_date = None
    if year:
        # If year is in the past, or specific year chosen, set ref to end of that year
        # Otherwise if current year, use today
        if year < date.today().year:
            ref_date = date(year, 12, 31)
        else:
            ref_date = date.today()

    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_cashflow_forecast(months, ref_date=ref_date)


@router.get("/anomalies")
async def get_spending_anomalies(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int | None = Query(None),
):
    """Detect anomalous spending patterns."""
    ref_date = None
    if year:
        if year < date.today().year:
            ref_date = date(year, 12, 31)
        else:
            ref_date = date.today()

    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_spending_anomalies(ref_date=ref_date)


@router.get("/insights")
async def get_savings_insights(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    year: int | None = Query(None),
):
    """Get AI-powered savings recommendations."""
    ref_date = None
    if year:
        if year < date.today().year:
            ref_date = date(year, 12, 31)
        else:
            ref_date = date.today()

    service = AnalyticsService(db, current_user.organization_id)
    return await service.get_savings_insights(ref_date=ref_date)
