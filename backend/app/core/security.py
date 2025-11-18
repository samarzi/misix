"""Security utilities for Telegram-based authentication.

Note: This module has been simplified to remove email/password authentication.
The application uses only Telegram-based authentication via telegram_id.
JWT token functions are kept for potential future use with Telegram authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


# ============================================================================
# JWT Token Management (Optional - for Telegram auth if needed)
# ============================================================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.
    
    Args:
        subject: Subject of the token (usually user_id)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token(subject="user-123")
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token.
    
    Args:
        subject: Subject of the token (usually user_id)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_refresh_token(subject="user-123")
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload if valid, None otherwise
        
    Example:
        >>> token = create_access_token(subject="user-123")
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        user-123
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify a JWT token and return the subject (user_id).
    
    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        User ID (subject) if token is valid, None otherwise
        
    Example:
        >>> token = create_access_token(subject="user-123")
        >>> user_id = verify_token(token, token_type="access")
        >>> print(user_id)
        user-123
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Verify token type
    if payload.get("type") != token_type:
        return None
    
    # Extract subject (user_id)
    subject: Optional[str] = payload.get("sub")
    return subject


# ============================================================================
# Token Response Helper (Optional - for Telegram auth if needed)
# ============================================================================

def create_token_response(user_id: str) -> dict:
    """Create a complete token response with access and refresh tokens.
    
    Note: This function is kept for potential future use with Telegram authentication.
    Currently, the application uses Telegram-based authentication without JWT tokens.
    
    Args:
        user_id: User ID to create tokens for
        
    Returns:
        Dictionary containing access_token, refresh_token, token_type, and expires_in
        
    Example:
        >>> response = create_token_response(user_id="user-123")
        >>> print(response.keys())
        dict_keys(['access_token', 'refresh_token', 'token_type', 'expires_in'])
    """
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,  # in seconds
    }


# ============================================================================
# Utility Functions
# ============================================================================

def generate_secure_random_string(length: int = 32) -> str:
    """Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string to generate
        
    Returns:
        Random hex string
        
    Example:
        >>> random_str = generate_secure_random_string(32)
        >>> len(random_str)
        64  # hex encoding doubles the length
    """
    import secrets
    return secrets.token_hex(length)


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks.
    
    Args:
        val1: First string to compare
        val2: Second string to compare
        
    Returns:
        True if strings are equal, False otherwise
        
    Example:
        >>> constant_time_compare("secret", "secret")
        True
        >>> constant_time_compare("secret", "public")
        False
    """
    import hmac
    return hmac.compare_digest(val1, val2)
