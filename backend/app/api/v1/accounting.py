"""
Accounting API endpoints:
  - Chart of Accounts (CRUD)
  - Journal Entries (list, create, void)
  - Trial Balance
  - General Ledger
  - Financial Year Lock
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, get_db
from app.services.accounting_service import AccountingService, LineSpec
from app.services.coa_service import CoAService

router = APIRouter(prefix="/accounting", tags=["Accounting"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class AccountCreateRequest(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    account_type: str = Field(..., description="asset | liability | equity | income | expense")
    sub_type: str | None = None
    parent_id: uuid.UUID | None = None
    description: str | None = None


class JournalLineRequest(BaseModel):
    account_id: uuid.UUID
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    description: str | None = None


class JournalEntryRequest(BaseModel):
    entry_date: date
    description: str
    reference: str | None = None
    lines: list[JournalLineRequest] = Field(..., min_length=2)


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_accounting(db: AsyncSession, current_user: Any) -> AccountingService:
    return AccountingService(db, current_user.organization_id)


def _get_coa(db: AsyncSession, current_user: Any) -> CoAService:
    return CoAService(db, current_user.organization_id)


# ── Chart of Accounts ────────────────────────────────────────────────────────

@router.get("/coa")
async def get_coa(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Get full hierarchical Chart of Accounts for the organisation."""
    svc = CoAService(db, current_user.organization_id)
    return await svc.get_account_tree()


@router.post("/coa", status_code=201)
async def create_account(
    body: AccountCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Create a new custom account."""
    svc = CoAService(db, current_user.organization_id)
    try:
        acct = await svc.create_account(
            code=body.code,
            name=body.name,
            account_type=body.account_type,
            sub_type=body.sub_type,
            parent_id=body.parent_id,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": str(acct.id), "code": acct.code, "name": acct.name}


@router.delete("/coa/{account_id}", status_code=204)
async def deactivate_account(
    account_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Soft-deactivate a custom account."""
    svc = CoAService(db, current_user.organization_id)
    try:
        await svc.deactivate_account(account_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/coa/seed", status_code=201)
async def seed_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Seed default Chart of Accounts for this organisation (idempotent)."""
    svc = CoAService(db, current_user.organization_id)
    await svc.seed_default_accounts()
    return {"message": "Default accounts seeded successfully"}


# ── Journal Entries ──────────────────────────────────────────────────────────

@router.get("/journal-entries")
async def list_journal_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    """List journal entries with pagination and filters."""
    svc = AccountingService(db, current_user.organization_id)
    return await svc.list_journal_entries(
        page=page,
        page_size=page_size,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )


@router.post("/journal-entries", status_code=201)
async def create_journal_entry(
    body: JournalEntryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Post a manual balanced journal entry."""
    svc = AccountingService(db, current_user.organization_id)
    try:
        lines = [
            LineSpec(
                account_id=l.account_id,
                debit=l.debit,
                credit=l.credit,
                description=l.description,
            )
            for l in body.lines
        ]
        entry = await svc.post_journal_entry(
            entry_date=body.entry_date,
            description=body.description,
            lines=lines,
            reference=body.reference,
            source="manual",
            created_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"id": str(entry.id), "status": entry.status, "date": str(entry.entry_date)}


@router.post("/journal-entries/{entry_id}/void")
async def void_journal_entry(
    entry_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Void a posted journal entry (creates a reversal entry)."""
    svc = AccountingService(db, current_user.organization_id)
    try:
        reversal = await svc.void_entry(entry_id, voided_by=current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"reversal_entry_id": str(reversal.id), "status": "voided"}


# ── Trial Balance ─────────────────────────────────────────────────────────────

@router.get("/trial-balance")
async def get_trial_balance(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    as_of: date | None = Query(default=None, description="Default: today"),
):
    """
    Generate Trial Balance as of a given date.
    Returns all accounts with their debit/credit totals and whether totals balance.
    """
    svc = AccountingService(db, current_user.organization_id)
    return await svc.get_trial_balance(as_of_date=as_of)


# ── General Ledger ────────────────────────────────────────────────────────────

@router.get("/general-ledger")
async def get_general_ledger(
    account_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
):
    """
    Get full general ledger for a specific account with running balance.
    """
    svc = AccountingService(db, current_user.organization_id)
    try:
        return await svc.get_general_ledger(account_id, from_date, to_date)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Financial Year Lock ───────────────────────────────────────────────────────

class LockYearRequest(BaseModel):
    year: int


@router.post("/lock-year")
async def lock_financial_year(
    body: LockYearRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """
    Lock a financial year. Once locked, no new journals can be posted for that year.
    """
    svc = AccountingService(db, current_user.organization_id)
    try:
        fy = await svc.lock_financial_year(body.year, locked_by=current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"year": fy.year, "is_locked": fy.is_locked, "locked_at": str(fy.locked_at)}
