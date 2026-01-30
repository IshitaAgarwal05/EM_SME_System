"""Aging API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, get_db
from app.services.aging_service import AgingService

router = APIRouter(prefix="/aging", tags=["Aging & Payables"])


@router.get("/receivables")
async def get_receivables_aging(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    as_of: date | None = Query(default=None),
):
    """Receivables aging grouped by client, bucketed 0-30 / 31-60 / 61-90 / 90+."""
    svc = AgingService(db, current_user.organization_id)
    return await svc.get_receivables_aging(as_of)


@router.get("/payables")
async def get_payables_aging(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    as_of: date | None = Query(default=None),
):
    """Payables aging from existing payments table, bucketed."""
    svc = AgingService(db, current_user.organization_id)
    return await svc.get_payables_aging(as_of)


@router.get("/overdue")
async def get_overdue_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """All overdue (unpaid after due_date) invoices."""
    svc = AgingService(db, current_user.organization_id)
    return await svc.get_overdue_invoices()
