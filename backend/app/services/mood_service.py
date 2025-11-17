"""Mood tracking service."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from collections import Counter

from app.repositories.mood import get_mood_repository
from app.models.mood import MoodEntry, MoodCreate, MoodTrend

logger = logging.getLogger(__name__)


class MoodService:
    """Service for mood tracking operations."""
    
    def __init__(self):
        self.mood_repo = get_mood_repository()
    
    async def save_mood(
        self,
        user_id: str,
        mood: str,
        intensity: int,
        note: Optional[str] = None
    ) -> dict:
        """Save mood entry.
        
        Args:
            user_id: User ID
            mood: Mood type (happy, sad, anxious, etc.)
            intensity: Intensity from 1 to 10
            note: Optional note
            
        Returns:
            Created mood entry
        """
        try:
            mood_data = {
                "user_id": user_id,
                "mood": mood.lower(),
                "intensity": intensity,
                "note": note
            }
            
            result = await self.mood_repo.create(mood_data)
            logger.info(f"Saved mood entry for user {user_id}: {mood} ({intensity}/10)")
            return result
        except Exception as e:
            logger.error(f"Failed to save mood: {e}")
            raise
    
    async def get_mood_history(
        self,
        user_id: str,
        days: int = 7
    ) -> List[dict]:
        """Get mood history for user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of mood entries
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            entries = await self.mood_repo.get_by_user_and_period(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return entries
        except Exception as e:
            logger.error(f"Failed to get mood history: {e}")
            return []
    
    async def analyze_mood_trends(
        self,
        user_id: str,
        days: int = 7
    ) -> MoodTrend:
        """Analyze mood trends for user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Mood trend analysis
        """
        try:
            entries = await self.get_mood_history(user_id, days)
            
            if not entries:
                return MoodTrend(
                    average_intensity=0.0,
                    most_common_mood="unknown",
                    mood_distribution={},
                    period_days=days
                )
            
            # Calculate average intensity
            intensities = [entry["intensity"] for entry in entries]
            average_intensity = sum(intensities) / len(intensities)
            
            # Find most common mood
            moods = [entry["mood"] for entry in entries]
            mood_counter = Counter(moods)
            most_common_mood = mood_counter.most_common(1)[0][0]
            
            # Build mood distribution
            mood_distribution = dict(mood_counter)
            
            return MoodTrend(
                average_intensity=round(average_intensity, 2),
                most_common_mood=most_common_mood,
                mood_distribution=mood_distribution,
                period_days=days
            )
        except Exception as e:
            logger.error(f"Failed to analyze mood trends: {e}")
            return MoodTrend(
                average_intensity=0.0,
                most_common_mood="unknown",
                mood_distribution={},
                period_days=days
            )


def get_mood_service() -> MoodService:
    """Get mood service instance."""
    return MoodService()
