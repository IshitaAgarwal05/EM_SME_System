"""
Receivables Aging & Payables service.

Computes standard aging buckets: 0-30, 31-60, 61-90, 90+ days overdue.
Works from invoices (receivables) and payments table (payables).
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Payment
from app.models.invoice import Invoice


BUCKETS = [
    ("current", 0, 30),
    ("31_60", 31, 60),
    ("61_90", 61, 90),
    ("over_90", 91, None),
]


def _assign_bucket(days_overdue: int) -> str:
    for name, lo, hi in BUCKETS:
        if hi is None and days_overdue >= lo:
            return name
        if hi is not None and lo <= days_overdue <= hi:
            return name
    return "current"


class AgingService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id

    async def get_receivables_aging(
        self, as_of_date: date | None = None
    ) -> dict[str, Any]:
        """
        Returns receivables aging: per-client breakdown and bucket summary.
        Source: invoices table (status != paid/void).
        """
        as_of = as_of_date or date.today()

        result = await self.db.execute(
            select(Invoice).where(
                Invoice.organization_id == self.org_id,
                Invoice.status.in_(["sent", "partial"]),
                Invoice.total_amount > Invoice.paid_amount,
            )
        )
        invoices = result.scalars().all()

        summary: dict[str, Decimal] = {b[0]: Decimal("0") for b in BUCKETS}
        clients: dict[str, dict] = {}

        for inv in invoices:
            outstanding = inv.total_amount - inv.paid_amount
            ref_date = inv.due_date or inv.issue_date
            days_overdue = (as_of - ref_date).days if as_of > ref_date else 0
            bucket = _assign_bucket(days_overdue)
            summary[bucket] += outstanding

            if inv.client_name not in clients:
                clients[inv.client_name] = {
                    "client": inv.client_name,
                    "total_outstanding": Decimal("0"),
                    "invoices": [],
                    "buckets": {b[0]: Decimal("0") for b in BUCKETS},
                }
            clients[inv.client_name]["total_outstanding"] += outstanding
            clients[inv.client_name]["buckets"][bucket] += outstanding
            clients[inv.client_name]["invoices"].append(
                {
                    "invoice_number": inv.invoice_number,
                    "issue_date": str(inv.issue_date),
                    "due_date": str(inv.due_date) if inv.due_date else None,
                    "total": float(inv.total_amount),
                    "outstanding": float(outstanding),
                    "days_overdue": days_overdue,
                    "bucket": bucket,
                }
            )

        return {
            "as_of_date": str(as_of),
            "summary": {k: float(v) for k, v in summary.items()},
            "total_outstanding": float(sum(summary.values())),
            "clients": sorted(
                [
                    {
                        **c,
                        "total_outstanding": float(c["total_outstanding"]),
                        "buckets": {k: float(v) for k, v in c["buckets"].items()},
                    }
                    for c in clients.values()
                ],
                key=lambda x: x["total_outstanding"],
                reverse=True,
            ),
        }

    async def get_payables_aging(
        self, as_of_date: date | None = None
    ) -> dict[str, Any]:
        """
        Returns payables aging from existing payments table (pending/processing).
        """
        as_of = as_of_date or date.today()

        result = await self.db.execute(
            select(Payment).where(
                Payment.organization_id == self.org_id,
                Payment.status.in_(["pending", "processing"]),
            )
        )
        payments = result.scalars().all()

        summary: dict[str, Decimal] = {b[0]: Decimal("0") for b in BUCKETS}
        vendors: dict[str, dict] = {}

        for pay in payments:
            ref_date = pay.due_date or pay.created_at.date()
            days_overdue = (as_of - ref_date).days if as_of > ref_date else 0
            bucket = _assign_bucket(days_overdue)
            summary[bucket] += pay.amount

            vendor_key = str(pay.contractor_id) if pay.contractor_id else "Unassigned"
            if vendor_key not in vendors:
                vendors[vendor_key] = {
                    "vendor_id": vendor_key,
                    "total_outstanding": Decimal("0"),
                    "buckets": {b[0]: Decimal("0") for b in BUCKETS},
                    "bills": [],
                }
            vendors[vendor_key]["total_outstanding"] += pay.amount
            vendors[vendor_key]["buckets"][bucket] += pay.amount
            vendors[vendor_key]["bills"].append(
                {
                    "payment_id": str(pay.id),
                    "amount": float(pay.amount),
                    "due_date": str(pay.due_date) if pay.due_date else None,
                    "days_overdue": days_overdue,
                    "bucket": bucket,
                    "status": pay.status,
                }
            )

        return {
            "as_of_date": str(as_of),
            "summary": {k: float(v) for k, v in summary.items()},
            "total_outstanding": float(sum(summary.values())),
            "vendors": [
                {
                    **v,
                    "total_outstanding": float(v["total_outstanding"]),
                    "buckets": {k: float(v_b) for k, v_b in v["buckets"].items()},
                }
                for v in vendors.values()
            ],
        }

    async def get_overdue_invoices(self) -> list[dict]:
        """Returns all invoices past their due date with outstanding balance."""
        today = date.today()
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.organization_id == self.org_id,
                Invoice.status.in_(["sent", "partial"]),
                Invoice.due_date < today,
                Invoice.total_amount > Invoice.paid_amount,
            ).order_by(Invoice.due_date)
        )
        invoices = result.scalars().all()
        return [
            {
                "invoice_number": inv.invoice_number,
                "client_name": inv.client_name,
                "issue_date": str(inv.issue_date),
                "due_date": str(inv.due_date),
                "days_overdue": (today - inv.due_date).days,
                "total": float(inv.total_amount),
                "outstanding": float(inv.total_amount - inv.paid_amount),
            }
            for inv in invoices
        ]
