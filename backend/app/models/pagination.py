"""Pagination models for API responses."""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for requests."""
    
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit (same as page_size)."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    items: list[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items and pagination params.
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse instance
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters for large datasets."""
    
    cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response."""
    
    items: list[T] = Field(description="List of items")
    next_cursor: Optional[str] = Field(description="Cursor for next page")
    has_more: bool = Field(description="Whether there are more items")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        limit: int,
        cursor_field: str = "id"
    ) -> "CursorPaginatedResponse[T]":
        """Create cursor paginated response.
        
        Args:
            items: List of items (should fetch limit + 1)
            limit: Requested limit
            cursor_field: Field to use as cursor
            
        Returns:
            CursorPaginatedResponse instance
        """
        has_more = len(items) > limit
        
        # Trim to limit
        if has_more:
            items = items[:limit]
        
        # Get next cursor from last item
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            if isinstance(last_item, dict):
                next_cursor = str(last_item.get(cursor_field))
            else:
                next_cursor = str(getattr(last_item, cursor_field, None))
        
        return cls(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more
        )
