"""
Double-Entry Accounting Service.

Core responsibilities:
  - Post balanced journal entries (enforces debit == credit)
  - Void entries (reversal method)
  - Generate Trial Balance
  - Generate General Ledger for a specific account
  - Check financial year lock before any posting
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounting import Account, FinancialYear, JournalEntry, JournalLine

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Data structures (plain dicts to avoid heavy schema imports)
# ---------------------------------------------------------------------------
class LineSpec:
    """Spec for a single journal line (debit OR credit)."""

    def __init__(
        self,
        account_id: uuid.UUID,
        debit: Decimal = Decimal("0"),
        credit: Decimal = Decimal("0"),
        description: str | None = None,
    ):
        if (debit > 0 and credit > 0) or (debit == 0 and credit == 0):
            raise ValueError(f"Exactly one of debit/credit must be positive — got Dr={debit} Cr={credit}")
        self.account_id = account_id
        self.debit = debit
        self.credit = credit
        self.description = description


class AccountingService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    async def _assert_year_open(self, year: int) -> None:
        """Raise if the financial year is locked for this org."""
        result = await self.db.execute(
            select(FinancialYear).where(
                FinancialYear.organization_id == self.org_id,
                FinancialYear.year == year,
                FinancialYear.is_locked == True,
            )
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Financial year {year} is locked. No new postings allowed.")

    async def _validate_accounts(self, lines: list[LineSpec]) -> None:
        """Ensure all account IDs exist and belong to this organisation."""
        account_ids = {line.account_id for line in lines}
        result = await self.db.execute(
            select(Account.id).where(
                Account.id.in_(account_ids),
                Account.organization_id == self.org_id,
                Account.is_active == True,
            )
        )
        found = {row[0] for row in result.all()}
        missing = account_ids - found
        if missing:
            raise ValueError(f"Accounts not found in this organisation: {missing}")

    # -----------------------------------------------------------------------
    # Post Entry
    # -----------------------------------------------------------------------
    async def post_journal_entry(
        self,
        entry_date: date,
        description: str,
        lines: list[LineSpec],
        reference: str | None = None,
        source: str = "manual",
        source_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,
    ) -> JournalEntry:
        """
        Create and immediately post a balanced journal entry.

        Raises:
            ValueError: if debits ≠ credits or year is locked
        """
        # 1. Validate balance
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)
        if total_debit != total_credit:
            raise ValueError(
                f"Journal entry not balanced: Dr={total_debit} Cr={total_credit}"
            )
        if total_debit == 0:
            raise ValueError("Journal entry must have non-zero amounts")

        # 2. Check year lock
        fiscal_year = entry_date.year
        await self._assert_year_open(fiscal_year)

        # 3. Validate all accounts
        await self._validate_accounts(lines)

        # 4. Create entry
        entry = JournalEntry(
            organization_id=self.org_id,
            entry_date=entry_date,
            reference=reference,
            description=description,
            source=source,
            source_id=source_id,
            status="posted",
            fiscal_year=fiscal_year,
            created_by=created_by,
        )
        self.db.add(entry)
        await self.db.flush()  # get entry.id

        # 5. Create lines
        for spec in lines:
            self.db.add(
                JournalLine(
                    entry_id=entry.id,
                    account_id=spec.account_id,
                    debit=spec.debit,
                    credit=spec.credit,
                    description=spec.description,
                )
            )

        await self.db.commit()
        await self.db.refresh(entry)
        logger.info(
            "journal_entry_posted",
            entry_id=str(entry.id),
            amount=str(total_debit),
            source=source,
        )
        return entry

    # -----------------------------------------------------------------------
    # Void Entry
    # -----------------------------------------------------------------------
    async def void_entry(
        self,
        entry_id: uuid.UUID,
        voided_by: uuid.UUID | None = None,
    ) -> JournalEntry:
        """
        Void a posted entry by creating a reversal entry (debit↔credit swapped).
        The original entry is marked 'voided'.
        """
        result = await self.db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(
                JournalEntry.id == entry_id,
                JournalEntry.organization_id == self.org_id,
            )
        )
        original = result.scalar_one_or_none()
        if not original:
            raise ValueError("Journal entry not found")
        if original.status != "posted":
            raise ValueError(f"Cannot void entry with status '{original.status}'")

        # Post reversal
        reversal_lines = [
            LineSpec(
                account_id=line.account_id,
                debit=line.credit,   # swap
                credit=line.debit,
                description=f"Reversal of {line.description or entry_id}",
            )
            for line in original.lines
        ]
        reversal = await self.post_journal_entry(
            entry_date=date.today(),
            description=f"REVERSAL: {original.description}",
            lines=reversal_lines,
            reference=original.reference,
            source="void",
            source_id=original.id,
            created_by=voided_by,
        )

        # Mark original as voided
        original.status = "voided"
        original.reversed_by = reversal.id
        await self.db.commit()

        logger.info("journal_entry_voided", original_id=str(entry_id), reversal_id=str(reversal.id))
        return reversal

    # -----------------------------------------------------------------------
    # Trial Balance
    # -----------------------------------------------------------------------
    async def get_trial_balance(
        self, as_of_date: date | None = None
    ) -> dict[str, Any]:
        """
        Returns trial balance as of a given date (defaults to today).
        Only 'posted' entries are included.
        """
        as_of_date = as_of_date or date.today()

        # Sum debits and credits per account
        q = (
            select(
                Account.id,
                Account.code,
                Account.name,
                Account.account_type,
                Account.sub_type,
                func.coalesce(func.sum(JournalLine.debit), Decimal("0")).label("total_debit"),
                func.coalesce(func.sum(JournalLine.credit), Decimal("0")).label("total_credit"),
            )
            .join(JournalLine, JournalLine.account_id == Account.id, isouter=True)
            .join(
                JournalEntry,
                (JournalEntry.id == JournalLine.entry_id)
                & (JournalEntry.status == "posted")
                & (JournalEntry.entry_date <= as_of_date)
                & (JournalEntry.organization_id == self.org_id),
                isouter=True,
            )
            .where(Account.organization_id == self.org_id, Account.is_active == True)
            .group_by(Account.id, Account.code, Account.name, Account.account_type, Account.sub_type)
            .order_by(Account.code)
        )

        result = await self.db.execute(q)
        rows = result.all()

        total_dr = Decimal("0")
        total_cr = Decimal("0")
        accounts = []
        for row in rows:
            dr = row.total_debit or Decimal("0")
            cr = row.total_credit or Decimal("0")
            net = dr - cr
            total_dr += dr
            total_cr += cr
            accounts.append(
                {
                    "account_id": str(row.id),
                    "code": row.code,
                    "name": row.name,
                    "account_type": row.account_type,
                    "sub_type": row.sub_type,
                    "total_debit": float(dr),
                    "total_credit": float(cr),
                    "net_balance": float(net),
                }
            )

        return {
            "as_of_date": str(as_of_date),
            "accounts": accounts,
            "grand_total_debit": float(total_dr),
            "grand_total_credit": float(total_cr),
            "is_balanced": total_dr == total_cr,
        }

    # -----------------------------------------------------------------------
    # General Ledger
    # -----------------------------------------------------------------------
    async def get_general_ledger(
        self,
        account_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Returns all posted journal lines for a given account, with running balance.
        """
        account = await self.db.get(Account, account_id)
        if not account or account.organization_id != self.org_id:
            raise ValueError("Account not found")

        q = (
            select(
                JournalLine.debit,
                JournalLine.credit,
                JournalLine.description.label("line_desc"),
                JournalEntry.entry_date,
                JournalEntry.reference,
                JournalEntry.description.label("entry_desc"),
                JournalEntry.id.label("entry_id"),
            )
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .where(
                JournalLine.account_id == account_id,
                JournalEntry.organization_id == self.org_id,
                JournalEntry.status == "posted",
            )
            .order_by(JournalEntry.entry_date, JournalEntry.created_at)
        )

        if from_date:
            q = q.where(JournalEntry.entry_date >= from_date)
        if to_date:
            q = q.where(JournalEntry.entry_date <= to_date)

        result = await self.db.execute(q)
        rows = result.all()

        running_balance = Decimal("0")
        entries = []
        for row in rows:
            dr = row.debit or Decimal("0")
            cr = row.credit or Decimal("0")
            running_balance += dr - cr
            entries.append(
                {
                    "entry_id": str(row.entry_id),
                    "date": str(row.entry_date),
                    "reference": row.reference,
                    "description": row.entry_desc or row.line_desc,
                    "debit": float(dr),
                    "credit": float(cr),
                    "balance": float(running_balance),
                }
            )

        return {
            "account": {
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "type": account.account_type,
            },
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
            "entries": entries,
            "closing_balance": float(running_balance),
        }

    # -----------------------------------------------------------------------
    # Journal entries list (paginated)
    # -----------------------------------------------------------------------
    async def list_journal_entries(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        q = (
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines).selectinload(JournalLine.account))
            .where(JournalEntry.organization_id == self.org_id)
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        )
        if status:
            q = q.where(JournalEntry.status == status)
        if from_date:
            q = q.where(JournalEntry.entry_date >= from_date)
        if to_date:
            q = q.where(JournalEntry.entry_date <= to_date)

        total_result = await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = total_result.scalar() or 0

        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(q)
        entries = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_entry_to_dict(e) for e in entries],
        }

    # -----------------------------------------------------------------------
    # Financial Year Lock
    # -----------------------------------------------------------------------
    async def lock_financial_year(
        self, year: int, locked_by: uuid.UUID | None = None
    ) -> FinancialYear:
        result = await self.db.execute(
            select(FinancialYear).where(
                FinancialYear.organization_id == self.org_id,
                FinancialYear.year == year,
            )
        )
        fy = result.scalar_one_or_none()
        if not fy:
            fy = FinancialYear(organization_id=self.org_id, year=year)
            self.db.add(fy)

        if fy.is_locked:
            raise ValueError(f"Financial year {year} is already locked")

        fy.is_locked = True
        fy.locked_by = locked_by
        fy.locked_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info("financial_year_locked", year=year, org_id=str(self.org_id))
        return fy


def _entry_to_dict(e: JournalEntry) -> dict[str, Any]:
    return {
        "id": str(e.id),
        "date": str(e.entry_date),
        "reference": e.reference,
        "description": e.description,
        "status": e.status,
        "source": e.source,
        "fiscal_year": e.fiscal_year,
        "lines": [
            {
                "account_id": str(l.account_id),
                "account_code": l.account.code if l.account else None,
                "account_name": l.account.name if l.account else None,
                "debit": float(l.debit),
                "credit": float(l.credit),
                "description": l.description,
            }
            for l in (e.lines or [])
        ],
    }
