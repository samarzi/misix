"""Custom exception classes for the application."""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for all application errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails.
    
    Examples:
        - Invalid credentials
        - Invalid token
        - Expired token
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AppException):
    """Raised when user lacks permission for an action.
    
    Examples:
        - Accessing another user's data
        - Performing admin-only actions
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=403, details=details)


class ValidationError(AppException):
    """Raised when input validation fails.
    
    Examples:
        - Invalid email format
        - Password too weak
        - Missing required fields
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[dict[str, list[str]]] = None,
    ):
        details = {"errors": errors} if errors else {}
        super().__init__(message, status_code=422, details=details)


class NotFoundError(AppException):
    """Raised when a requested resource is not found.
    
    Examples:
        - User not found
        - Task not found
        - Note not found
    """
    
    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[dict[str, Any]] = None,
    ):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404, details=details)


class ConflictError(AppException):
    """Raised when a resource conflict occurs.
    
    Examples:
        - Email already registered
        - Duplicate entry
    """
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=409, details=details)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded.
    
    Examples:
        - Too many login attempts
        - Too many API requests
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, status_code=429, details=details)


class ExternalServiceError(AppException):
    """Raised when an external service fails.
    
    Examples:
        - Yandex GPT API error
        - Supabase connection error
        - Redis connection error
    """
    
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[dict[str, Any]] = None,
    ):
        full_message = f"{service}: {message}"
        super().__init__(full_message, status_code=503, details=details)


class DatabaseError(AppException):
    """Raised when a database operation fails.
    
    Examples:
        - Connection error
        - Query timeout
        - Constraint violation
    """
    
    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, details=details)
