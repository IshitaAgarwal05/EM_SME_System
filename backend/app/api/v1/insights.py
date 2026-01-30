"""Insights API — deterministic business analytics endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, get_db
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/profitability")
async def get_profitability_trend(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    months: int = Query(default=12, ge=1, le=36),
):
    """Net profitability trend by month (journal-based)."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.net_profitability_trend(months=months)


@router.get("/client-profitability")
async def get_client_profitability(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Revenue per client from invoices with share %."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.client_profitability()


@router.get("/revenue-concentration")
async def get_revenue_concentration(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Revenue concentration risk (high/medium/low) based on top-client share."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.revenue_concentration()


@router.get("/aging-risk")
async def get_aging_risk(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Weighted aging risk index with high-risk receivables amount."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.aging_risk_index()


@router.get("/expense-trends")
async def get_expense_trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Month-over-month expense spike detection by category."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.expense_spike_detection()


@router.get("/inventory-turnover")
async def get_inventory_turnover(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Inventory turnover ratio (COGS / avg inventory value, last 12 months)."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.inventory_turnover()


@router.get("/summary")
async def get_insights_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Combined dashboard summary: profitability, risk, spikes, turnover."""
    svc = InsightsService(db, current_user.organization_id)
    return await svc.get_dashboard_summary()
