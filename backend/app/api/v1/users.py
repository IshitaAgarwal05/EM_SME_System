"""
User management API endpoints.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, ManagerUser, check_organization_access
from app.models.user import User
from app.models.task import Task, TaskAssignment
from app.models.meeting import Meeting, MeetingParticipant
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.core.security import get_password_hash

logger = structlog.get_logger()

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    role: str | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
) -> PaginatedResponse[UserResponse]:
    """
    List users in the current organization.

    Supports pagination and filtering by role and active status.
    """
    # Build query
    query = select(User).where(User.organization_id == current_user.organization_id)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return PaginatedResponse.create(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
) -> UserResponse:
    """
    Create a new user in the organization.
    Requires manager role or higher.
    """
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        organization_id=current_user.organization_id,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="viewer", # Default role for added users, can be updated
        branch=user_data.branch,
        position=user_data.position,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_created_by_manager", user_id=str(user.id), creator_id=str(current_user.id))

    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: CurrentUser) -> UserResponse:
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> UserResponse:
    """
    Get user by ID.

    User must be in the same organization.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check organization access
    check_organization_access(user.organization_id, current_user)

    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> UserResponse:
    """Update current user's profile."""
    # Update fields
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    if update_data.preferences is not None:
        current_user.preferences = update_data.preferences

    await db.commit()
    await db.refresh(current_user)

    logger.info("user_profile_updated", user_id=str(current_user.id))

    return UserResponse.model_validate(current_user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
) -> UserResponse:
    """
    Update user by ID.

    Requires manager role or higher.
    User must be in the same organization.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check organization access
    check_organization_access(user.organization_id, current_user)

    # Update fields
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.phone is not None:
        user.phone = update_data.phone
    if update_data.preferences is not None:
        user.preferences = update_data.preferences
    if update_data.branch is not None:
        user.branch = update_data.branch
    if update_data.position is not None:
        user.position = update_data.position
    if update_data.role is not None:
        user.role = update_data.role

    await db.commit()
    await db.refresh(user)

    logger.info(
        "user_updated",
        user_id=str(user.id),
        updated_by=str(current_user.id),
    )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
) -> None:
    """
    Deactivate user (soft delete).

    Requires manager role or higher.
    User must be in the same organization.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check organization access
    check_organization_access(user.organization_id, current_user)

    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    # Soft delete
    user.is_active = False
    await db.commit()

    logger.info(
        "user_deactivated",
        user_id=str(user.id),
        deactivated_by=str(current_user.id),
    )

@router.get("/{user_id}/details")
async def get_user_details(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Get detailed info about a user: tasks and meetings."""
    # Check if user exists and belongs to same org
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    check_organization_access(user.organization_id, current_user)

    # Get assigned tasks
    task_query = select(Task).join(TaskAssignment).where(TaskAssignment.user_id == user_id)
    task_res = await db.execute(task_query)
    tasks = task_res.scalars().all()

    # Get scheduled meetings
    meeting_query = select(Meeting).join(MeetingParticipant).where(MeetingParticipant.user_id == user_id)
    meeting_res = await db.execute(meeting_query)
    meetings = meeting_res.scalars().all()

    return {
        "user": UserResponse.model_validate(user),
        "tasks": tasks,
        "meetings": meetings
    }
