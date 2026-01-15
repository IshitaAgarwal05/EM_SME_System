import pytest
from httpx import AsyncClient
from datetime import date, timedelta

@pytest.mark.asyncio
async def test_complete_business_workflow(client: AsyncClient):
    """
    Integration test for Phase 8:
    Complete workflow: Register -> Login -> Create Task -> List Tasks
    """
    # 1. Register
    reg_payload = {
        "email": "workflow@example.com",
        "password": "StrongPassword123!",
        "full_name": "Workflow User",
        "organization_name": "Workflow Org"
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    
    # 2. Login
    login_res = await client.post("/api/v1/auth/login", json={
        "email": reg_payload["email"],
        "password": reg_payload["password"]
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Task
    task_payload = {
        "title": "Integration Task",
        "description": "Test the full flow",
        "priority": "high",
        "due_date": str(date.today() + timedelta(days=1))
    }
    task_res = await client.post("/api/v1/tasks", json=task_payload, headers=headers)
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]
    
    # 4. List Tasks
    list_res = await client.get("/api/v1/tasks", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert any(t["id"] == task_id for t in data["items"])
    
    # 5. Get Task Details
    detail_res = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Integration Task"
