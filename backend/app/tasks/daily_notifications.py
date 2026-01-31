"""
Daily notification Celery Beat task.
Runs every morning at 9:00 AM IST (Asia/Kolkata).

Checks:
  - Invoices due today
  - Overdue receivables (past due_date, unpaid)
  - Vendor payments due today (from payments table)
  - Contractor contract expiries within 7 days

Generates Notification entries with idempotency (no duplicate per day per event).
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import structlog
from celery import Celery
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.financial import Contractor, Payment
from app.models.invoice import Invoice
from app.models.system import Notification

logger = structlog.get_logger()

celery_app = Celery(
    "worker",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# ── Beat schedule ────────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "daily-payment-notifications": {
        "task": "app.tasks.daily_notifications.run_daily_notifications",
        "schedule": {
            # crontab: 9:00 AM every day (IST = UTC+5:30 → 3:30 UTC)
            "type": "crontab",
            "minute": "30",
            "hour": "3",
        },
    },
}


@celery_app.task(name="app.tasks.daily_notifications.run_daily_notifications")
def run_daily_notifications():
    """Synchronous Celery task wrapper."""
    logger.info("daily_notifications_started")
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(_process_daily_notifications())
    logger.info("daily_notifications_completed")


async def _process_daily_notifications():
    async with AsyncSessionLocal() as db:
        today = date.today()
        created = 0

        # 1. Invoices due today
        result = await db.execute(
            select(Invoice).where(
                Invoice.due_date == today,
                Invoice.status.in_(["sent", "partial"]),
            )
        )
        for inv in result.scalars().all():
            owner_id = inv.created_by
            created += await _upsert_notification(
                db,
                org_id=inv.organization_id,
                user_id=owner_id,
                notif_type="invoice_due",
                message=f"Invoice {inv.invoice_number} ({inv.client_name}) is due today. Outstanding: ₹{float(inv.total_amount - inv.paid_amount):,.2f}",
                reference_id=inv.id,
                reference_type="invoice",
            )

        # 2. Overdue invoices (past due_date, still unpaid)
        result = await db.execute(
            select(Invoice).where(
                Invoice.due_date < today,
                Invoice.status.in_(["sent", "partial"]),
                Invoice.total_amount > Invoice.paid_amount,
            )
        )
        for inv in result.scalars().all():
            days_overdue = (today - inv.due_date).days
            created += await _upsert_notification(
                db,
                org_id=inv.organization_id,
                user_id=inv.created_by,
                notif_type="invoice_overdue",
                message=f"Invoice {inv.invoice_number} ({inv.client_name}) is {days_overdue} day(s) overdue. Outstanding: ₹{float(inv.total_amount - inv.paid_amount):,.2f}",
                reference_id=inv.id,
                reference_type="invoice",
            )

        # 3. Vendor payments due today
        result = await db.execute(
            select(Payment).where(
                Payment.due_date == today,
                Payment.status.in_(["pending", "processing"]),
            )
        )
        for pay in result.scalars().all():
            created += await _upsert_notification(
                db,
                org_id=pay.organization_id,
                user_id=pay.paid_by,
                notif_type="vendor_payment_due",
                message=f"Vendor payment of ₹{float(pay.amount):,.2f} is due today.",
                reference_id=pay.id,
                reference_type="payment",
            )

        # 4. Contract expiries within 7 days
        expiry_threshold = today + timedelta(days=7)
        result = await db.execute(
            select(Contractor).where(
                Contractor.contract_end_date <= expiry_threshold,
                Contractor.contract_end_date >= today,
                Contractor.is_active == True,
            )
        )
        for contractor in result.scalars().all():
            days_left = (contractor.contract_end_date - today).days
            created += await _upsert_notification(
                db,
                org_id=contractor.organization_id,
                user_id=contractor.user_id,
                notif_type="contract_expiry",
                message=f"Contract with {contractor.name} expires in {days_left} day(s) (on {contractor.contract_end_date}).",
                reference_id=contractor.id,
                reference_type="contractor",
            )

        await db.commit()
        logger.info("daily_notifications_created", count=created)


async def _upsert_notification(
    db,
    org_id,
    user_id,
    notif_type: str,
    message: str,
    reference_id,
    reference_type: str,
) -> int:
    """
    Insert-or-ignore a notification.  The unique constraint on
    (org, type, reference_id, date) ensures idempotency.
    Returns 1 if inserted, 0 if already existed.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    today_dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        stmt = pg_insert(Notification).values(
            organization_id=org_id,
            user_id=user_id,
            notification_type=notif_type,
            message=message,
            reference_id=reference_id,
            reference_type=reference_type,
            notification_date=today_dt,
        ).on_conflict_do_nothing(
            constraint="uq_notifications_idempotency"
        )
        result = await db.execute(stmt)
        return result.rowcount
    except Exception as e:
        logger.warning("notification_upsert_failed", error=str(e), type=notif_type)
        return 0
