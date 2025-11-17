"""Note repository for database operations."""

import logging
from typing import Optional
from uuid import UUID

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class NoteRepository(BaseRepository):
    """Repository for note data access."""
    
    def __init__(self):
        super().__init__("notes")
    
    async def get_by_user_id(
        self,
        user_id: str | UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict]:
        """Get notes by user ID.
        
        Args:
            user_id: User ID
            limit: Maximum number of notes
            offset: Number of notes to skip
            
        Returns:
            List of notes
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get by user_id failed: {e}")
            return []
    
    async def search(
        self,
        user_id: str | UUID,
        search_term: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Search notes by content.
        
        Args:
            user_id: User ID
            search_term: Search term
            limit: Maximum number of notes
            
        Returns:
            List of matching notes
        """
        try:
            supabase = self._get_client()
            query = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .ilike("content", f"%{search_term}%")
                .order("created_at", desc=True)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


def get_note_repository() -> NoteRepository:
    """Get note repository instance."""
    return NoteRepository()
