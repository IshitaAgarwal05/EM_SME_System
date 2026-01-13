"""
Worker tasks for background processing (Reminders, etc.).
"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID

import structlog
from celery import Celery
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.system import Reminder
from app.models.user import User

logger = structlog.get_logger()

# Initialize Celery
# Note: In production, use a separate celery app config file
celery_app = Celery(
    "worker",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url)
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

@celery_app.task(name="send_due_reminders")
def check_and_send_reminders():
    """
    Periodic task to check for due reminders and send them.
    This should be scheduled by Celery Beat (e.g., every minute).
    """
    logger.info("checking_reminders")
    
    # Run async function in sync celery task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(_process_due_reminders())

async def _process_due_reminders():
    """Async logic to process reminders."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        # Find due reminders that are pending
        query = select(Reminder).where(
            Reminder.status == "pending",
            Reminder.scheduled_for <= now
        )
        result = await db.execute(query)
        reminders = result.scalars().all()
        
        logger.info("found_due_reminders", count=len(reminders))
        
        for reminder in reminders:
            try:
                # Retrieve user to send to
                user = await db.get(User, reminder.user_id) if reminder.user_id else None
                
                # Mock sending (Email/SMS/Push)
                await _send_notification(reminder, user)
                
                # Update status
                reminder.status = "sent"
                reminder.sent_at = datetime.now(timezone.utc)
                
            except Exception as e:
                logger.error("reminder_failed", id=str(reminder.id), error=str(e))
                reminder.retry_count += 1
                if reminder.retry_count >= reminder.max_retries:
                    reminder.status = "failed"
            
            await db.commit()

async def _send_notification(reminder: Reminder, user: User | None):
    """Mock notification sending."""
    contact = user.email if user else "Unknown"
    logger.info(
        "sending_notification", 
        type=reminder.reminder_type,
        to=contact,
        msg=reminder.message
    )
    # Simulate IO
    await asyncio.sleep(0.1)
