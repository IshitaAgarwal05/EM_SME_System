"""
Task management Pydantic schemas.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None
    start_date: date | None = None
    tags: list[str] | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    contractor_id: UUID | None = None
    transaction_id: UUID | None = None
    target_role: str | None = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    parent_task_id: UUID | None = None
    assigned_user_ids: list[UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: str | None = Field(
        default=None,
        pattern="^(pending|in_progress|review|completed|cancelled|on_hold)$",
    )
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None
    start_date: date | None = None
    completed_at: datetime | None = None
    tags: list[str] | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    actual_hours: float | None = Field(default=None, ge=0)
    contractor_id: UUID | None = None
    transaction_id: UUID | None = None
    target_role: str | None = None


class TaskAssignmentResponse(BaseModel):
    """Schema for task assignment."""

    id: UUID
    user_id: UUID
    assigned_by: UUID
    assigned_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(TaskBase, TimestampSchema):
    """Schema for task response."""

    id: UUID
    organization_id: UUID
    status: str
    created_by: UUID
    parent_task_id: UUID | None
    actual_hours: float | None
    completed_at: datetime | None
    contractor_id: UUID | None
    transaction_id: UUID | None
    target_role: str | None
    assignments: list[TaskAssignmentResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TaskAssignRequest(BaseModel):
    """Schema for assigning users to a task."""

    user_ids: list[UUID] = Field(min_length=1)


class TaskCommentCreate(BaseModel):
    """Schema for creating a task comment."""

    comment: str = Field(min_length=1)


class TaskCommentResponse(TimestampSchema):
    """Schema for task comment response."""

    id: UUID
    task_id: UUID
    user_id: UUID
    comment: str

    class Config:
        from_attributes = True
