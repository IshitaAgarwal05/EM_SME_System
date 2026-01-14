"""
Reminder API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser
from app.services.reminder_service import ReminderService
from app.schemas.system import ReminderCreate, ReminderResponse
from app.models.system import Reminder

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Schedule a personal reminder."""
    service = ReminderService(db)
    return await service.create_reminder(
        user=current_user,
        title=data.title,
        message=data.message,
        scheduled_for=data.scheduled_for,
        reminder_type=data.reminder_type
    )

@router.get("", response_model=list[ReminderResponse])
async def list_my_reminders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """List my pending reminders."""
    query = select(Reminder).where(
        Reminder.user_id == current_user.id,
        Reminder.status == "pending"
    ).order_by(Reminder.scheduled_for)
    
    result = await db.execute(query)
    reminders = result.scalars().all()
    
    return [ReminderResponse.model_validate(r) for r in reminders]

@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
async def dismiss_reminder(
    reminder_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Dismiss a reminder."""
    service = ReminderService(db)
    return await service.dismiss_reminder(reminder_id, current_user)
