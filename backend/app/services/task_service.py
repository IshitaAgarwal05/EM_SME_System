"""
Task service for managing tasks, assignments, and workflows.
"""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.task import Task, TaskAssignment, TaskComment
from app.models.financial import TaskPaymentLink
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate

logger = structlog.get_logger()


class TaskService:
    """Service for task management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_task(self, task_id: UUID) -> Task:
        """Get task by ID with relationships loaded."""
        query = (
            select(Task)
            .options(
                selectinload(Task.assignments),
                selectinload(Task.subtasks)
            )
            .where(Task.id == task_id)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError("Task", str(task_id))

        return task

    async def create_task(self, task_data: TaskCreate, creator: User) -> Task:
        """Create a new task."""
        # Create task
        task = Task(
            organization_id=creator.organization_id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=task_data.due_date,
            start_date=task_data.start_date,
            tags=task_data.tags,
            estimated_hours=task_data.estimated_hours,
            parent_task_id=task_data.parent_task_id,
            created_by=creator.id,
            contractor_id=task_data.contractor_id,
            transaction_id=task_data.transaction_id,
            target_role=task_data.target_role,
            status="pending"
        )
        self.db.add(task)
        await self.db.flush()  # Get ID

        # Handle assignments
        if task_data.assigned_user_ids:
            for user_id in task_data.assigned_user_ids:
                # Verify user exists and belongs to org
                user = await self.db.get(User, user_id)
                if not user or user.organization_id != creator.organization_id:
                     raise ValidationError(f"Invalid user assignment: {user_id}")
                
                assignment = TaskAssignment(
                    task_id=task.id,
                    user_id=user_id,
                    assigned_by=creator.id
                )
                self.db.add(assignment)

        await self.db.commit()
        await self.db.refresh(task)
        
        # Load relationships for response
        return await self.get_task(task.id)

    async def update_task(self, task_id: UUID, update_data: TaskUpdate, user: User) -> Task:
        """Update existing task."""
        task = await self.get_task(task_id)

        # Check access
        if task.organization_id != user.organization_id:
            raise AuthorizationError("Access denied")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(task, key, value)

        # Status transition logic
        if update_data.status == "completed" and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
        elif update_data.status and update_data.status != "completed":
            task.completed_at = None

        await self.db.commit()
        await self.db.refresh(task)

        # Sync with Transaction if linked
        if update_data.status == "completed" and task.transaction_id:
            from app.models.financial import Transaction
            transaction = await self.db.get(Transaction, task.transaction_id)
            if transaction:
                transaction.is_reconciled = True
                transaction.reconciled_at = datetime.now(timezone.utc)
                transaction.reconciled_by = user.id
                # Sync category if task has tags or title that might match
                if not transaction.category:
                    transaction.category = task.target_role or "Task Related"
                await self.db.commit()

        return task

    async def assign_users(self, task_id: UUID, user_ids: list[UUID], assigned_by: User) -> list[TaskAssignment]:
        """Assign users to a task."""
        task = await self.get_task(task_id)
        if task.organization_id != assigned_by.organization_id:
             raise AuthorizationError("Access denied")

        new_assignments = []
        for user_id in user_ids:
            # Check if already assigned
            exists = await self.db.execute(
                select(TaskAssignment).where(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.user_id == user_id
                )
            )
            if exists.scalar_one_or_none():
                continue

            assignment = TaskAssignment(
                task_id=task_id,
                user_id=user_id,
                assigned_by=assigned_by.id
            )
            self.db.add(assignment)
            new_assignments.append(assignment)

        await self.db.commit()
        return new_assignments

    async def add_comment(self, task_id: UUID, comment_text: str, user: User) -> TaskComment:
        """Add a comment to a task."""
        task = await self.get_task(task_id)
        if task.organization_id != user.organization_id:
             raise AuthorizationError("Access denied")

        comment = TaskComment(
            task_id=task_id,
            user_id=user.id,
            comment=comment_text
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
