"""Mood repository for database operations."""

import logging
from datetime import datetime
from typing import List, Optional

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class MoodRepository(BaseRepository):
    """Repository for mood data access."""
    
    def __init__(self):
        super().__init__("mood_entries")
    
    async def get_by_user_and_period(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Get mood entries for user within date range.
        
        Args:
            user_id: User ID
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of mood entries
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .order("created_at", desc=True)
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get by user and period failed: {e}")
            return []
    
    async def get_recent_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[dict]:
        """Get recent mood entries for user.
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
            
        Returns:
            List of mood entries
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get recent by user failed: {e}")
            return []


def get_mood_repository() -> MoodRepository:
    """Get mood repository instance."""
    return MoodRepository()
