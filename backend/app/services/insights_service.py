"""
Insights service — deterministic business insights derived from DB data.

Role-based insight groups:
  FOUNDER/CEO    — Profitability, cash runway, client risk
  FINANCE HEAD   — Aging risk, expense trends
  OPERATIONS     — (future: event margins, vendor efficiency)
  MARKETING      — Revenue seasonality, client revenue
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import Account, JournalEntry, JournalLine
from app.models.inventory import Item
from app.models.invoice import Invoice
from app.services.aging_service import AgingService


class InsightsService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id

    # -----------------------------------------------------------------------
    # 1. Net Profitability Trend (monthly, last N months)
    # -----------------------------------------------------------------------
    async def net_profitability_trend(self, months: int = 12) -> list[dict[str, Any]]:
        """P&L trend from journal entries grouped by month."""
        today = date.today()
        start = date(today.year, today.month, 1) - timedelta(days=months * 30)

        # Income account totals per month
        income_q = (
            select(
                func.date_trunc("month", JournalEntry.entry_date).label("month"),
                func.coalesce(func.sum(JournalLine.credit), Decimal("0")).label("income"),
            )
            .join(JournalLine, JournalLine.entry_id == JournalEntry.id)
            .join(Account, Account.id == JournalLine.account_id)
            .where(
                JournalEntry.organization_id == self.org_id,
                JournalEntry.status == "posted",
                JournalEntry.entry_date >= start,
                Account.account_type == "income",
            )
            .group_by(func.date_trunc("month", JournalEntry.entry_date))
        )

        # Expense account totals per month
        expense_q = (
            select(
                func.date_trunc("month", JournalEntry.entry_date).label("month"),
                func.coalesce(func.sum(JournalLine.debit), Decimal("0")).label("expense"),
            )
            .join(JournalLine, JournalLine.entry_id == JournalEntry.id)
            .join(Account, Account.id == JournalLine.account_id)
            .where(
                JournalEntry.organization_id == self.org_id,
                JournalEntry.status == "posted",
                JournalEntry.entry_date >= start,
                Account.account_type == "expense",
            )
            .group_by(func.date_trunc("month", JournalEntry.entry_date))
        )

        income_rows = {row.month: row.income for row in (await self.db.execute(income_q)).all()}
        expense_rows = {row.month: row.expense for row in (await self.db.execute(expense_q)).all()}

        all_months = sorted(set(list(income_rows.keys()) + list(expense_rows.keys())))
        trend = []
        for m in all_months:
            inc = float(income_rows.get(m, 0))
            exp = float(expense_rows.get(m, 0))
            trend.append({
                "month": m.strftime("%Y-%m") if m else None,
                "revenue": inc,
                "expenses": exp,
                "net_profit": round(inc - exp, 2),
                "margin_pct": round((inc - exp) / inc * 100, 1) if inc else 0,
            })

        return trend

    # -----------------------------------------------------------------------
    # 2. Client Profitability (from invoices)
    # -----------------------------------------------------------------------
    async def client_profitability(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(
                Invoice.client_name,
                func.sum(Invoice.subtotal).label("total_revenue"),
                func.sum(Invoice.paid_amount).label("total_paid"),
                func.count(Invoice.id).label("invoice_count"),
            )
            .where(
                Invoice.organization_id == self.org_id,
                Invoice.status.notin_(["void", "draft"]),
            )
            .group_by(Invoice.client_name)
            .order_by(func.sum(Invoice.subtotal).desc())
        )
        rows = result.all()
        total_revenue = sum(float(r.total_revenue or 0) for r in rows)
        return [
            {
                "client": r.client_name,
                "total_revenue": float(r.total_revenue or 0),
                "total_paid": float(r.total_paid or 0),
                "invoice_count": r.invoice_count,
                "revenue_share_pct": round(
                    float(r.total_revenue or 0) / total_revenue * 100, 1
                ) if total_revenue else 0,
            }
            for r in rows
        ]

    # -----------------------------------------------------------------------
    # 3. Revenue Concentration Risk
    # -----------------------------------------------------------------------
    async def revenue_concentration(self) -> dict[str, Any]:
        """Herfindahl-like concentration: top client % of total."""
        clients = await self.client_profitability()
        if not clients:
            return {"risk": "low", "top_client_pct": 0, "clients": []}
        top = clients[0]
        risk = "high" if top["revenue_share_pct"] > 50 else "medium" if top["revenue_share_pct"] > 30 else "low"
        return {
            "risk": risk,
            "top_client": top["client"],
            "top_client_pct": top["revenue_share_pct"],
            "clients": clients[:5],
        }

    # -----------------------------------------------------------------------
    # 4. Aging Risk Index
    # -----------------------------------------------------------------------
    async def aging_risk_index(self) -> dict[str, Any]:
        aging_svc = AgingService(self.db, self.org_id)
        aging = await aging_svc.get_receivables_aging()
        total = aging["total_outstanding"]
        over_60 = aging["summary"].get("61_90", 0) + aging["summary"].get("over_90", 0)
        risk_pct = round(over_60 / total * 100, 1) if total else 0
        risk = "high" if risk_pct > 40 else "medium" if risk_pct > 20 else "low"
        return {
            "risk": risk,
            "total_outstanding": total,
            "high_risk_amount": round(over_60, 2),
            "high_risk_pct": risk_pct,
            "buckets": aging["summary"],
        }

    # -----------------------------------------------------------------------
    # 5. Expense Spike Detection (MoM category change)
    # -----------------------------------------------------------------------
    async def expense_spike_detection(self) -> list[dict[str, Any]]:
        """Compare current month vs previous month expense by sub_type."""
        today = date.today()
        cur_start = date(today.year, today.month, 1)
        prev_start = (cur_start - timedelta(days=1)).replace(day=1)
        prev_end = cur_start - timedelta(days=1)

        def month_expense_q(from_d: date, to_d: date):
            return (
                select(
                    Account.sub_type,
                    func.coalesce(func.sum(JournalLine.debit), Decimal("0")).label("amount"),
                )
                .join(JournalLine, JournalLine.account_id == Account.id)
                .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
                .where(
                    Account.organization_id == self.org_id,
                    Account.account_type == "expense",
                    JournalEntry.status == "posted",
                    JournalEntry.entry_date >= from_d,
                    JournalEntry.entry_date <= to_d,
                )
                .group_by(Account.sub_type)
            )

        cur = {r.sub_type: float(r.amount) for r in (await self.db.execute(month_expense_q(cur_start, today))).all()}
        prev = {r.sub_type: float(r.amount) for r in (await self.db.execute(month_expense_q(prev_start, prev_end))).all()}

        results = []
        for cat in set(list(cur.keys()) + list(prev.keys())):
            c = cur.get(cat, 0)
            p = prev.get(cat, 0)
            change_pct = round((c - p) / p * 100, 1) if p else None
            results.append({
                "category": cat,
                "current_month": c,
                "previous_month": p,
                "change_pct": change_pct,
                "is_spike": change_pct is not None and change_pct > 30,
            })

        return sorted(results, key=lambda x: abs(x.get("change_pct") or 0), reverse=True)

    # -----------------------------------------------------------------------
    # 6. Inventory Turnover
    # -----------------------------------------------------------------------
    async def inventory_turnover(self) -> dict[str, Any]:
        """COGS / average inventory value (simple ratio for last 12 months)."""
        from app.models.inventory import InventoryMovement
        today = date.today()
        one_year_ago = today - timedelta(days=365)

        # COGS from journal entries linked to inventory
        cogs_q = (
            select(func.coalesce(func.sum(JournalLine.debit), Decimal("0")))
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .join(Account, Account.id == JournalLine.account_id)
            .where(
                JournalEntry.organization_id == self.org_id,
                JournalEntry.status == "posted",
                JournalEntry.source == "inventory",
                JournalEntry.entry_date >= one_year_ago,
                Account.sub_type == "cogs",
            )
        )
        cogs = float((await self.db.execute(cogs_q)).scalar() or 0)

        # Average inventory value (sum of current_qty * cost_price)
        inv_q = select(
            func.coalesce(func.sum(Item.current_qty * Item.cost_price), Decimal("0"))
        ).where(Item.organization_id == self.org_id, Item.is_active == True)
        avg_inv = float((await self.db.execute(inv_q)).scalar() or 0)

        turnover = round(cogs / avg_inv, 2) if avg_inv else None
        return {
            "cogs_12m": cogs,
            "avg_inventory_value": avg_inv,
            "turnover_ratio": turnover,
            "interpretation": (
                "Good" if turnover and turnover > 4
                else "Average" if turnover and turnover > 2
                else "Low / high stock"
            ),
        }

    # -----------------------------------------------------------------------
    # 7. Dashboard Summary
    # -----------------------------------------------------------------------
    async def get_dashboard_summary(self) -> dict[str, Any]:
        trend = await self.net_profitability_trend(months=3)
        concentration = await self.revenue_concentration()
        risk = await self.aging_risk_index()
        spikes = [s for s in await self.expense_spike_detection() if s["is_spike"]]
        turnover = await self.inventory_turnover()
        return {
            "profitability_trend": trend[-3:] if trend else [],
            "revenue_concentration": concentration,
            "aging_risk": risk,
            "expense_spikes": spikes[:5],
            "inventory_turnover": turnover,
        }
