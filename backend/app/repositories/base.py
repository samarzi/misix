"""Base repository with common CRUD operations."""

import logging
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from app.core.exceptions import DatabaseError, NotFoundError
from app.shared.supabase import get_supabase_client, supabase_available

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations.
    
    Provides standard database operations that can be inherited by
    specific repositories.
    """
    
    def __init__(self, table_name: str):
        """Initialize repository.
        
        Args:
            table_name: Name of the database table
        """
        self.table_name = table_name
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Ensure Supabase is available."""
        if not supabase_available():
            raise DatabaseError("Database connection not available")
    
    def _get_client(self):
        """Get Supabase client."""
        return get_supabase_client()
    
    async def create(self, data: dict[str, Any]) -> dict:
        """Create a new record.
        
        Args:
            data: Record data
            
        Returns:
            Created record
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            supabase = self._get_client()
            result = supabase.table(self.table_name).insert(data).execute()
            
            if not result.data:
                raise DatabaseError(f"Failed to create {self.table_name} record")
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Create failed in {self.table_name}: {e}")
            raise DatabaseError(f"Failed to create {self.table_name}: {str(e)}")
    
    async def get_by_id(self, record_id: str | UUID) -> Optional[dict]:
        """Get record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            Record data or None if not found
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("id", str(record_id))
                .execute()
            )
            
            if not result.data:
                return None
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Get by ID failed in {self.table_name}: {e}")
            return None
    
    async def get_by_user_id(
        self,
        user_id: str | UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[dict]:
        """Get records by user ID.
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of records
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
            logger.error(f"Get by user ID failed in {self.table_name}: {e}")
            return []
    
    async def update(self, record_id: str | UUID, data: dict[str, Any]) -> dict:
        """Update a record.
        
        Args:
            record_id: Record ID
            data: Updated data
            
        Returns:
            Updated record
            
        Raises:
            NotFoundError: If record not found
            DatabaseError: If update fails
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .update(data)
                .eq("id", str(record_id))
                .execute()
            )
            
            if not result.data:
                raise NotFoundError(self.table_name, str(record_id))
            
            return result.data[0]
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Update failed in {self.table_name}: {e}")
            raise DatabaseError(f"Failed to update {self.table_name}: {str(e)}")
    
    async def delete(self, record_id: str | UUID) -> bool:
        """Delete a record.
        
        Args:
            record_id: Record ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If record not found
            DatabaseError: If deletion fails
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .delete()
                .eq("id", str(record_id))
                .execute()
            )
            
            if not result.data:
                raise NotFoundError(self.table_name, str(record_id))
            
            return True
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Delete failed in {self.table_name}: {e}")
            raise DatabaseError(f"Failed to delete {self.table_name}: {str(e)}")
    
    async def count_by_user_id(self, user_id: str | UUID) -> int:
        """Count records for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of records
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("id", count="exact")
                .eq("user_id", str(user_id))
                .execute()
            )
            
            return result.count or 0
        except Exception as e:
            logger.error(f"Count failed in {self.table_name}: {e}")
            return 0
    
    async def exists(self, record_id: str | UUID) -> bool:
        """Check if record exists.
        
        Args:
            record_id: Record ID
            
        Returns:
            True if record exists
        """
        record = await self.get_by_id(record_id)
        return record is not None
