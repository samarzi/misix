"""Task repository for database operations."""

import logging
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta

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
    
    async def get_tasks_needing_reminders(self) -> List[Dict]:
        """Get tasks that need reminders sent.
        
        Returns tasks with deadlines in the next 2 hours that are not completed.
        
        Returns:
            List of task dicts
        """
        try:
            supabase = self._get_client()
            
            # Get tasks with deadlines in next 2 hours
            now = datetime.utcnow()
            future = now + timedelta(hours=2)
            
            result = (
                supabase.table(self.table_name)
                .select("*")
                .neq("status", "completed")
                .not_.is_("deadline", "null")
                .gte("deadline", now.isoformat())
                .lte("deadline", future.isoformat())
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get tasks needing reminders failed: {e}")
            return []
    
    async def update_last_reminder_sent(
        self,
        task_id: str | UUID,
        sent_at: datetime
    ) -> bool:
        """Update last reminder sent timestamp.
        
        Args:
            task_id: Task ID
            sent_at: Timestamp when reminder was sent
            
        Returns:
            True if successful
        """
        try:
            supabase = self._get_client()
            
            supabase.table(self.table_name).update({
                "last_reminder_sent_at": sent_at.isoformat()
            }).eq("id", str(task_id)).execute()
            
            return True
        except Exception as e:
            logger.error(f"Update last reminder sent failed: {e}")
            return False
    
    async def get_user_tasks_for_today(self, user_id: str | UUID) -> List[Dict]:
        """Get user's tasks for today.
        
        Args:
            user_id: User ID
            
        Returns:
            List of tasks with deadline today
        """
        try:
            supabase = self._get_client()
            
            # Get today's date range
            today = datetime.utcnow().date()
            start = datetime.combine(today, datetime.min.time())
            end = datetime.combine(today, datetime.max.time())
            
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .neq("status", "completed")
                .gte("deadline", start.isoformat())
                .lte("deadline", end.isoformat())
                .order("deadline")
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get user tasks for today failed: {e}")
            return []
    
    async def get_overdue_tasks(self, user_id: str | UUID) -> List[Dict]:
        """Get user's overdue tasks.
        
        Args:
            user_id: User ID
            
        Returns:
            List of overdue tasks
        """
        try:
            supabase = self._get_client()
            
            now = datetime.utcnow()
            
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .neq("status", "completed")
                .not_.is_("deadline", "null")
                .lt("deadline", now.isoformat())
                .order("deadline")
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get overdue tasks failed: {e}")
            return []
    
    async def get_completed_yesterday_count(self, user_id: str | UUID) -> int:
        """Get count of tasks completed yesterday.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of completed tasks
        """
        try:
            supabase = self._get_client()
            
            # Get yesterday's date range
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            start = datetime.combine(yesterday, datetime.min.time())
            end = datetime.combine(yesterday, datetime.max.time())
            
            result = (
                supabase.table(self.table_name)
                .select("id", count="exact")
                .eq("user_id", str(user_id))
                .eq("status", "completed")
                .gte("updated_at", start.isoformat())
                .lte("updated_at", end.isoformat())
                .execute()
            )
            
            return result.count or 0
        except Exception as e:
            logger.error(f"Get completed yesterday count failed: {e}")
            return 0


def get_task_repository() -> TaskRepository:
    """Get task repository instance."""
    return TaskRepository()
