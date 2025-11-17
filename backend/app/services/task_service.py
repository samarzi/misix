"""Task service for business logic."""

import logging
from typing import Optional
from uuid import UUID

from app.core.exceptions import NotFoundError, AuthorizationError
from app.models.common import PaginationParams
from app.models.task import CreateTaskRequest, UpdateTaskRequest, TaskFilters
from app.repositories.task import TaskRepository, get_task_repository

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task management business logic."""
    
    def __init__(self, task_repo: Optional[TaskRepository] = None):
        """Initialize task service.
        
        Args:
            task_repo: Task repository (injected for testing)
        """
        self.task_repo = task_repo or get_task_repository()
    
    async def create_task(
        self,
        user_id: str,
        task_data: CreateTaskRequest,
    ) -> dict:
        """Create a new task.
        
        Args:
            user_id: User ID creating the task
            task_data: Task data
            
        Returns:
            Created task
        """
        data = {
            "user_id": user_id,
            **task_data.model_dump(exclude_none=True),
        }
        
        # Convert datetime to ISO string
        if "deadline" in data and data["deadline"]:
            data["deadline"] = data["deadline"].isoformat()
        
        task = await self.task_repo.create(data)
        logger.info(f"Task created: {task['id']} by user {user_id}")
        
        return task
    
    async def get_task(self, task_id: str, user_id: str) -> dict:
        """Get task by ID.
        
        Args:
            task_id: Task ID
            user_id: User ID requesting the task
            
        Returns:
            Task data
            
        Raises:
            NotFoundError: If task not found
            AuthorizationError: If user doesn't own the task
        """
        task = await self.task_repo.get_by_id(task_id)
        
        if not task:
            raise NotFoundError("Task", task_id)
        
        # Verify ownership
        if task["user_id"] != user_id:
            raise AuthorizationError("You don't have permission to access this task")
        
        return task
    
    async def get_user_tasks(
        self,
        user_id: str,
        filters: Optional[TaskFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> tuple[list[dict], int]:
        """Get user's tasks with filtering and pagination.
        
        Args:
            user_id: User ID
            filters: Optional filters
            pagination: Optional pagination params
            
        Returns:
            Tuple of (tasks, total_count)
        """
        pagination = pagination or PaginationParams()
        
        # Get tasks with filters
        tasks = await self.task_repo.get_by_user_id_with_filters(
            user_id=user_id,
            filters=filters,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        
        # Get total count
        total = await self.task_repo.count_by_user_id_with_filters(
            user_id=user_id,
            filters=filters,
        )
        
        return tasks, total
    
    async def update_task(
        self,
        task_id: str,
        user_id: str,
        task_data: UpdateTaskRequest,
    ) -> dict:
        """Update a task.
        
        Args:
            task_id: Task ID
            user_id: User ID updating the task
            task_data: Updated task data
            
        Returns:
            Updated task
            
        Raises:
            NotFoundError: If task not found
            AuthorizationError: If user doesn't own the task
        """
        # Verify ownership
        await self.get_task(task_id, user_id)
        
        # Prepare update data
        data = task_data.model_dump(exclude_none=True)
        
        # Convert datetime to ISO string
        if "deadline" in data and data["deadline"]:
            data["deadline"] = data["deadline"].isoformat()
        
        task = await self.task_repo.update(task_id, data)
        logger.info(f"Task updated: {task_id} by user {user_id}")
        
        return task
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID
            user_id: User ID deleting the task
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If task not found
            AuthorizationError: If user doesn't own the task
        """
        # Verify ownership
        await self.get_task(task_id, user_id)
        
        result = await self.task_repo.delete(task_id)
        logger.info(f"Task deleted: {task_id} by user {user_id}")
        
        return result
    
    async def mark_completed(self, task_id: str, user_id: str) -> dict:
        """Mark task as completed.
        
        Args:
            task_id: Task ID
            user_id: User ID
            
        Returns:
            Updated task
        """
        return await self.update_task(
            task_id,
            user_id,
            UpdateTaskRequest(status="completed"),
        )
    
    async def get_task_statistics(self, user_id: str) -> dict:
        """Get task statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        total = await self.task_repo.count_by_user_id(user_id)
        completed = await self.task_repo.count_by_user_id_with_filters(
            user_id,
            TaskFilters(status="completed"),
        )
        in_progress = await self.task_repo.count_by_user_id_with_filters(
            user_id,
            TaskFilters(status="in_progress"),
        )
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "open": total - completed,
        }


def get_task_service() -> TaskService:
    """Get task service instance."""
    return TaskService()
