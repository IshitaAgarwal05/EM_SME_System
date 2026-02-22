"""
Chart of Accounts (CoA) service.

Responsibilities:
  - Seed default system accounts when a new org is created
  - Retrieve hierarchical account tree
  - Create/update custom accounts per org
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import Account

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Default system accounts (Schedule III aligned)
# ---------------------------------------------------------------------------
DEFAULT_ACCOUNTS: list[dict] = [
    # ── ASSETS ──────────────────────────────────────────────────────────────
    {"code": "1000", "name": "Assets",                        "type": "asset",     "sub_type": "current_asset",     "is_system": True, "parent_code": None},
    {"code": "1010", "name": "Cash in Hand",                  "type": "asset",     "sub_type": "bank_cash",         "is_system": True, "parent_code": "1000"},
    {"code": "1020", "name": "Bank Accounts",                  "type": "asset",     "sub_type": "bank_cash",         "is_system": True, "parent_code": "1000"},
    {"code": "1100", "name": "Accounts Receivable",            "type": "asset",     "sub_type": "current_asset",     "is_system": True, "parent_code": "1000"},
    {"code": "1200", "name": "Inventory",                      "type": "asset",     "sub_type": "current_asset",     "is_system": True, "parent_code": "1000"},
    {"code": "1300", "name": "Prepaid Expenses",               "type": "asset",     "sub_type": "current_asset",     "is_system": True, "parent_code": "1000"},
    {"code": "1500", "name": "Fixed Assets",                   "type": "asset",     "sub_type": "non_current_asset", "is_system": True, "parent_code": "1000"},
    {"code": "1510", "name": "Accumulated Depreciation",       "type": "asset",     "sub_type": "non_current_asset", "is_system": True, "parent_code": "1500"},

    # ── LIABILITIES ──────────────────────────────────────────────────────────
    {"code": "2000", "name": "Liabilities",                    "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": None},
    {"code": "2010", "name": "Accounts Payable",               "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2000"},
    {"code": "2100", "name": "GST Payable",                    "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2000"},
    {"code": "2110", "name": "CGST Payable",                   "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2100"},
    {"code": "2120", "name": "SGST Payable",                   "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2100"},
    {"code": "2130", "name": "IGST Payable",                   "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2100"},
    {"code": "2200", "name": "Short-term Borrowings",          "type": "liability", "sub_type": "current_liability",     "is_system": True, "parent_code": "2000"},
    {"code": "2500", "name": "Long-term Borrowings",           "type": "liability", "sub_type": "non_current_liability", "is_system": True, "parent_code": "2000"},

    # ── EQUITY ────────────────────────────────────────────────────────────────
    {"code": "3000", "name": "Equity",                         "type": "equity",    "sub_type": "equity",            "is_system": True, "parent_code": None},
    {"code": "3010", "name": "Share Capital",                  "type": "equity",    "sub_type": "equity",            "is_system": True, "parent_code": "3000"},
    {"code": "3020", "name": "Retained Earnings",              "type": "equity",    "sub_type": "equity",            "is_system": True, "parent_code": "3000"},

    # ── INCOME ───────────────────────────────────────────────────────────────
    {"code": "4000", "name": "Revenue from Operations",        "type": "income",    "sub_type": "revenue",           "is_system": True, "parent_code": None},
    {"code": "4010", "name": "Service Revenue",                "type": "income",    "sub_type": "revenue",           "is_system": True, "parent_code": "4000"},
    {"code": "4020", "name": "Product Sales",                  "type": "income",    "sub_type": "revenue",           "is_system": True, "parent_code": "4000"},
    {"code": "4100", "name": "Other Income",                   "type": "income",    "sub_type": "other_income",      "is_system": True, "parent_code": "4000"},

    # ── EXPENSES ─────────────────────────────────────────────────────────────
    {"code": "5000", "name": "Expenses",                       "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": None},
    {"code": "5010", "name": "Cost of Goods Sold",             "type": "expense",   "sub_type": "cogs",              "is_system": True, "parent_code": "5000"},
    {"code": "5100", "name": "Employee Benefit Expense",       "type": "expense",   "sub_type": "employee_expense",  "is_system": True, "parent_code": "5000"},
    {"code": "5200", "name": "Depreciation & Amortisation",    "type": "expense",   "sub_type": "depreciation",      "is_system": True, "parent_code": "5000"},
    {"code": "5300", "name": "Finance Costs",                  "type": "expense",   "sub_type": "finance_cost",      "is_system": True, "parent_code": "5000"},
    {"code": "5400", "name": "Other Expenses",                 "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": "5000"},
    {"code": "5410", "name": "Rent",                           "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": "5400"},
    {"code": "5420", "name": "Utilities",                      "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": "5400"},
    {"code": "5430", "name": "Marketing & Advertising",        "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": "5400"},
    {"code": "5440", "name": "Travel & Conveyance",            "type": "expense",   "sub_type": "other_expense",     "is_system": True, "parent_code": "5400"},
]


class CoAService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id

    # -----------------------------------------------------------------------
    # Seeding
    # -----------------------------------------------------------------------
    async def seed_default_accounts(self) -> None:
        """
        Idempotently create the default chart of accounts for an org.
        Safe to call multiple times — skips existing codes.
        """
        # Fetch existing codes once
        existing = await self.db.execute(
            select(Account.code).where(Account.organization_id == self.org_id)
        )
        existing_codes = {row[0] for row in existing.all()}

        # First pass: create root accounts (no parent)
        code_to_id: dict[str, uuid.UUID] = {}
        for spec in DEFAULT_ACCOUNTS:
            if spec["parent_code"] is None and spec["code"] not in existing_codes:
                acct = Account(
                    organization_id=self.org_id,
                    code=spec["code"],
                    name=spec["name"],
                    account_type=spec["type"],
                    sub_type=spec["sub_type"],
                    is_system=spec["is_system"],
                )
                self.db.add(acct)
                await self.db.flush()  # get id before children need it
                code_to_id[spec["code"]] = acct.id
            elif spec["parent_code"] is None:
                # Already exists — fetch it
                row = await self.db.execute(
                    select(Account.id).where(
                        Account.organization_id == self.org_id,
                        Account.code == spec["code"],
                    )
                )
                code_to_id[spec["code"]] = row.scalar_one()

        # Second pass: create child accounts
        for spec in DEFAULT_ACCOUNTS:
            if spec["parent_code"] is not None and spec["code"] not in existing_codes:
                # Ensure parent id is resolved
                parent_id = code_to_id.get(spec["parent_code"])
                if parent_id is None:
                    # Parent may already exist in DB but not in code_to_id (edge case)
                    row = await self.db.execute(
                        select(Account.id).where(
                            Account.organization_id == self.org_id,
                            Account.code == spec["parent_code"],
                        )
                    )
                    parent_id = row.scalar_one_or_none()

                acct = Account(
                    organization_id=self.org_id,
                    parent_id=parent_id,
                    code=spec["code"],
                    name=spec["name"],
                    account_type=spec["type"],
                    sub_type=spec["sub_type"],
                    is_system=spec["is_system"],
                )
                self.db.add(acct)
                await self.db.flush()
                code_to_id[spec["code"]] = acct.id
            elif spec["parent_code"] is not None and spec["code"] in existing_codes:
                row = await self.db.execute(
                    select(Account.id).where(
                        Account.organization_id == self.org_id,
                        Account.code == spec["code"],
                    )
                )
                code_to_id[spec["code"]] = row.scalar_one()

        await self.db.commit()
        logger.info("coa_seeded", org_id=str(self.org_id), count=len(DEFAULT_ACCOUNTS))

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------
    async def get_account_by_code(self, code: str) -> Account | None:
        """Fetch a single account by its code for this org."""
        result = await self.db.execute(
            select(Account).where(
                Account.organization_id == self.org_id,
                Account.code == code,
                Account.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_accounts(self, active_only: bool = True) -> list[Account]:
        """Flat list of all accounts for this org."""
        q = select(Account).where(Account.organization_id == self.org_id)
        if active_only:
            q = q.where(Account.is_active == True)
        q = q.order_by(Account.code)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_account_tree(self) -> list[dict[str, Any]]:
        """
        Returns the full account hierarchy as a nested list of dicts.
        """
        accounts = await self.get_all_accounts()
        by_id = {a.id: _account_to_dict(a) for a in accounts}
        roots: list[dict] = []

        for a in accounts:
            node = by_id[a.id]
            if a.parent_id and a.parent_id in by_id:
                by_id[a.parent_id].setdefault("children", []).append(node)
            else:
                roots.append(node)

        return roots

    async def create_account(
        self,
        code: str,
        name: str,
        account_type: str,
        sub_type: str | None = None,
        parent_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> Account:
        """Create a new custom account for this org."""
        # Validate parent belongs to same org
        if parent_id:
            parent = await self.db.get(Account, parent_id)
            if not parent or parent.organization_id != self.org_id:
                raise ValueError("Parent account not found in this organisation")

        acct = Account(
            organization_id=self.org_id,
            parent_id=parent_id,
            code=code,
            name=name,
            account_type=account_type,
            sub_type=sub_type,
            description=description,
            is_system=False,
        )
        self.db.add(acct)
        await self.db.commit()
        await self.db.refresh(acct)
        return acct

    async def deactivate_account(self, account_id: uuid.UUID) -> Account:
        """Soft-delete an account (cannot deactivate system accounts)."""
        acct = await self.db.get(Account, account_id)
        if not acct or acct.organization_id != self.org_id:
            raise ValueError("Account not found")
        if acct.is_system:
            raise ValueError("System accounts cannot be deactivated")
        acct.is_active = False
        await self.db.commit()
        return acct


def _account_to_dict(a: Account) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "code": a.code,
        "name": a.name,
        "account_type": a.account_type,
        "sub_type": a.sub_type,
        "is_system": a.is_system,
        "is_active": a.is_active,
        "parent_id": str(a.parent_id) if a.parent_id else None,
        "children": [],
    }
