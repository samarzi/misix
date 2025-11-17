"""Task repository for database operations."""

import logging
from typing import Optional
from uuid import UUID

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository):
    """Repository for task data access."""
    
    def __init__(self):
        super().__init__("tasks")
    
    async def get_by_status(
        self,
        user_id: str | UUID,
        status: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get tasks by status.
        
        Args:
            user_id: User ID
            status: Task status
            limit: Maximum number of tasks
            
        Returns:
            List of tasks
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("status", status)
                .order("created_at", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get by status failed: {e}")
            return []
    
    async def get_by_priority(
        self,
        user_id: str | UUID,
        priority: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get tasks by priority.
        
        Args:
            user_id: User ID
            priority: Task priority
            limit: Maximum number of tasks
            
        Returns:
            List of tasks
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("priority", priority)
                .order("created_at", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get by priority failed: {e}")
            return []
    
    async def get_with_filters(
        self,
        user_id: str | UUID,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[str | UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict]:
        """Get tasks with filters.
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            priority: Filter by priority (optional)
            project_id: Filter by project (optional)
            limit: Maximum number of tasks
            offset: Number of tasks to skip
            
        Returns:
            List of tasks
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
            )
            
            if status:
                query = query.eq("status", status)
            
            if priority:
                query = query.eq("priority", priority)
            
            if project_id:
                query = query.eq("project_id", str(project_id))
            
            query = query.order("created_at", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get with filters failed: {e}")
            return []


def get_task_repository() -> TaskRepository:
    """Get task repository instance."""
    return TaskRepository()
