"""Mood tracking models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MoodEntry(BaseModel):
    """Model for mood tracking entry."""
    
    id: Optional[str] = None
    user_id: str
    mood: str  # happy, sad, anxious, calm, excited, tired, stressed, etc.
    intensity: int = Field(ge=1, le=10, description="Mood intensity from 1 to 10")
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MoodCreate(BaseModel):
    """Model for creating mood entry."""
    
    mood: str
    intensity: int = Field(ge=1, le=10)
    note: Optional[str] = None


class MoodTrend(BaseModel):
    """Model for mood trend analysis."""
    
    average_intensity: float
    most_common_mood: str
    mood_distribution: dict[str, int]
    period_days: int
