"""Audit export API endpoints."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, get_db
from app.services.accounting_service import AccountingService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/trial-balance/export")
async def export_trial_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    as_of: date | None = Query(default=None),
):
    """Download trial balance as CSV."""
    svc = AuditService(db, current_user.organization_id)
    csv_bytes = await svc.export_trial_balance_csv(as_of=as_of)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trial_balance.csv"},
    )


@router.get("/journal-register/export")
async def export_journal_register(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    """Download journal register as CSV."""
    svc = AuditService(db, current_user.organization_id)
    csv_bytes = await svc.export_journal_register_csv(from_date=from_date, to_date=to_date)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=journal_register.csv"},
    )


@router.get("/general-ledger/export")
async def export_general_ledger(
    account_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    """Download general ledger for a specific account as CSV."""
    svc = AuditService(db, current_user.organization_id)
    try:
        csv_bytes = await svc.export_general_ledger_csv(account_id, from_date, to_date)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ledger_{account_id}.csv"},
    )


class LockYearRequest(BaseModel):
    year: int


@router.post("/lock-year")
async def lock_financial_year(
    body: LockYearRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Lock a financial year for the organisation."""
    svc = AccountingService(db, current_user.organization_id)
    try:
        fy = await svc.lock_financial_year(body.year, locked_by=current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"year": fy.year, "is_locked": fy.is_locked}
