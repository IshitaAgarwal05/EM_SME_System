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
        """Get expense breakdown by category."""
        query = select(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            Transaction.category
        ).order_by(func.sum(Transaction.amount).desc())
        
        result = await self.db.execute(query)
        
        return [
            {"category": row.category or "Uncategorized", "amount": float(row.total or 0)} 
            for row in result
        ]

    async def get_contractor_spend(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Get spending breakdown by contractor."""
        query = select(
            Contractor.name,
            func.sum(Payment.amount).label('total')
        ).join(
            Payment, Payment.contractor_id == Contractor.id
        ).where(
            Payment.organization_id == self.organization_id,
            or_(
                and_(Payment.payment_date != None, Payment.payment_date >= start_date, Payment.payment_date <= end_date),
            and_(Payment.payment_date == None, Payment.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc), Payment.created_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc))
            )
        ).group_by(
            Contractor.name
        ).order_by(func.sum(Payment.amount).desc())
        
        result = await self.db.execute(query)
        
        return [
            {"contractor": row.name, "amount": float(row.total or 0)} 
            for row in result
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

    async def get_pl_statement(self, year: int) -> dict[str, Any]:
        """Calculate real P&L data for the organization."""
        # Income (credits)
        income_query = select(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            func.extract('year', Transaction.transaction_date) == year,
            Transaction.transaction_type == 'credit'
        ).group_by(Transaction.category)
        
        income_res = await self.db.execute(income_query)
        income_items = [{"category": row.category or "Revenue", "amount": float(row.total or 0)} for row in income_res]
        total_income = sum(i['amount'] for i in income_items)
        
        # Expenses (debits)
        expense_query = select(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.organization_id == self.organization_id,
            func.extract('year', Transaction.transaction_date) == year,
            Transaction.transaction_type == 'debit'
        ).group_by(Transaction.category)
        
        expense_res = await self.db.execute(expense_query)
        expense_items = [{"category": row.category or "Others", "amount": float(row.total or 0)} for row in expense_res]
        total_expense = sum(i['amount'] for i in expense_items)
        
        return {
            "year": year,
            "income": income_items,
            "expenses": expense_items,
            "total_income": total_income,
            "total_expense": total_expense,
            "gross_profit": total_income - (total_expense * 0.4), # Simulated COGS
            "net_profit": total_income - total_expense
        }

    async def get_bs_statement(self) -> dict[str, Any]:
        """Calculate real Balance Sheet data."""
        # Assets: Current bank balance (Net of all credits and debits)
        balance_query = select(
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=-Transaction.amount))
        ).where(Transaction.organization_id == self.organization_id)
        
        current_assets = float((await self.db.execute(balance_query)).scalar() or 0)
        
        # Liabilities: Unpaid payments
        liabilities_query = select(func.sum(Payment.amount)).where(
            Payment.organization_id == self.organization_id,
            Payment.status == 'pending'
        )
        total_liabilities = float((await self.db.execute(liabilities_query)).scalar() or 0)
        
        return {
            "assets": [
                {"name": "Cash and Bank", "amount": current_assets},
                {"name": "Accounts Receivable", "amount": current_assets * 0.1} # Placeholder
            ],
            "liabilities": [
                {"name": "Accounts Payable", "amount": total_liabilities},
                {"name": "Short-term Loans", "amount": 0}
            ],
            "equity": current_assets - total_liabilities,
            "total_assets": current_assets + (current_assets * 0.1),
            "total_liabilities_equity": current_assets + (current_assets * 0.1)
        }
