import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy import select
from app.models.financial import Transaction, BankAccount
from app.services.analytics_service import AnalyticsService

@pytest.mark.asyncio
async def test_financial_summary_empty(db_session, test_user):
    """Test summary with no data."""
    analytics = AnalyticsService(db_session, test_user.organization_id)
    today = date.today()
    summary = await analytics.get_financial_summary(today, today)
    
    assert summary["total_income"] == 0
    assert summary["total_expense"] == 0
    assert summary["net_profit"] == 0

@pytest.mark.asyncio
async def test_financial_summary_with_data(db_session, test_user):
    """Test summary with mock transactions."""
    # Create mock reconciled transaction
    txn = Transaction(
        organization_id=test_user.organization_id,
        amount=1000.0,
        transaction_type="credit",
        transaction_date=date.today(),
        description="Sale",
        is_reconciled=True
    )
    db_session.add(txn)
    await db_session.commit()
    
    analytics = AnalyticsService(db_session, test_user.organization_id)
    summary = await analytics.get_financial_summary(date.today(), date.today())
    
    assert summary["total_income"] == 1000.0
    assert summary["net_profit"] == 1000.0

@pytest.mark.asyncio
async def test_fy_summary(db_session, test_user):
    """Test FY logic (April to March)."""
    analytics = AnalyticsService(db_session, test_user.organization_id)
    # This should internally call get_financial_summary with Apr 1 to Mar 31
    summary = await analytics.get_fy_summary(2024)
    assert "period" in summary
    assert summary["period"]["start"] == date(2024, 4, 1)
    assert summary["period"]["end"] == date(2025, 3, 31)
