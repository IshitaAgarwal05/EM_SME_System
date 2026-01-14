"""
Task management API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, check_organization_access
from app.services.task_service import TaskService
from app.schemas.task import (
    TaskCreate, 
    TaskUpdate, 
    TaskResponse, 
    TaskAssignRequest,
    TaskCommentCreate,
    TaskCommentResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.models.task import Task
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Create a new task."""
    service = TaskService(db)
    try:
        return await service.create_task(task_data, current_user)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Depends()],
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assignee_id: UUID | None = Query(None),
):
    """List tasks with filtering."""
    query = select(Task).where(Task.organization_id == current_user.organization_id)
    
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if assignee_id:
        query = query.where(Task.assignments.any(user_id=assignee_id))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    # We need to load relationships for schema validation to work fully or use explicit loading
    # Ideally TaskService should handle listing to reuse loading logic, but for simplicity here:
    service = TaskService(db)
    # Re-fetch with relationships (n+1 optimization needed in real prod, but simple here)
    items = [await service.get_task(t.id) for t in tasks]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Get task details."""
    service = TaskService(db)
    try:
        task = await service.get_task(task_id)
        check_organization_access(task.organization_id, current_user)
        return task
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Update a task."""
    service = TaskService(db)
    try:
        return await service.update_task(task_id, update_data, current_user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/assign", status_code=status.HTTP_200_OK)
async def assign_users(
    task_id: UUID,
    assign_req: TaskAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Assign users to task."""
    service = TaskService(db)
    try:
        await service.assign_users(task_id, assign_req.user_ids, current_user)
        return await service.get_task(task_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/comments", response_model=TaskCommentResponse)
async def add_comment(
    task_id: UUID,
    comment_data: TaskCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Add a comment."""
    service = TaskService(db)
    try:
        return await service.add_comment(task_id, comment_data.comment, current_user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
