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
    
    @staticmethod
    def _generate_full_name(
        first_name: Optional[str],
        last_name: Optional[str],
        username: Optional[str]
    ) -> str:
        """Generate full_name from available user data.
        
        Priority:
        1. first_name + last_name (if both provided)
        2. first_name only (if only first_name)
        3. last_name only (if only last_name)
        4. username (if names are null)
        5. "Telegram User" (fallback if all are null)
        
        Args:
            first_name: User's first name
            last_name: User's last name
            username: User's Telegram username
            
        Returns:
            Generated full name (never null)
        """
        # Build name from first_name and last_name
        name_parts = []
        if first_name and first_name.strip():
            name_parts.append(first_name.strip())
        if last_name and last_name.strip():
            name_parts.append(last_name.strip())
        
        if name_parts:
            return " ".join(name_parts)
        
        # Fallback to username
        if username and username.strip():
            return username.strip()
        
        # Final fallback
        return "Telegram User"
    
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
        
        # Create new user with generated full_name
        logger.info(f"Creating new user for telegram_id {telegram_id}")
        full_name = self._generate_full_name(first_name, last_name, username)
        
        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,  # Always provide full_name
        }
        
        return await self.create(user_data)
    
    async def get_all_with_telegram(self) -> list[dict]:
        """Get all users who have Telegram ID.
        
        Returns:
            List of users with telegram_id
        """
        try:
            supabase = self._get_client()
            result = (
                supabase.table(self.table_name)
                .select("*")
                .not_.is_("telegram_id", "null")
                .execute()
            )
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get all with telegram failed: {e}")
            return []


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()
