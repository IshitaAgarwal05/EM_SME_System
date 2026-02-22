"""
Audit export service.
Produces CSV/Excel exports of GL, trial balance, and journal register.
Also exposes financial year locking (delegates to AccountingService).
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.accounting_service import AccountingService


class AuditService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id
        self._accounting = AccountingService(db, organization_id)

    async def export_trial_balance_csv(self, as_of: date | None = None) -> bytes:
        data = await self._accounting.get_trial_balance(as_of_date=as_of)
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["code", "name", "account_type", "sub_type",
                        "total_debit", "total_credit", "net_balance"],
        )
        writer.writeheader()
        for row in data["accounts"]:
            writer.writerow({
                "code": row["code"],
                "name": row["name"],
                "account_type": row["account_type"],
                "sub_type": row["sub_type"] or "",
                "total_debit": row["total_debit"],
                "total_credit": row["total_credit"],
                "net_balance": row["net_balance"],
            })
        buf.write(f"\nTotal Debit,{data['grand_total_debit']}\n")
        buf.write(f"Total Credit,{data['grand_total_credit']}\n")
        buf.write(f"Balanced,{data['is_balanced']}\n")
        return buf.getvalue().encode("utf-8")

    async def export_journal_register_csv(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> bytes:
        data = await self._accounting.list_journal_entries(
            page=1, page_size=10000, status="posted",
            from_date=from_date, to_date=to_date,
        )
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Entry ID", "Date", "Reference", "Description",
            "Account Code", "Account Name", "Debit", "Credit",
        ])
        for entry in data["items"]:
            for line in entry["lines"]:
                writer.writerow([
                    entry["id"],
                    entry["date"],
                    entry["reference"] or "",
                    entry["description"],
                    line["account_code"] or "",
                    line["account_name"] or "",
                    line["debit"],
                    line["credit"],
                ])
        return buf.getvalue().encode("utf-8")

    async def export_general_ledger_csv(
        self,
        account_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> bytes:
        data = await self._accounting.get_general_ledger(account_id, from_date, to_date)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Account", f"{data['account']['code']} — {data['account']['name']}"])
        writer.writerow(["Period", f"{from_date or 'all'} to {to_date or 'all'}"])
        writer.writerow([])
        writer.writerow(["Date", "Reference", "Description", "Debit", "Credit", "Balance"])
        for e in data["entries"]:
            writer.writerow([
                e["date"], e["reference"] or "", e["description"],
                e["debit"], e["credit"], e["balance"],
            ])
        writer.writerow([])
        writer.writerow(["Closing Balance", "", "", "", "", data["closing_balance"]])
        return buf.getvalue().encode("utf-8")
