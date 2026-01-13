from uuid import UUID
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.analytics_service import AnalyticsService
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate

def get_ai_tools(db: AsyncSession, organization_id: UUID):
    """Return list of available tools with DB context."""

    @tool
    async def get_financial_summary_tool(year: int):
        """
        Get financial summary (Income, Expense, Net Profile) for a specific year.
        Useful for answering questions about profit, revenue, or financial health.
        """
        analytics = AnalyticsService(db, organization_id)
        # Assuming get_monthly_trends returns full year breakdown
        trends = await analytics.get_monthly_trends(year)
        
        if not trends:
            return {
                "year": year,
                "total_income": 0,
                "total_expense": 0,
                "net_profit": 0,
                "details": "No financial data found for this year."
            }
        
        total_income = sum(t.get('income', 0) for t in trends)
        total_expense = sum(t.get('expense', 0) for t in trends)
        net = total_income - total_expense
        
        return {
            "year": year,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": net,
            "details": "Breakdown by month available via separate query if needed."
        }
        
    @tool
    async def get_monthly_breakdown_tool(month: int, year: int):
        """
        Get detailed financial breakdown for a specific month and year.
        Use this for questions like "April ka total expense?" or "How much did we earn in January?"
        """
        analytics = AnalyticsService(db, organization_id)
        return await analytics.get_monthly_breakdown(month, year)

    @tool
    async def get_top_expenses_tool(limit: int = 3):
        """
        Get the top N highest value expenses.
        Use this for questions like "Top 3 expenses kaunse the?" or "Show me our biggest spends."
        """
        analytics = AnalyticsService(db, organization_id)
        return await analytics.get_top_expenses(limit)

    @tool
    async def get_client_payments_total_tool():
        """
        Get the total amount received from client payments.
        Use this for questions like "Total client payments kitne aaye?" or "How much have clients paid us?"
        """
        analytics = AnalyticsService(db, organization_id)
        return await analytics.get_total_client_payments()

    @tool
    async def create_task_tool(title: str, description: str = None, due_date: str = None, priority: str = "medium"):
        """
        Create a new task in the project management system.
        """
        return "I can't create tasks directly yet due to internal security checks, but I can see everything and tell you what's pending!" 

    @tool
    async def list_tasks_tool(status: str = None):
        """
        List tasks from the system.
        """
        from sqlalchemy import select
        from app.models.task import Task
        
        query = select(Task).where(Task.organization_id == organization_id)
        if status:
            query = query.where(Task.status == status)
        
        result = await db.execute(query.limit(10))
        tasks = result.scalars().all()
        
        if not tasks:
            return "No tasks found."
            
        return "\n".join([f"- {t.title} ({t.status}, Due: {t.due_date})" for t in tasks])

    return [
        get_financial_summary_tool, 
        list_tasks_tool, 
        get_monthly_breakdown_tool, 
        get_top_expenses_tool, 
        get_client_payments_total_tool
    ]
