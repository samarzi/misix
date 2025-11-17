"""Dependency injection for API endpoints."""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import verify_token
from app.services.auth_service import AuthService, get_auth_service

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for Swagger UI
security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT access token",
    auto_error=False,
)


async def get_current_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> str:
    """Extract and validate user ID from JWT token.
    
    This dependency extracts the JWT token from the Authorization header,
    validates it, and returns the user ID.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
        
    Example:
        ```python
        @router.get("/protected")
        async def protected_route(
            user_id: Annotated[str, Depends(get_current_user_id)]
        ):
            return {"user_id": user_id}
        ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify token and extract user_id
    user_id = verify_token(token, token_type="access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    """Get current authenticated user's full profile.
    
    This dependency builds on get_current_user_id to fetch the complete
    user profile from the database.
    
    Args:
        user_id: User ID from JWT token
        auth_service: Authentication service instance
        
    Returns:
        User profile dictionary
        
    Raises:
        HTTPException: If user not found
        
    Example:
        ```python
        @router.get("/me")
        async def get_profile(
            user: Annotated[dict, Depends(get_current_user)]
        ):
            return user
        ```
    """
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found"},
        )
    
    return user


async def get_optional_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[str]:
    """Extract user ID from JWT token if present (optional authentication).
    
    This dependency is similar to get_current_user_id but doesn't raise
    an error if no token is provided. Useful for endpoints that work
    differently for authenticated vs anonymous users.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        User ID string if authenticated, None otherwise
        
    Example:
        ```python
        @router.get("/public")
        async def public_route(
            user_id: Annotated[Optional[str], Depends(get_optional_user_id)]
        ):
            if user_id:
                return {"message": f"Hello user {user_id}"}
            return {"message": "Hello anonymous user"}
        ```
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    return user_id


def require_verified_email(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Require that the current user has a verified email.
    
    This dependency can be chained after get_current_user to enforce
    email verification for sensitive operations.
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        User profile dictionary
        
    Raises:
        HTTPException: If email is not verified
        
    Example:
        ```python
        @router.post("/sensitive-action")
        async def sensitive_action(
            user: Annotated[dict, Depends(require_verified_email)]
        ):
            return {"message": "Action performed"}
        ```
    """
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Email verification required",
                "message": "Please verify your email before performing this action",
            },
        )
    
    return user
