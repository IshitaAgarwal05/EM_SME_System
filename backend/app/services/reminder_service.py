"""
Reminder service for scheduling and managing notifications.
"""

from datetime import datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, AuthorizationError
from app.models.system import Reminder
from app.models.user import User

logger = structlog.get_logger()


class ReminderService:
    """Service for managing reminders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reminder(
        self, 
        user: User, 
        title: str, 
        scheduled_for: datetime,
        message: str | None = None,
        reminder_type: str = "notification",
        reference_type: str | None = None,
        reference_id: UUID | None = None
    ) -> Reminder:
        """Schedule a new reminder."""
        reminder = Reminder(
            organization_id=user.organization_id,
            user_id=user.id,
            title=title,
            message=message,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            status="pending",
            reference_type=reference_type,
            reference_id=reference_id,
            channels=["in_app", "email"] # Default channels
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def get_my_reminders(self, user: User) -> list[Reminder]:
        """Get pending reminders for current user."""
        query = select(Reminder).where(
            Reminder.user_id == user.id,
            Reminder.status == "pending"
        ).order_by(Reminder.scheduled_for)
        result = await db.execute(query)
        return result.scalars().all()

    async def dismiss_reminder(self, reminder_id: UUID, user: User) -> Reminder:
        """Mark reminder as dismissed/completed."""
        reminder = await self.db.get(Reminder, reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", str(reminder_id))
            
        if reminder.user_id != user.id:
            raise AuthorizationError("Access denied")
            
        reminder.status = "dismissed"
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
