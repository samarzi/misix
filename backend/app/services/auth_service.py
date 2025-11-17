"""Authentication service for user registration, login, and token management."""

import logging
from typing import Optional
from uuid import UUID

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)
from app.core.security import (
    create_token_response,
    hash_password,
    verify_password,
    verify_token,
)
from app.shared.supabase import get_supabase_client, supabase_available

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations.
    
    This service manages user registration, login, token refresh,
    and password management operations.
    """
    
    def __init__(self):
        """Initialize the authentication service."""
        if not supabase_available():
            logger.warning("Supabase not available - authentication will fail")
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        telegram_id: Optional[int] = None,
    ) -> dict:
        """Register a new user.
        
        Args:
            email: User's email address
            password: User's password (will be hashed)
            full_name: User's full name
            telegram_id: Optional Telegram user ID
            
        Returns:
            Dictionary containing user data
            
        Raises:
            ConflictError: If email is already registered
            DatabaseError: If database operation fails
            
        Example:
            >>> service = AuthService()
            >>> user = await service.register(
            ...     email="user@example.com",
            ...     password="SecurePass123!",
            ...     full_name="John Doe"
            ... )
        """
        if not supabase_available():
            raise DatabaseError("Database connection not available")
        
        try:
            supabase = get_supabase_client()
            
            # Check if user already exists
            existing = supabase.table("users").select("id").eq("email", email).execute()
            
            if existing.data:
                raise ConflictError(
                    message="Email already registered",
                    details={"email": email},
                )
            
            # Hash password
            password_hash = hash_password(password)
            
            # Create user
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "email_verified": False,
            }
            
            if telegram_id is not None:
                user_data["telegram_id"] = telegram_id
            
            result = supabase.table("users").insert(user_data).execute()
            
            if not result.data:
                raise DatabaseError("Failed to create user")
            
            user = result.data[0]
            logger.info(f"User registered successfully: {user['id']}")
            
            # Remove password_hash from response
            user.pop("password_hash", None)
            
            return user
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise DatabaseError(f"Registration failed: {str(e)}")
    
    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing user data and tokens
            
        Raises:
            AuthenticationError: If credentials are invalid
            DatabaseError: If database operation fails
            
        Example:
            >>> service = AuthService()
            >>> result = await service.login(
            ...     email="user@example.com",
            ...     password="SecurePass123!"
            ... )
            >>> print(result.keys())
            dict_keys(['user', 'tokens'])
        """
        if not supabase_available():
            raise DatabaseError("Database connection not available")
        
        try:
            supabase = get_supabase_client()
            
            # Get user by email
            result = supabase.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                raise AuthenticationError("Invalid email or password")
            
            user = result.data[0]
            
            # Verify password
            if not verify_password(password, user["password_hash"]):
                logger.warning(f"Failed login attempt for email: {email}")
                raise AuthenticationError("Invalid email or password")
            
            # Generate tokens
            user_id = str(user["id"])
            tokens = create_token_response(user_id)
            
            logger.info(f"User logged in successfully: {user_id}")
            
            # Remove password_hash from response
            user.pop("password_hash", None)
            
            return {
                "user": user,
                "tokens": tokens,
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise DatabaseError(f"Login failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary containing new tokens
            
        Raises:
            AuthenticationError: If refresh token is invalid
            NotFoundError: If user not found
            
        Example:
            >>> service = AuthService()
            >>> tokens = await service.refresh_access_token(refresh_token)
        """
        # Verify refresh token
        user_id = verify_token(refresh_token, token_type="refresh")
        
        if not user_id:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Verify user still exists
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise NotFoundError("User", user_id)
        
        # Generate new tokens
        tokens = create_token_response(user_id)
        
        logger.info(f"Access token refreshed for user: {user_id}")
        
        return tokens
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User data dictionary or None if not found
            
        Example:
            >>> service = AuthService()
            >>> user = await service.get_user_by_id("user-id-here")
        """
        if not supabase_available():
            return None
        
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not result.data:
                return None
            
            user = result.data[0]
            # Remove password_hash from response
            user.pop("password_hash", None)
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email.
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
            
        Example:
            >>> service = AuthService()
            >>> user = await service.get_user_by_email("user@example.com")
        """
        if not supabase_available():
            return None
        
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                return None
            
            user = result.data[0]
            # Remove password_hash from response
            user.pop("password_hash", None)
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user's password.
        
        Args:
            user_id: User's unique identifier
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully
            
        Raises:
            AuthenticationError: If current password is incorrect
            NotFoundError: If user not found
            DatabaseError: If database operation fails
            
        Example:
            >>> service = AuthService()
            >>> success = await service.change_password(
            ...     user_id="user-id",
            ...     current_password="OldPass123!",
            ...     new_password="NewPass456!"
            ... )
        """
        if not supabase_available():
            raise DatabaseError("Database connection not available")
        
        try:
            supabase = get_supabase_client()
            
            # Get user with password hash
            result = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not result.data:
                raise NotFoundError("User", user_id)
            
            user = result.data[0]
            
            # Verify current password
            if not verify_password(current_password, user["password_hash"]):
                raise AuthenticationError("Current password is incorrect")
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            update_result = (
                supabase.table("users")
                .update({"password_hash": new_password_hash})
                .eq("id", user_id)
                .execute()
            )
            
            if not update_result.data:
                raise DatabaseError("Failed to update password")
            
            logger.info(f"Password changed successfully for user: {user_id}")
            
            return True
            
        except (AuthenticationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            raise DatabaseError(f"Password change failed: {str(e)}")
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Mark user's email as verified.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if email verified successfully
            
        Raises:
            NotFoundError: If user not found
            DatabaseError: If database operation fails
        """
        if not supabase_available():
            raise DatabaseError("Database connection not available")
        
        try:
            supabase = get_supabase_client()
            
            result = (
                supabase.table("users")
                .update({"email_verified": True})
                .eq("id", user_id)
                .execute()
            )
            
            if not result.data:
                raise NotFoundError("User", user_id)
            
            logger.info(f"Email verified for user: {user_id}")
            
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            raise DatabaseError(f"Email verification failed: {str(e)}")


# ============================================================================
# Global Service Instance
# ============================================================================

def get_auth_service() -> AuthService:
    """Get authentication service instance.
    
    Returns:
        AuthService instance
    """
    return AuthService()
