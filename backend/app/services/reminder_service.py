"""Service for managing task reminders."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID

from app.repositories.task import get_task_repository
from app.repositories.user import get_user_repository

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for checking and sending task reminders."""
    
    def __init__(self):
        self.task_repo = get_task_repository()
        self.user_repo = get_user_repository()
    
    async def check_reminders(self) -> List[Dict]:
        """Check for tasks needing reminders and return them.
        
        Returns:
            List of tasks that need reminders with user info
        """
        try:
            now = datetime.utcnow()
            reminders_to_send = []
            
            # Get tasks with upcoming deadlines
            tasks = await self.task_repo.get_tasks_needing_reminders()
            
            logger.info(f"Checking {len(tasks)} tasks for reminders")
            
            for task in tasks:
                reminder_info = self._should_send_reminder(task, now)
                
                if reminder_info:
                    # Get user info
                    user = await self.user_repo.get_by_id(task["user_id"])
                    
                    if user and user.get("telegram_id"):
                        reminders_to_send.append({
                            "task": task,
                            "user": user,
                            "reminder_type": reminder_info["type"]
                        })
                        
                        # Update last reminder sent
                        await self.task_repo.update_last_reminder_sent(
                            task_id=task["id"],
                            sent_at=now
                        )
            
            logger.info(f"Found {len(reminders_to_send)} reminders to send")
            return reminders_to_send
            
        except Exception as e:
            logger.error(f"Error checking reminders: {e}", exc_info=True)
            return []
    
    def _should_send_reminder(
        self, 
        task: Dict, 
        now: datetime
    ) -> Optional[Dict]:
        """Determine if a reminder should be sent for this task.
        
        Args:
            task: Task dict with deadline and last_reminder_sent_at
            now: Current datetime
            
        Returns:
            Dict with reminder info or None if no reminder needed
        """
        deadline = task.get("deadline")
        if not deadline:
            return None
        
        # Skip if task is completed
        if task.get("status") == "completed":
            return None
        
        last_sent = task.get("last_reminder_sent_at")
        
        # Calculate time until deadline
        time_until = deadline - now
        minutes_until = time_until.total_seconds() / 60
        
        # Don't send if deadline has passed by more than 5 minutes
        if minutes_until < -5:
            return None
        
        # Get user's reminder preference (default 60 minutes)
        reminder_minutes = 60  # TODO: Get from user_settings
        
        # Check if we should send "before" reminder
        if reminder_minutes <= minutes_until <= (reminder_minutes + 5):
            # Only send if we haven't sent recently
            if not last_sent or (now - last_sent).total_seconds() > 3600:
                return {"type": "before", "minutes": reminder_minutes}
        
        # Check if we should send "deadline" reminder
        if -5 <= minutes_until <= 5:
            # Only send if we haven't sent in last 10 minutes
            if not last_sent or (now - last_sent).total_seconds() > 600:
                return {"type": "deadline"}
        
        return None
    
    async def get_daily_summary_data(self, user_id: UUID) -> Optional[Dict]:
        """Get data for daily summary for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dict with summary data or None if no tasks
        """
        try:
            # Get today's tasks
            today_tasks = await self.task_repo.get_user_tasks_for_today(user_id)
            
            # Get overdue tasks
            overdue_tasks = await self.task_repo.get_overdue_tasks(user_id)
            
            # Get yesterday's completed count
            completed_yesterday = await self.task_repo.get_completed_yesterday_count(user_id)
            
            # Don't send summary if no tasks
            if not today_tasks and not overdue_tasks:
                return None
            
            return {
                "today_tasks": today_tasks,
                "overdue_tasks": overdue_tasks,
                "completed_yesterday": completed_yesterday
            }
            
        except Exception as e:
            logger.error(f"Error getting daily summary for user {user_id}: {e}", exc_info=True)
            return None
    
    async def get_all_users_for_summary(self) -> List[Dict]:
        """Get all users who should receive daily summary.
        
        Returns:
            List of user dicts with telegram_id
        """
        try:
            # TODO: Filter by user_settings.reminders_enabled
            users = await self.user_repo.get_all_with_telegram()
            return users
        except Exception as e:
            logger.error(f"Error getting users for summary: {e}", exc_info=True)
            return []


# Singleton instance
_reminder_service = None


def get_reminder_service() -> ReminderService:
    """Get or create ReminderService singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service
