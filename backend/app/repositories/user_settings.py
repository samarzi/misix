"""User settings repository for reminder preferences."""

import logging
from typing import Optional, Dict, List
from uuid import UUID
from datetime import time

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserSettingsRepository(BaseRepository):
    """Repository for user settings data access."""
    
    def __init__(self):
        super().__init__("user_settings")
    
    async def get_settings(self, user_id: str | UUID) -> Dict:
        """Get user settings with defaults if not exists.
        
        Args:
            user_id: User ID
            
        Returns:
            User settings dict with defaults
        """
        try:
            supabase = self._get_client()
            
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )
            
            if result.data:
                return result.data[0]
            
            # Return defaults if not found
            return {
                "user_id": str(user_id),
                "reminders_enabled": True,
                "daily_summary_time": "09:00",
                "reminder_minutes_before": 60
            }
        except Exception as e:
            logger.error(f"Get settings failed: {e}")
            # Return defaults on error
            return {
                "user_id": str(user_id),
                "reminders_enabled": True,
                "daily_summary_time": "09:00",
                "reminder_minutes_before": 60
            }
    
    async def update_settings(
        self,
        user_id: str | UUID,
        reminders_enabled: Optional[bool] = None,
        daily_summary_time: Optional[str] = None,
        reminder_minutes_before: Optional[int] = None
    ) -> bool:
        """Update user settings.
        
        Args:
            user_id: User ID
            reminders_enabled: Enable/disable reminders
            daily_summary_time: Time for daily summary (HH:MM format)
            reminder_minutes_before: Minutes before deadline to remind
            
        Returns:
            True if successful
        """
        try:
            supabase = self._get_client()
            
            # Build update dict
            updates = {}
            if reminders_enabled is not None:
                updates["reminders_enabled"] = reminders_enabled
            if daily_summary_time is not None:
                updates["daily_summary_time"] = daily_summary_time
            if reminder_minutes_before is not None:
                updates["reminder_minutes_before"] = reminder_minutes_before
            
            if not updates:
                return True
            
            # Try to update first
            result = (
                supabase.table(self.table_name)
                .update(updates)
                .eq("user_id", str(user_id))
                .execute()
            )
            
            # If no rows updated, insert new record
            if not result.data:
                updates["user_id"] = str(user_id)
                supabase.table(self.table_name).insert(updates).execute()
            
            return True
        except Exception as e:
            logger.error(f"Update settings failed: {e}")
            return False
    
    async def get_all_users_with_reminders_enabled(self) -> List[Dict]:
        """Get all users with reminders enabled.
        
        Returns:
            List of user_settings dicts
        """
        try:
            supabase = self._get_client()
            
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("reminders_enabled", True)
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get users with reminders enabled failed: {e}")
            return []


def get_user_settings_repository() -> UserSettingsRepository:
    """Get user settings repository instance."""
    return UserSettingsRepository()
