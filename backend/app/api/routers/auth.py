"""Authentication API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)
from app.models.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService, get_auth_service
from app.api.deps import get_current_user_id, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password",
    responses={
        201: {
            "description": "User created successfully",
            "model": UserResponse,
        },
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Email already registered",
                        "details": {"email": "user@example.com"},
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Validation failed",
                        "details": {
                            "errors": {
                                "password": [
                                    "Password must contain at least one uppercase letter"
                                ]
                            }
                        },
                    }
                }
            },
        },
    },
)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user account.
    
    Creates a new user with the provided email, password, and full name.
    Password will be securely hashed before storage.
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }
    ```
    """
    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            telegram_id=request.telegram_id,
        )
        return UserResponse(**user)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": e.message, "details": e.details},
        )
    except DatabaseError as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Registration failed", "details": {}},
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user and receive access and refresh tokens",
    responses={
        200: {
            "description": "Login successful",
            "model": LoginResponse,
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"error": "Invalid email or password"}
                }
            },
        },
    },
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """Authenticate user and return tokens.
    
    Validates user credentials and returns JWT access and refresh tokens.
    
    **Access Token:**
    - Short-lived (15 minutes)
    - Used for API authentication
    - Include in Authorization header: `Bearer <access_token>`
    
    **Refresh Token:**
    - Long-lived (7 days)
    - Used to obtain new access tokens
    - Store securely on client
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "user": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "full_name": "John Doe",
            "email_verified": false,
            "created_at": "2025-01-17T10:30:00Z"
        },
        "tokens": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 900
        }
    }
    ```
    """
    try:
        result = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        return LoginResponse(
            user=UserResponse(**result["user"]),
            tokens=TokenResponse(**result["tokens"]),
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": e.message},
        )
    except DatabaseError as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Login failed"},
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange refresh token for new access token",
    responses={
        200: {
            "description": "Token refreshed successfully",
            "model": TokenResponse,
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"error": "Invalid or expired refresh token"}
                }
            },
        },
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Refresh access token using refresh token.
    
    When the access token expires, use this endpoint to obtain a new one
    without requiring the user to log in again.
    
    **Example Request:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Example Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 900
    }
    ```
    """
    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)
        return TokenResponse(**tokens)
    except (AuthenticationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": e.message},
        )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change user's password (requires authentication)",
    responses={
        200: {
            "description": "Password changed successfully",
            "model": MessageResponse,
        },
        401: {
            "description": "Current password is incorrect or not authenticated",
            "content": {
                "application/json": {
                    "example": {"error": "Current password is incorrect"}
                }
            },
        },
    },
)
async def change_password(
    request: ChangePasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> MessageResponse:
    """Change user's password.
    
    Requires authentication via JWT token. User must provide current password for verification.
    
    **Authentication Required:**
    Include JWT access token in Authorization header:
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    **Example Request:**
    ```json
    {
        "current_password": "OldPass123!",
        "new_password": "NewPass456!"
    }
    ```
    """
    try:
        await auth_service.change_password(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return MessageResponse(message="Password changed successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": e.message},
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": e.message},
        )
    except DatabaseError as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Password change failed"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user's profile information",
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "model": UserResponse,
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"error": "Not authenticated"}
                }
            },
        },
    },
)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> UserResponse:
    """Get current authenticated user's profile.
    
    Requires authentication via JWT token in Authorization header.
    
    **Authentication Required:**
    Include JWT access token in Authorization header:
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    **Example Response:**
    ```json
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "full_name": "John Doe",
        "telegram_id": null,
        "email_verified": false,
        "created_at": "2025-01-17T10:30:00Z",
        "updated_at": "2025-01-17T10:30:00Z"
    }
    ```
    """
    return UserResponse(**current_user)
