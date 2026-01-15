import pytest
from datetime import date, timedelta
from app.models.task import Task
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate

@pytest.mark.asyncio
async def test_create_task(db_session, test_user):
    """Test task creation logic."""
    service = TaskService(db_session)
    task_in = TaskCreate(
        title="Test Task",
        description="Verify this works",
        priority="high",
        due_date=date.today() + timedelta(days=5)
    )
    
    task = await service.create_task(task_in, test_user)
    assert task.title == "Test Task"
    assert task.organization_id == test_user.organization_id
    assert task.status == "pending"

@pytest.mark.asyncio
async def test_list_tasks(db_session, test_user):
    """Test task listing."""
    service = TaskService(db_session)
    tasks = await service.get_tasks(test_user.organization_id)
    assert isinstance(tasks, list)
