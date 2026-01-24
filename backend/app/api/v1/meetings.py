"""
Meeting management API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, check_organization_access
from app.services.meeting_service import MeetingService
from app.schemas.meeting import MeetingCreate, MeetingUpdate, MeetingResponse
from app.models.meeting import Meeting

router = APIRouter(prefix="/meetings", tags=["Meetings"])

@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Schedule a new meeting."""
    service = MeetingService(db)
    return await service.create_meeting(data, current_user)

@router.get("", response_model=dict[str, list[MeetingResponse]])
async def list_meetings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    view_all: bool = Query(False, description="Owner/Manager: see all org meetings"),
):
    """List meetings. With view_all=true (owner/manager only), returns all org meetings."""
    from sqlalchemy.orm import selectinload

    # Roles that can use view_all
    elevated_roles = {"owner", "admin", "manager"}
    can_view_all = view_all and current_user.role in elevated_roles

    query = (
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.organization_id == current_user.organization_id)
        .order_by(Meeting.start_time)
    )

    result = await db.execute(query)
    meetings = result.scalars().all()

    if not can_view_all:
        # Filter to meetings where current user is organizer or participant
        user_id_str = str(current_user.id)
        meetings = [
            m for m in meetings
            if str(m.organizer_id) == user_id_str
            or any(str(p.id) == user_id_str for p in (m.participants or []))
        ]

    return {"items": [MeetingResponse.model_validate(m) for m in meetings]}

@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = MeetingService(db)
    meeting = await service.get_meeting(meeting_id)
    check_organization_access(meeting.organization_id, current_user)
    return meeting

@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    data: MeetingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = MeetingService(db)
    return await service.update_meeting(meeting_id, data, current_user)

@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_meeting(
    meeting_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = MeetingService(db)
    await service.delete_meeting(meeting_id, current_user)
