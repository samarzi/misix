from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.shared.config import settings
from app.shared.supabase import get_supabase_client
from app.web.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_TASK_STATUSES = {"new", "in_progress", "waiting", "completed", "cancelled"}
VALID_TASK_PRIORITIES = {"low", "medium", "high", "critical"}

# Pydantic models
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "new"
    deadline: Optional[str] = None
    estimated_hours: Optional[float] = None
    project_id: Optional[str] = None

class TaskCreate(TaskBase):
    pass


class TaskCreatePublic(TaskBase):
    user_id: str

class Task(TaskBase):
    id: str
    user_id: str
    parent_task_id: Optional[str] = None
    actual_hours: Optional[float] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    project_id: Optional[str] = None

@router.get("/tasks", response_model=List[Task])
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status: new, in_progress, waiting, completed"),
    priority: Optional[str] = Query(None, description="Filter by priority: low, medium, high, critical"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """Get user's tasks with optional filters and pagination."""
    try:
        supabase = get_supabase_client()

        query = supabase.table("tasks").select("*").eq("user_id", user_id)

        if status:
            if status not in VALID_TASK_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid status value")
            query = query.eq("status", status)

        if priority:
            if priority not in VALID_TASK_PRIORITIES:
                raise HTTPException(status_code=400, detail="Invalid priority value")
            query = query.eq("priority", priority)

        if project_id:
            query = query.eq("project_id", project_id)

        query = query.order("created_at", desc=True).range(skip, skip + limit - 1)

        response = query.execute()

        return [Task(**task) for task in response.data]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")

def _build_task_payload(user_id: str, task: TaskBase) -> dict:
    status = task.status or "new"
    priority = task.priority or "medium"

    if status not in VALID_TASK_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status value")
    if priority not in VALID_TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority value")

    payload = {
        "user_id": user_id,
        "title": task.title,
        "description": task.description,
        "priority": priority,
        "status": status,
    }

    if task.deadline:
        payload["deadline"] = task.deadline
    if task.estimated_hours is not None:
        payload["estimated_hours"] = task.estimated_hours
    if task.project_id:
        payload["project_id"] = task.project_id

    return payload


def _insert_task(payload: dict) -> Task:
    supabase = get_supabase_client()
    response = supabase.table("tasks").insert(payload).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create task")

    return Task(**response.data[0])


@router.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new task."""
    try:
        payload = _build_task_payload(user_id, task)
        return _insert_task(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.post("/tasks/public", response_model=Task)
async def create_task_public(task: TaskCreatePublic):
    """Create a task when only user_id is available (no auth token)."""
    try:
        payload = _build_task_payload(task.user_id, task)
        return _insert_task(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating public task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific task by ID."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("tasks").select("*").eq("id", task_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return Task(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")

@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update a task."""
    try:
        supabase = get_supabase_client()

        update_data = {}
        if task_update.title is not None:
            update_data["title"] = task_update.title
        if task_update.description is not None:
            update_data["description"] = task_update.description
        if task_update.priority is not None:
            if task_update.priority not in ["low", "medium", "high", "critical"]:
                raise HTTPException(status_code=400, detail="Invalid priority value")
            update_data["priority"] = task_update.priority
        if task_update.status is not None:
            if task_update.status not in ["new", "in_progress", "waiting", "completed", "cancelled"]:
                raise HTTPException(status_code=400, detail="Invalid status value")
            update_data["status"] = task_update.status
        if task_update.deadline is not None:
            update_data["deadline"] = task_update.deadline
        if task_update.estimated_hours is not None:
            update_data["estimated_hours"] = task_update.estimated_hours
        if task_update.actual_hours is not None:
            update_data["actual_hours"] = task_update.actual_hours
        if task_update.project_id is not None:
            update_data["project_id"] = task_update.project_id

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = supabase.table("tasks").update(update_data).eq("id", task_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return Task(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a task."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    user_id: str = Depends(get_current_user_id)
):
    """Quick status update for Kanban board drag & drop."""
    try:
        if status not in ["new", "in_progress", "waiting", "completed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Invalid status value")

        supabase = get_supabase_client()

        response = supabase.table("tasks").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", task_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Status updated successfully", "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")
