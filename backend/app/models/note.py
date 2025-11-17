"""Note request and response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Models
# ============================================================================

class CreateNoteRequest(BaseModel):
    """Request model for creating a note.
    
    Example:
        {
            "title": "Meeting Notes",
            "content": "# Meeting with team\\n\\n- Discussed project timeline",
            "content_format": "markdown",
            "folder_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """
    
    title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Note title (optional)",
        examples=["Meeting Notes"],
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Note content",
        examples=["# Meeting with team\\n\\n- Discussed project timeline"],
    )
    content_format: str = Field(
        default="markdown",
        description="Content format (markdown, html, plain)",
        examples=["markdown"],
    )
    folder_id: Optional[UUID] = Field(
        default=None,
        description="Folder ID to organize note",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    is_favorite: bool = Field(
        default=False,
        description="Mark as favorite",
        examples=[False],
    )
    
    @field_validator("content_format")
    @classmethod
    def validate_content_format(cls, v: str) -> str:
        """Validate content format."""
        allowed = {"markdown", "html", "plain"}
        if v not in allowed:
            raise ValueError(f"Content format must be one of: {allowed}")
        return v
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate and clean content."""
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty")
        return v
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean title."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None  # Empty title becomes None
        return v


class UpdateNoteRequest(BaseModel):
    """Request model for updating a note.
    
    All fields are optional - only provided fields will be updated.
    
    Example:
        {
            "title": "Updated Meeting Notes",
            "is_favorite": true
        }
    """
    
    title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Note title",
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100000,
        description="Note content",
    )
    content_format: Optional[str] = Field(
        default=None,
        description="Content format",
    )
    folder_id: Optional[UUID] = Field(
        default=None,
        description="Folder ID",
    )
    is_favorite: Optional[bool] = Field(
        default=None,
        description="Favorite status",
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="Archive status",
    )
    
    @field_validator("content_format")
    @classmethod
    def validate_content_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate content format."""
        if v is None:
            return v
        allowed = {"markdown", "html", "plain"}
        if v not in allowed:
            raise ValueError(f"Content format must be one of: {allowed}")
        return v
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate content."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty")
        return v


class NoteFilters(BaseModel):
    """Filters for querying notes.
    
    Example:
        {
            "folder_id": "123e4567-e89b-12d3-a456-426614174000",
            "is_favorite": true,
            "is_archived": false,
            "search": "meeting"
        }
    """
    
    folder_id: Optional[UUID] = Field(
        default=None,
        description="Filter by folder",
    )
    is_favorite: Optional[bool] = Field(
        default=None,
        description="Filter favorites",
    )
    is_archived: Optional[bool] = Field(
        default=None,
        description="Filter archived",
    )
    search: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Search in title and content",
    )


# ============================================================================
# Response Models
# ============================================================================

class NoteResponse(BaseModel):
    """Response model for note data.
    
    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "123e4567-e89b-12d3-a456-426614174001",
            "title": "Meeting Notes",
            "content": "# Meeting with team",
            "content_format": "markdown",
            "folder_id": null,
            "is_favorite": false,
            "is_archived": false,
            "created_at": "2025-01-17T10:00:00Z",
            "updated_at": "2025-01-17T12:00:00Z"
        }
    """
    
    id: UUID
    user_id: UUID
    title: Optional[str]
    content: str
    content_format: str
    folder_id: Optional[UUID]
    is_favorite: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Response model for list of notes with pagination."""
    
    notes: list[NoteResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
