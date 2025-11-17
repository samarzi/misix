"""Task request and response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class TaskStatus(str):
    """Task status values."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str):
    """Task priority values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Request Models
# ============================================================================

class CreateTaskRequest(BaseModel):
    """Request model for creating a task.
    
    Example:
        {
            "title": "Complete project documentation",
            "description": "Write comprehensive docs for the API",
            "priority": "high",
            "status": "new",
            "deadline": "2025-01-20T18:00:00Z",
            "estimated_hours": 8.5
        }
    """
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Task title",
        examples=["Complete project documentation"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detailed task description",
        examples=["Write comprehensive docs for the API"],
    )
    priority: str = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority (low, medium, high, critical)",
        examples=["high"],
    )
    status: str = Field(
        default=TaskStatus.NEW,
        description="Task status (new, in_progress, waiting, completed, cancelled)",
        examples=["new"],
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Task deadline (ISO 8601 format)",
        examples=["2025-01-20T18:00:00Z"],
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1000.0,
        description="Estimated hours to complete",
        examples=[8.5],
    )
    actual_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1000.0,
        description="Actual hours spent",
        examples=[10.0],
    )
    project_id: Optional[UUID] = Field(
        default=None,
        description="Associated project ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        allowed = {TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {allowed}")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed = {
            TaskStatus.NEW,
            TaskStatus.IN_PROGRESS,
            TaskStatus.WAITING,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        }
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v
    
    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate deadline is not in the past."""
        if v and v < datetime.now(v.tzinfo):
            raise ValueError("Deadline cannot be in the past")
        return v
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and clean title."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class UpdateTaskRequest(BaseModel):
    """Request model for updating a task.
    
    All fields are optional - only provided fields will be updated.
    
    Example:
        {
            "status": "completed",
            "actual_hours": 10.5
        }
    """
    
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Task title",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Task description",
    )
    priority: Optional[str] = Field(
        default=None,
        description="Task priority",
    )
    status: Optional[str] = Field(
        default=None,
        description="Task status",
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Task deadline",
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1000.0,
        description="Estimated hours",
    )
    actual_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1000.0,
        description="Actual hours",
    )
    project_id: Optional[UUID] = Field(
        default=None,
        description="Project ID",
    )
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority value."""
        if v is None:
            return v
        allowed = {TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {allowed}")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value."""
        if v is None:
            return v
        allowed = {
            TaskStatus.NEW,
            TaskStatus.IN_PROGRESS,
            TaskStatus.WAITING,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        }
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean title."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class TaskFilters(BaseModel):
    """Filters for querying tasks.
    
    Example:
        {
            "status": "in_progress",
            "priority": "high",
            "project_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """
    
    status: Optional[str] = Field(
        default=None,
        description="Filter by status",
    )
    priority: Optional[str] = Field(
        default=None,
        description="Filter by priority",
    )
    project_id: Optional[UUID] = Field(
        default=None,
        description="Filter by project",
    )
    has_deadline: Optional[bool] = Field(
        default=None,
        description="Filter tasks with/without deadline",
    )


# ============================================================================
# Response Models
# ============================================================================

class TaskResponse(BaseModel):
    """Response model for task data.
    
    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "123e4567-e89b-12d3-a456-426614174001",
            "title": "Complete project documentation",
            "description": "Write comprehensive docs",
            "priority": "high",
            "status": "in_progress",
            "deadline": "2025-01-20T18:00:00Z",
            "estimated_hours": 8.5,
            "actual_hours": 5.0,
            "project_id": null,
            "created_at": "2025-01-17T10:00:00Z",
            "updated_at": "2025-01-17T12:00:00Z"
        }
    """
    
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    priority: str
    status: str
    deadline: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    project_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response model for list of tasks with pagination.
    
    Example:
        {
            "tasks": [...],
            "total": 42,
            "page": 1,
            "page_size": 20,
            "has_more": true
        }
    """
    
    tasks: list[TaskResponse]
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages")
