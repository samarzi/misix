"""Common models used across the application."""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints.
    
    Example:
        {
            "page": 1,
            "page_size": 20
        }
    """
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
        examples=[1],
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
        examples=[20],
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model.
    
    Example:
        {
            "items": [...],
            "total": 42,
            "page": 1,
            "page_size": 20,
            "has_more": true
        }
    """
    
    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items and pagination params."""
        has_more = (pagination.page * pagination.page_size) < total
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            has_more=has_more,
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


class ErrorResponse(BaseModel):
    """Error response model.
    
    Example:
        {
            "error": "Validation failed",
            "details": {
                "field": ["Error message"]
            }
        }
    """
    
    error: str = Field(
        ...,
        description="Error message",
        examples=["Validation failed"],
    )
    details: dict = Field(
        default_factory=dict,
        description="Additional error details",
        examples=[{"field": ["Error message"]}],
    )


class HealthCheckResponse(BaseModel):
    """Health check response model.
    
    Example:
        {
            "status": "healthy",
            "timestamp": "2025-01-17T10:30:00Z",
            "version": "1.0.0",
            "checks": {
                "database": "ok",
                "redis": "ok"
            }
        }
    """
    
    status: str = Field(
        ...,
        description="Overall health status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    timestamp: str = Field(
        ...,
        description="Check timestamp (ISO 8601)",
        examples=["2025-01-17T10:30:00Z"],
    )
    version: str = Field(
        ...,
        description="Application version",
        examples=["1.0.0"],
    )
    checks: dict[str, str] = Field(
        default_factory=dict,
        description="Individual service checks",
        examples=[{"database": "ok", "redis": "ok"}],
    )
