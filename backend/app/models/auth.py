"""Authentication request and response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength


# ============================================================================
# Request Models
# ============================================================================

class RegisterRequest(BaseModel):
    """Request model for user registration.
    
    Example:
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
    """
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 chars, must include uppercase, lowercase, digit, and special char)",
        examples=["SecurePass123!"],
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="User's full name",
        examples=["John Doe"],
    )
    telegram_id: Optional[int] = Field(
        default=None,
        description="Optional Telegram user ID for integration",
        examples=[123456789],
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and clean full name."""
        # Strip whitespace
        v = v.strip()
        
        # Check if empty after stripping
        if not v:
            raise ValueError("Full name cannot be empty")
        
        # Check for invalid characters
        if any(char in v for char in ["<", ">", "{", "}", "[", "]"]):
            raise ValueError("Full name contains invalid characters")
        
        return v


class LoginRequest(BaseModel):
    """Request model for user login.
    
    Example:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    """
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePass123!"],
    )


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing access token.
    
    Example:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """
    
    refresh_token: str = Field(
        ...,
        description="Refresh token to exchange for new access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class ChangePasswordRequest(BaseModel):
    """Request model for changing password.
    
    Example:
        {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }
    """
    
    current_password: str = Field(
        ...,
        description="Current password",
        examples=["OldPass123!"],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password",
        examples=["NewPass456!"],
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class ResetPasswordRequest(BaseModel):
    """Request model for password reset.
    
    Example:
        {
            "email": "user@example.com"
        }
    """
    
    email: EmailStr = Field(
        ...,
        description="Email address to send reset link to",
        examples=["user@example.com"],
    )


class ConfirmPasswordResetRequest(BaseModel):
    """Request model for confirming password reset.
    
    Example:
        {
            "token": "reset-token-here",
            "new_password": "NewPass456!"
        }
    """
    
    token: str = Field(
        ...,
        description="Password reset token from email",
        examples=["reset-token-here"],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password",
        examples=["NewPass456!"],
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


# ============================================================================
# Response Models
# ============================================================================

class TokenResponse(BaseModel):
    """Response model for authentication tokens.
    
    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        examples=["bearer"],
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[900],
    )


class UserResponse(BaseModel):
    """Response model for user data.
    
    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "full_name": "John Doe",
            "telegram_id": 123456789,
            "email_verified": true,
            "created_at": "2025-01-17T10:30:00Z",
            "updated_at": "2025-01-17T10:30:00Z"
        }
    """
    
    id: UUID = Field(
        ...,
        description="User unique identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    full_name: str = Field(
        ...,
        description="User's full name",
        examples=["John Doe"],
    )
    telegram_id: Optional[int] = Field(
        default=None,
        description="Telegram user ID if linked",
        examples=[123456789],
    )
    email_verified: bool = Field(
        default=False,
        description="Whether email is verified",
        examples=[True],
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        examples=["2025-01-17T10:30:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2025-01-17T10:30:00Z"],
    )
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response model for successful login.
    
    Example:
        {
            "user": {...},
            "tokens": {...}
        }
    """
    
    user: UserResponse = Field(
        ...,
        description="User information",
    )
    tokens: TokenResponse = Field(
        ...,
        description="Authentication tokens",
    )


class MessageResponse(BaseModel):
    """Generic message response.
    
    Example:
        {
            "message": "Operation successful"
        }
    """
    
    message: str = Field(
        ...,
        description="Response message",
        examples=["Operation successful"],
    )


# ============================================================================
# Internal Models (not exposed in API)
# ============================================================================

class TokenPayload(BaseModel):
    """JWT token payload structure (internal use only)."""
    
    sub: str = Field(..., description="Subject (user_id)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(..., description="Token type (access or refresh)")
