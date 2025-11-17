"""User repository for database operations."""

import logging
from typing import Optional
from uuid import UUID

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user data access."""
    
    def __init__(self):
        super().__init__("users")
    
    async def get_by_email(self, email: str) -> Optional[dict]:
        """Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            User data or None if not found
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("email", email)
                .execute()
            )
            
            if not result.data:
                return None
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Get by email failed: {e}")
            return None
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User data or None if not found
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("telegram_id", telegram_id)
                .execute()
            )
            
            if not result.data:
                return None
            
            return result.data[0]
        except Exception as e:
            logger.error(f"Get by telegram_id failed: {e}")
            return None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
        """
        user = await self.get_by_email(email)
        return user is not None
    
    async def update_password(self, user_id: str | UUID, password_hash: str) -> dict:
        """Update user's password hash.
        
        Args:
            user_id: User ID
            password_hash: New password hash
            
        Returns:
            Updated user data
        """
        return await self.update(user_id, {"password_hash": password_hash})
    
    async def verify_email(self, user_id: str | UUID) -> dict:
        """Mark user's email as verified.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user data
        """
        return await self.update(user_id, {"email_verified": True})
    
    async def get_or_create_by_telegram_id(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> dict:
        """Get existing user or create new one by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            username: Optional Telegram username
            first_name: Optional first name
            last_name: Optional last name
            
        Returns:
            User data (existing or newly created)
        """
        # Try to get existing user
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            logger.info(f"Found existing user for telegram_id {telegram_id}")
            return user
        
        # Create new user
        logger.info(f"Creating new user for telegram_id {telegram_id}")
        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
        
        return await self.create(user_data)


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()
