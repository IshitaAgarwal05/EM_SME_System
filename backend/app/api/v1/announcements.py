
from typing import Annotated
from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, ManagerUser
from app.models.system import Announcement
from app.schemas.system import AnnouncementCreate, AnnouncementResponse
from app.schemas.common import PaginatedResponse, PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/announcements", tags=["Announcements"])

@router.get("", response_model=list[AnnouncementResponse])
async def list_announcements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """List announcements for the organization."""
    query = select(Announcement).where(
        Announcement.organization_id == current_user.organization_id
    ).order_by(Announcement.created_at.desc())
    
    result = await db.execute(query)
    announcements = result.scalars().all()
    return announcements

@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement_data: AnnouncementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """
    Create a new announcement.
    Requires manager role or higher.
    """
    announcement = Announcement(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        title=announcement_data.title,
        content=announcement_data.content,
        target_role=announcement_data.target_role,
    )
    
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    
    logger.info("announcement_created", id=str(announcement.id), by=str(current_user.id))
    
    return announcement
