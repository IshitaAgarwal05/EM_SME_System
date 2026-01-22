"""
Analytics service for financial insights and reporting.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Transaction, Payment, Contractor
from app.models.task import Task
from app.models.user import User

logger = structlog.get_logger()


class AnalyticsService:
    """Service for generating analytics and reports."""

    def __init__(self, db: AsyncSession, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id

    async def get_financial_summary(self, start_date: date, end_date: date, include_unreconciled: bool = True) -> dict[str, Any]:
        """
        Get high-level financial summary (Total Income, Total Expense, Net).
        """
        filters = [
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ]
        if not include_unreconciled:
            filters.append(Transaction.is_reconciled == True)

        query = select(
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('expense')
        ).where(and_(*filters))
        
        result = await self.db.execute(query)
        row = result.one()
        
        income = float(row.income or 0)
        expense = float(row.expense or 0)
        
        return {
            "period": {"start": start_date, "end": end_date},
            "total_income": income,
            "total_expense": expense,
            "net_profit": income - expense
        }

    async def get_monthly_trends(self, year: int, include_unreconciled: bool = True) -> list[dict[str, Any]]:
        """Get monthly income vs expense for a given year."""
        filters = [
            Transaction.organization_id == self.organization_id,
            func.extract('year', Transaction.transaction_date) == year
        ]
        if not include_unreconciled:
            filters.append(Transaction.is_reconciled == True)

        query = select(
            func.extract('month', Transaction.transaction_date).label('month'),
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('expense')
        ).where(and_(*filters)).group_by(
            func.extract('month', Transaction.transaction_date)
        ).order_by('month')
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Fill missing months
        monthly_data = {int(r.month): {"income": float(r.income or 0), "expense": float(r.expense or 0)} for r in rows}
        
        trends = []
        for month in range(1, 13):
            data = monthly_data.get(month, {"income": 0.0, "expense": 0.0})
            trends.append({
                "month": month,
                "income": data["income"],
                "expense": data["expense"],
                "net": data["income"] - data["expense"]
            })
            
        return trends

    async def get_details_by_category(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Get expense breakdown by category. Coalesces NULL and 'Uncategorized' into one bucket."""
        query = select(
            func.coalesce(
                func.nullif(Transaction.category, ''),
                func.nullif(Transaction.category, 'Uncategorized'),
                'Uncategorized'
            ).label('category'),
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            func.coalesce(
                func.nullif(Transaction.category, ''),
                func.nullif(Transaction.category, 'Uncategorized'),
                'Uncategorized'
            )
        ).order_by(func.sum(Transaction.amount).desc())

        result = await self.db.execute(query)
        rows = result.all()

        # Merge any remaining duplicate 'Uncategorized' rows in Python
        merged: dict[str, float] = {}
        for row in rows:
            cat = row.category if row.category and row.category.strip() and row.category != 'Uncategorized' else 'Uncategorized'
            merged[cat] = merged.get(cat, 0.0) + float(row.total or 0)

        return [
            {"category": cat, "amount": amt}
            for cat, amt in sorted(merged.items(), key=lambda x: -x[1])
        ]

    async def get_contractor_spend(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Get spending breakdown by contractor.
        Primary: Payments linked to contractors.
        Fallback: Transactions categorised as 'Contractor' when no Payment records exist.
        """
        # Primary: formal contractor payments
        payment_query = select(
            Contractor.name,
            func.sum(Payment.amount).label('total')
        ).join(
            Payment, Payment.contractor_id == Contractor.id
        ).where(
            Payment.organization_id == self.organization_id,
            or_(
                and_(Payment.payment_date != None,
                     Payment.payment_date >= start_date,
                     Payment.payment_date <= end_date),
                and_(Payment.payment_date == None,
                     Payment.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                     Payment.created_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc))
            )
        ).group_by(Contractor.name).order_by(func.sum(Payment.amount).desc())

        result = await self.db.execute(payment_query)
        payment_rows = [
            {"contractor": row.name, "amount": float(row.total or 0)}
            for row in result
        ]

        if payment_rows:
            return payment_rows

        # Fallback: transactions with category containing 'contractor' or 'vendor'
        txn_query = select(
            Transaction.counterparty,
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type == 'debit',
            or_(
                func.lower(Transaction.category).contains('contractor'),
                func.lower(Transaction.category).contains('vendor'),
                func.lower(Transaction.category).contains('salary'),
            )
        ).group_by(Transaction.counterparty).order_by(func.sum(Transaction.amount).desc())

        txn_result = await self.db.execute(txn_query)
        return [
            {"contractor": row.counterparty or "Unknown", "amount": float(row.total or 0)}
            for row in txn_result
        ]

    async def get_monthly_breakdown(self, month: int, year: int, include_unreconciled: bool = True) -> dict[str, Any]:
        """Get detailed breakdown for a specific month."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        filters = [
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ]
        if not include_unreconciled:
            filters.append(Transaction.is_reconciled == True)
            
        query = select(
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('expense')
        ).where(and_(*filters))
        
        result = await self.db.execute(query)
        row = result.one()
        
        return {
            "month": month,
            "year": year,
            "income": float(row.income or 0),
            "expense": float(row.expense or 0),
            "net": float((row.income or 0) - (row.expense or 0))
        }

    async def get_top_expenses(self, limit: int = 5, include_unreconciled: bool = True) -> list[dict[str, Any]]:
        """Get top expenses by amount."""
        filters = [
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_type == 'debit'
        ]
        if not include_unreconciled:
            filters.append(Transaction.is_reconciled == True)
            
        query = select(Transaction).where(and_(*filters)).order_by(Transaction.amount.desc()).limit(limit)
        result = await self.db.execute(query)
        txns = result.scalars().all()
        
        return [
            {
                "date": t.transaction_date,
                "description": t.description,
                "counterparty": t.counterparty,
                "amount": float(t.amount)
            } for t in txns
        ]

    async def get_total_client_payments(self, include_unreconciled: bool = True) -> dict[str, Any]:
        """Get sum of all client payments (credits)."""
        filters = [
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_type == 'credit'
        ]
        if not include_unreconciled:
            filters.append(Transaction.is_reconciled == True)
            
        query = select(func.sum(Transaction.amount)).where(and_(*filters))
        result = await self.db.execute(query)
        total = result.scalar() or 0
        
        return {"total_client_payments": float(total)}

    async def get_fy_summary(self, fy_start_year: int) -> dict[str, Any]:
        """
        Get summary for the Indian Financial Year (April 1st to March 31st).
        """
        start_date = date(fy_start_year, 4, 1)
        end_date = date(fy_start_year + 1, 3, 31)
        
        return await self.get_financial_summary(start_date, end_date)

    async def categorize_transactions(self, user_categories: list[str] | None = None) -> dict[str, Any]:
        """
        AI-driven transaction categorization based on description.
        If user_categories provided, prioritizes matching against them.
        """
        query = select(Transaction).where(
            Transaction.organization_id == self.organization_id,
            or_(Transaction.category == None, Transaction.category == 'Uncategorized')
        )
        result = await self.db.execute(query)
        txns = result.scalars().all()
        
        rules = {
            "Food": ["swiggy", "zomato", "restaurant", "cafe", "food"],
            "Travel": ["uber", "ola", "travel", "flight", "indigo", "railway"],
            "Maintenance": ["repair", "fix", "plumber", "clean", "service"],
            "Utility": ["electricity", "bill", "recharge", "water", "bbps"],
            "Salary": ["salary", "payout", "bonus"],
            "Contractor": ["payment", "vendor", "contractor"]
        }
        if user_categories:
            for cat in user_categories:
                rules[cat.capitalize()] = [cat.lower()]

        count = 0
        for t in txns:
            desc = t.description.lower()
            matched = False
            for cat, keywords in rules.items():
                if any(kw in desc for kw in keywords):
                    t.category = cat
                    matched = True
                    count += 1
                    break
            
            if not matched:
                t.category = "Uncategorized"
                
        await self.db.commit()
        return {"categorized_count": count, "total_uncategorized": len(txns)}

    async def get_cashflow_forecast(self, months_ahead: int = 3, ref_date: date | None = None) -> list[dict[str, Any]]:
        """
        Predict future cashflow based on the last 6 months of data relative to ref_date.
        """
        # Get last 6 months trends
        if not ref_date:
            ref_date = date.today()
        
        start_date = ref_date - timedelta(days=180)
        
        # We reuse get_monthly_trends but it only takes a year. 
        # For forecast, let's get raw data for last 6 months.
        query = select(
            func.extract('year', Transaction.transaction_date).label('year'),
            func.extract('month', Transaction.transaction_date).label('month'),
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('expense')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date
        ).group_by(
            'year', 'month'
        ).order_by('year', 'month')
        
        result = await self.db.execute(query)
        rows = result.all()
        
        if not rows:
            return []

        # Calculate averages/growth
        avg_income = sum(float(r.income or 0) for r in rows) / len(rows)
        avg_expense = sum(float(r.expense or 0) for r in rows) / len(rows)
        
        forecast = []
        last_month = int(rows[-1].month)
        last_year = int(rows[-1].year)
        
        # Project future
        for i in range(1, months_ahead + 1):
            next_month = (last_month + i - 1) % 12 + 1
            next_year = last_year + (last_month + i - 1) // 12
            
            # Simple simulation: assume slight 2% growth in income and 1% in expenses
            projected_income = avg_income * (1.02 ** i)
            projected_expense = avg_expense * (1.01 ** i)
            
            forecast.append({
                "month": next_month,
                "year": next_year,
                "date": f"{next_year}-{next_month:02d}-01",
                "income": round(projected_income, 2),
                "expense": round(projected_expense, 2),
                "is_projection": True
            })
            
        return forecast

    async def get_spending_anomalies(self, ref_date: date | None = None) -> list[dict[str, Any]]:
        """
        Detect transactions that deviate significantly from category averages relative to ref_date.
        """
        # Get category averages from last 6 months
        if not ref_date:
            ref_date = date.today()
        
        start_date = ref_date - timedelta(days=180)
        
        # Subquery for category stats
        stats_query = select(
            Transaction.category,
            func.avg(Transaction.amount).label('avg_amount'),
            func.stddev(Transaction.amount).label('std_amount')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_type == 'debit',
            Transaction.transaction_date >= start_date
        ).group_by(Transaction.category)
        
        stats_result = await self.db.execute(stats_query)
        cat_stats = {r.category: (float(r.avg_amount), float(r.std_amount or 0)) for r in stats_result}
        
        # Find current month anomalies
        cur_start = ref_date.replace(day=1)
        cur_query = select(Transaction).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_type == 'debit',
            Transaction.transaction_date >= cur_start
        )
        
        cur_result = await self.db.execute(cur_query)
        anomalies = []
        
        for t in cur_result.scalars().all():
            if t.category in cat_stats:
                avg, std = cat_stats[t.category]
                # If transaction > avg + 2*std
                if float(t.amount) > (avg + 2 * std) and float(t.amount) > 5000: # Min threshold for noise
                    anomalies.append({
                        "id": str(t.id),
                        "date": t.transaction_date,
                        "description": t.description,
                        "category": t.category,
                        "amount": float(t.amount),
                        "average": round(avg, 2),
                        "deviation_score": round((float(t.amount) - avg) / (std if std > 0 else 1), 2)
                    })
        
        return sorted(anomalies, key=lambda x: x['deviation_score'], reverse=True)

    async def get_savings_insights(self, ref_date: date | None = None) -> list[dict[str, Any]]:
        """
        Analyze recurring expenses and trends to suggest savings relative to ref_date.
        """
        # Example logic: Find categories where spend increased in last 2 months vs prev 4
        if not ref_date:
            ref_date = date.today()
        
        # Prev 2 months
        p2_start = ref_date - timedelta(days=60)
        # Prev 4 months before that
        p4_start = ref_date - timedelta(days=180)
        p4_end = p2_start
        
        def get_cat_spend_query(s, e):
            return select(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            ).where(
                Transaction.organization_id == self.organization_id,
                Transaction.transaction_type == 'debit',
                Transaction.transaction_date >= s,
                Transaction.transaction_date <= e
            ).group_by(Transaction.category)

        res_p2 = await self.db.execute(get_cat_spend_query(p2_start, ref_date))
        res_p4 = await self.db.execute(get_cat_spend_query(p4_start, p4_end))
        
        m2_spend = {r.category: float(r.total) / 2 for r in res_p2} # monthly avg
        m4_spend = {r.category: float(r.total) / 4 for r in res_p4} # monthly avg
        
        insights = []
        for cat, cur_avg in m2_spend.items():
            if cat in m4_spend:
                prev_avg = m4_spend[cat]
                if cur_avg > prev_avg * 1.2: # 20% increase
                    insights.append({
                        "category": cat,
                        "insight": f"Spending on {cat} has increased by {round(((cur_avg/prev_avg)-1)*100)}% recently.",
                        "recommendation": f"Review {cat} subscriptions or vendor contracts to optimize costs.",
                        "potential_monthly_saving": round(cur_avg - prev_avg, 2),
                        "urgency": "medium"
                    })
        
        return insights

    # Categories treated as Cost of Sales / COGS
    COGS_CATEGORIES = {
        "purchase", "purchases", "cogs", "cost of goods", "cost of sales",
        "stock", "materials", "raw materials", "inventory", "merchandise"
    }

    async def get_pl_statement(self, year: int) -> dict[str, Any]:
        """Calculate P&L — Schedule III format with current + previous year comparison."""

        async def _fetch_year(y: int) -> dict:
            inc_q = select(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            ).where(
                Transaction.organization_id == self.organization_id,
                func.extract('year', Transaction.transaction_date) == y,
                Transaction.transaction_type == 'credit'
            ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())

            exp_q = select(
                Transaction.category,
                func.sum(Transaction.amount).label('total')
            ).where(
                Transaction.organization_id == self.organization_id,
                func.extract('year', Transaction.transaction_date) == y,
                Transaction.transaction_type == 'debit'
            ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())

            inc_res = await self.db.execute(inc_q)
            exp_res = await self.db.execute(exp_q)

            revenue_items = [
                {"category": row.category or "Sales / Revenue", "amount": float(row.total or 0)}
                for row in inc_res
            ]
            total_revenue = sum(i["amount"] for i in revenue_items)

            all_expense_rows = [
                {"category": row.category or "General Expenses", "amount": float(row.total or 0)}
                for row in exp_res
            ]

            # Categorise expenses into Schedule III buckets
            cost_of_materials, purchases, inventory_changes = 0.0, 0.0, 0.0
            employee_expense, finance_costs, depreciation = 0.0, 0.0, 0.0
            other_expenses_total = 0.0
            other_expenses_rows = []

            EMPLOYEE_CATS  = {"salary", "salaries", "wages", "payroll", "employee", "staff"}
            FINANCE_CATS   = {"interest", "bank charges", "finance", "loan"}
            DEPN_CATS      = {"depreciation", "amortisation", "amortization"}
            COG_CATS       = self.COGS_CATEGORIES  # purchase, cogs, stock, materials…

            for row in all_expense_rows:
                cat = row["category"].strip().lower()
                amt = row["amount"]
                if cat in COG_CATS:
                    if any(k in cat for k in ("material", "raw")):
                        cost_of_materials += amt
                    elif any(k in cat for k in ("stock", "inventory", "merchandise")):
                        purchases += amt
                    else:
                        purchases += amt
                elif any(k in cat for k in EMPLOYEE_CATS):
                    employee_expense += amt
                elif any(k in cat for k in FINANCE_CATS):
                    finance_costs += amt
                elif any(k in cat for k in DEPN_CATS):
                    depreciation += amt
                else:
                    other_expenses_total += amt
                    other_expenses_rows.append(row)

            total_expenses = cost_of_materials + purchases + inventory_changes + \
                             employee_expense + finance_costs + depreciation + other_expenses_total
            profit_before_tax = total_revenue - total_expenses

            return {
                "revenue_items":     revenue_items,
                "total_revenue":     total_revenue,
                "other_income":      0.0,
                "total_rev_inc":     total_revenue,
                "cost_of_materials": cost_of_materials,
                "purchases":         purchases,
                "inventory_changes": inventory_changes,
                "employee_expense":  employee_expense,
                "finance_costs":     finance_costs,
                "depreciation":      depreciation,
                "other_expenses":    other_expenses_total,
                "other_expense_rows": other_expenses_rows,
                "total_expenses":    total_expenses,
                "profit_before_tax": profit_before_tax,
                "tax":               0.0,
                "profit_after_tax":  profit_before_tax,
                # legacy
                "total_income":   total_revenue,
                "total_expense":  total_expenses,
                "gross_profit":   total_revenue - purchases - cost_of_materials,
                "net_profit":     profit_before_tax,
            }

        cur = await _fetch_year(year)
        prv = await _fetch_year(year - 1)

        def row(name: str, c: float, p: float) -> dict:
            return {"name": name, "current": c, "previous": p}

        return {
            "year":          year,
            "previous_year": year - 1,

            # Schedule III rows
            "revenue_from_ops":  row("I. Revenue from Operations",          cur["total_revenue"],     prv["total_revenue"]),
            "other_income":      row("II. Other Income",                     cur["other_income"],      prv["other_income"]),
            "total_revenue":     row("III. Total Revenue (I + II)",          cur["total_rev_inc"],     prv["total_rev_inc"]),
            "cost_of_materials": row("Cost of Materials Consumed",           cur["cost_of_materials"], prv["cost_of_materials"]),
            "purchases":         row("Purchase of Stock-in-Trade",           cur["purchases"],         prv["purchases"]),
            "inventory_changes": row("Changes in Inventories",               cur["inventory_changes"], prv["inventory_changes"]),
            "employee_expense":  row("Employee Benefit Expense",             cur["employee_expense"],  prv["employee_expense"]),
            "finance_costs":     row("Finance Costs",                        cur["finance_costs"],     prv["finance_costs"]),
            "depreciation":      row("Depreciation and Amortisation Expense",cur["depreciation"],      prv["depreciation"]),
            "other_expenses":    row("Other Expenses",                       cur["other_expenses"],    prv["other_expenses"]),
            "other_expense_rows": cur["other_expense_rows"],
            "total_expenses":    row("IV. Total Expenses",                   cur["total_expenses"],    prv["total_expenses"]),
            "profit_before_tax": row("V. Profit before Tax (III - IV)",      cur["profit_before_tax"], prv["profit_before_tax"]),
            "tax":               row("VI. Tax",                              cur["tax"],               prv["tax"]),
            "profit_after_tax":  row("VII. Profit after Tax (V - VI)",       cur["profit_after_tax"],  prv["profit_after_tax"]),

            # legacy flat fields so existing callers don't break
            "income":       cur["revenue_items"],
            "expenses":     cur["other_expense_rows"],
            "total_income": cur["total_revenue"],
            "total_expense":cur["total_expenses"],
            "gross_profit": cur["gross_profit"],
            "net_profit":   cur["profit_after_tax"],
            "revenue":      cur["revenue_items"],
            "operating_expenses": cur["other_expense_rows"],
            "total_revenue_val": cur["total_revenue"],
            "total_opex":  cur["other_expenses"],
            "total_cogs":  cur["cost_of_materials"] + cur["purchases"],
            "cost_of_sales": [],
        }

    async def get_bs_statement(self, year: int | None = None) -> dict[str, Any]:
        """Balance Sheet — Schedule III format with current + previous period comparison."""
        from datetime import date as date_type

        current_year  = year or date_type.today().year
        previous_year = current_year - 1
        current_end   = date_type(current_year, 12, 31)
        previous_end  = date_type(previous_year, 12, 31)

        async def _cash(end: date_type) -> float:
            q = select(func.sum(case(
                (Transaction.transaction_type == 'credit', Transaction.amount),
                else_=-Transaction.amount
            ))).where(
                Transaction.organization_id == self.organization_id,
                Transaction.transaction_date <= end,
            )
            return float((await self.db.execute(q)).scalar() or 0)

        async def _trade_rec(end: date_type) -> float:
            q = select(func.sum(Transaction.amount)).where(
                Transaction.organization_id == self.organization_id,
                Transaction.transaction_type == 'credit',
                Transaction.is_reconciled == False,
                Transaction.transaction_date <= end,
            )
            return float((await self.db.execute(q)).scalar() or 0)

        async def _pay(statuses: list, end: date_type) -> float:
            q = select(func.sum(Payment.amount)).where(
                Payment.organization_id == self.organization_id,
                Payment.status.in_(statuses),
                Payment.created_at <= datetime.combine(end, datetime.max.time()).replace(tzinfo=timezone.utc),
            )
            return float((await self.db.execute(q)).scalar() or 0)

        # Current period
        cur_cash      = await _cash(current_end)
        cur_trade_rec = await _trade_rec(current_end)
        cur_trade_pay = await _pay(['pending'], current_end)
        cur_other_cl  = await _pay(['processing'], current_end)
        cur_total_ca  = cur_cash + cur_trade_rec
        cur_equity    = cur_total_ca - (cur_trade_pay + cur_other_cl)

        # Previous period
        prv_cash      = await _cash(previous_end)
        prv_trade_rec = await _trade_rec(previous_end)
        prv_trade_pay = await _pay(['pending'], previous_end)
        prv_other_cl  = await _pay(['processing'], previous_end)
        prv_total_ca  = prv_cash + prv_trade_rec
        prv_equity    = prv_total_ca - (prv_trade_pay + prv_other_cl)

        def row(name: str, c: float, p: float) -> dict:
            return {"name": name, "current": c, "previous": p}

        cur_total = cur_total_ca
        prv_total = prv_total_ca

        return {
            "current_year":  current_year,
            "previous_year": previous_year,

            # ── I. EQUITY & LIABILITIES ──────────────────────────────────
            "shareholder_funds": {
                "share_capital":    row("(a) Share Capital",        0,           0),
                "reserves_surplus": row("(b) Reserves and Surplus", cur_equity,  prv_equity),
            },
            "non_current_liabilities": {
                "long_term_borrowings":  row("(a) Long-term Borrowings",          0, 0),
                "deferred_tax_liab":     row("(b) Deferred Tax Liabilities (Net)",0, 0),
                "other_ltl":             row("(c) Other Long-term Liabilities",   0, 0),
                "long_term_provisions":  row("(d) Long-term Provisions",          0, 0),
            },
            "current_liabilities": {
                "short_term_borrowings": row("(a) Short-term Borrowings",    0,             0),
                "trade_payables":        row("(b) Trade Payables",            cur_trade_pay, prv_trade_pay),
                "other_current_liab":    row("(c) Other Current Liabilities", cur_other_cl,  prv_other_cl),
                "short_term_provisions": row("(d) Short-term Provisions",    0,             0),
            },
            "total_equity_liab": row("Total", cur_total, prv_total),

            # ── II. ASSETS ────────────────────────────────────────────────
            "non_current_assets": {
                "tangible_assets":      row("(i) Tangible Assets",            0, 0),
                "intangible_assets":    row("(ii) Intangible Assets",         0, 0),
                "capital_wip":          row("(iii) Capital Work-in-Progress", 0, 0),
                "non_current_invest":   row("(b) Non-current Investments",    0, 0),
                "deferred_tax_assets":  row("(c) Deferred Tax Assets (Net)",  0, 0),
                "long_term_loans":      row("(d) Long-term Loans & Advances", 0, 0),
                "other_nca":            row("(e) Other Non-current Assets",   0, 0),
            },
            "current_assets": {
                "current_investments":  row("(a) Current Investments",        0,             0),
                "inventories":          row("(b) Inventories",                0,             0),
                "trade_receivables":    row("(c) Trade Receivables",          cur_trade_rec, prv_trade_rec),
                "cash_equivalents":     row("(d) Cash and Cash Equivalents",  cur_cash,      prv_cash),
                "short_term_loans":     row("(e) Short-term Loans & Advances",0,             0),
                "other_current_assets": row("(f) Other Current Assets",       0,             0),
            },
            "total_assets": row("Total", cur_total, prv_total),

            # legacy flat fields for backward compat
            "equity":                     cur_equity,
            "total_current_assets":       cur_total_ca,
            "total_current_liabilities":  cur_trade_pay + cur_other_cl,
            "total_equity_and_liabilities": cur_total,
            "assets":      [{"name": "Cash and Cash Equivalents", "amount": cur_cash},
                            {"name": "Trade Receivables",         "amount": cur_trade_rec}],
            "liabilities": [{"name": "Trade Payables",            "amount": cur_trade_pay},
                            {"name": "Other Current Liabilities", "amount": cur_other_cl}],
        }

    async def get_cashflow_statement(self, year: int) -> dict[str, Any]:
        """Calculate Cash Flow Statement (indirect method).
        Sections: Operating, Investing, Financing Activities.
        """
        from datetime import date as date_type
        start_date = date_type(year, 1, 1)
        end_date   = date_type(year, 12, 31)

        # ── Operating: all transactions in the year ─────────────────────────
        ops_query = select(
            Transaction.category,
            Transaction.transaction_type,
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        ).group_by(Transaction.category, Transaction.transaction_type
        ).order_by(func.sum(Transaction.amount).desc())

        ops_res = await self.db.execute(ops_query)
        rows = ops_res.all()

        operating_inflows  = []
        operating_outflows = []
        for row in rows:
            cat = row.category or ("Revenue" if row.transaction_type == 'credit' else "Expenses")
            amt = float(row.total or 0)
            if row.transaction_type == 'credit':
                operating_inflows.append({"name": cat, "amount": amt})
            else:
                operating_outflows.append({"name": cat, "amount": amt})

        total_inflows  = sum(r["amount"] for r in operating_inflows)
        total_outflows = sum(r["amount"] for r in operating_outflows)
        net_operating  = total_inflows - total_outflows

        # ── Financing: completed contractor payments in the year ─────────────
        fin_query = select(func.sum(Payment.amount)).where(
            Payment.organization_id == self.organization_id,
            Payment.status == 'completed',
            or_(
                and_(Payment.payment_date >= start_date, Payment.payment_date <= end_date),
                and_(Payment.payment_date == None,
                     Payment.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                     Payment.created_at <= datetime.combine(end_date,   datetime.max.time()).replace(tzinfo=timezone.utc))
            )
        )
        fin_outflows = float((await self.db.execute(fin_query)).scalar() or 0)
        net_financing = -fin_outflows  # outflow to contractors

        net_change = net_operating + net_financing

        # Opening balance: net cash before this year
        opening_query = select(
            func.sum(case(
                (Transaction.transaction_type == 'credit', Transaction.amount),
                else_=-Transaction.amount
            ))
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date < start_date,
        )
        opening_balance = float((await self.db.execute(opening_query)).scalar() or 0)
        closing_balance = opening_balance + net_change

        return {
            "year": year,
            "operating_inflows":  operating_inflows,
            "operating_outflows": operating_outflows,
            "total_inflows":      total_inflows,
            "total_outflows":     total_outflows,
            "net_operating":      net_operating,
            "financing_outflows": [{"name": "Contractor Payments", "amount": fin_outflows}] if fin_outflows else [],
            "net_financing":      net_financing,
            "net_investing":      0.0,
            "net_change":         net_change,
            "opening_balance":    opening_balance,
            "closing_balance":    closing_balance,
        }
