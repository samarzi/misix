"""Service for extracting structured data from natural language."""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from app.services.ai_service import AIService, get_ai_service

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting structured data from user messages."""
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or get_ai_service()
    
    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        """Parse relative deadline strings to datetime.
        
        Args:
            deadline_str: String like "tomorrow", "через 2 дня", "2024-01-15"
            
        Returns:
            Parsed datetime or None
        """
        if not deadline_str or deadline_str == "null":
            return None
        
        deadline_lower = deadline_str.lower()
        now = datetime.now()
        
        # Tomorrow
        if "tomorrow" in deadline_lower or "завтра" in deadline_lower:
            return now + timedelta(days=1)
        
        # Today
        if "today" in deadline_lower or "сегодня" in deadline_lower:
            return now
        
        # In X days
        days_match = re.search(r"через\s+(\d+)\s+(?:день|дня|дней)", deadline_lower)
        if days_match:
            days = int(days_match.group(1))
            return now + timedelta(days=days)
        
        # Next week
        if "next week" in deadline_lower or "следующ" in deadline_lower and "недел" in deadline_lower:
            return now + timedelta(weeks=1)
        
        # Try to parse as ISO date
        try:
            return datetime.fromisoformat(deadline_str)
        except:
            pass
        
        return None


def get_extraction_service() -> ExtractionService:
    """Get extraction service instance."""
    return ExtractionService()

    async def extract_task_data(self, message: str) -> Optional[dict]:
        """Extract task information from message.
        
        Args:
            message: User message
            
        Returns:
            Task data dict or None if confidence too low
        """
        if not self.ai_service.available:
            logger.warning("AI service not available for task extraction")
            return None
        
        try:
            prompt = f"""
Извлеки информацию о задаче из сообщения: "{message}"

Верни JSON:
{{
    "title": "описание задачи",
    "deadline": "YYYY-MM-DD HH:MM или tomorrow/today/через X дней или null",
    "priority": "low/medium/high",
    "confidence": 0.0-1.0
}}

Примеры:
"напомни завтра позвонить партнеру" -> {{"title": "позвонить партнеру", "deadline": "tomorrow 09:00", "priority": "medium", "confidence": 0.95}}
"срочно купить молоко" -> {{"title": "купить молоко", "deadline": null, "priority": "high", "confidence": 0.9}}
"через 2 дня встреча" -> {{"title": "встреча", "deadline": "через 2 дня", "priority": "medium", "confidence": 0.85}}

Верни ТОЛЬКО JSON, без дополнительного текста.
"""
            
            messages = [
                {"role": "system", "text": "Ты - экстрактор данных. Отвечай только JSON."},
                {"role": "user", "text": prompt}
            ]
            
            response = await self.ai_service.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Check confidence
            if data.get('confidence', 0) < 0.7:
                logger.info(f"Task extraction confidence too low: {data.get('confidence')}")
                return None
            
            # Parse deadline
            if data.get('deadline'):
                data['deadline'] = self._parse_deadline(data['deadline'])
            
            logger.info(f"Extracted task data: {data['title']}")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse task extraction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Task extraction failed: {e}")
            return None

    async def extract_finance_data(self, message: str) -> Optional[dict]:
        """Extract finance information from message.
        
        Args:
            message: User message
            
        Returns:
            Finance data dict or None if confidence too low
        """
        if not self.ai_service.available:
            logger.warning("AI service not available for finance extraction")
            return None
        
        try:
            prompt = f"""
Извлеки финансовую информацию из сообщения: "{message}"

Верни JSON:
{{
    "amount": число,
    "type": "expense" или "income",
    "category": "еда и напитки/транспорт/развлечения/здоровье/покупки/другое",
    "description": "краткое описание",
    "confidence": 0.0-1.0
}}

Примеры:
"потратил 500 рублей на кофе" -> {{"amount": 500, "type": "expense", "category": "еда и напитки", "description": "кофе", "confidence": 0.95}}
"заработал 50000" -> {{"amount": 50000, "type": "income", "category": "другое", "description": "доход", "confidence": 0.9}}
"200₽ на такси" -> {{"amount": 200, "type": "expense", "category": "транспорт", "description": "такси", "confidence": 0.95}}

Верни ТОЛЬКО JSON, без дополнительного текста.
"""
            
            messages = [
                {"role": "system", "text": "Ты - экстрактор финансовых данных. Отвечай только JSON."},
                {"role": "user", "text": prompt}
            ]
            
            response = await self.ai_service.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Check confidence
            if data.get('confidence', 0) < 0.7:
                logger.info(f"Finance extraction confidence too low: {data.get('confidence')}")
                return None
            
            logger.info(f"Extracted finance data: {data['amount']} ({data['type']})")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse finance extraction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Finance extraction failed: {e}")
            return None

    async def extract_note_data(self, message: str) -> Optional[dict]:
        """Extract note information from message.
        
        Args:
            message: User message
            
        Returns:
            Note data dict or None if confidence too low
        """
        if not self.ai_service.available:
            logger.warning("AI service not available for note extraction")
            return None
        
        try:
            prompt = f"""
Извлеки информацию для заметки из сообщения: "{message}"

Верни JSON:
{{
    "title": "краткий заголовок",
    "content": "полное содержание",
    "confidence": 0.0-1.0
}}

Примеры:
"запомни что встреча в офисе на Ленина 5" -> {{"title": "Встреча в офисе", "content": "встреча в офисе на Ленина 5", "confidence": 0.9}}
"сохрани пароль от wifi: qwerty123" -> {{"title": "Пароль от wifi", "content": "пароль от wifi: qwerty123", "confidence": 0.95}}

Верни ТОЛЬКО JSON, без дополнительного текста.
"""
            
            messages = [
                {"role": "system", "text": "Ты - экстрактор заметок. Отвечай только JSON."},
                {"role": "user", "text": prompt}
            ]
            
            response = await self.ai_service.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Check confidence
            if data.get('confidence', 0) < 0.7:
                logger.info(f"Note extraction confidence too low: {data.get('confidence')}")
                return None
            
            logger.info(f"Extracted note data: {data['title']}")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse note extraction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Note extraction failed: {e}")
            return None

    async def extract_mood_data(self, message: str) -> Optional[dict]:
        """Extract mood information from message.
        
        Args:
            message: User message
            
        Returns:
            Mood data dict or None if confidence too low
        """
        if not self.ai_service.available:
            logger.warning("AI service not available for mood extraction")
            return None
        
        try:
            prompt = f"""
Определи настроение из сообщения: "{message}"

Верни JSON:
{{
    "mood": "happy/sad/anxious/calm/excited/tired/stressed/angry/neutral",
    "intensity": 1-10,
    "note": "дополнительная заметка если есть",
    "confidence": 0.0-1.0
}}

Примеры:
"сегодня отличное настроение!" -> {{"mood": "happy", "intensity": 9, "note": null, "confidence": 0.95}}
"устал очень" -> {{"mood": "tired", "intensity": 7, "note": null, "confidence": 0.9}}
"немного тревожно перед встречей" -> {{"mood": "anxious", "intensity": 5, "note": "перед встречей", "confidence": 0.85}}

Верни ТОЛЬКО JSON, без дополнительного текста.
"""
            
            messages = [
                {"role": "system", "text": "Ты - анализатор настроения. Отвечай только JSON."},
                {"role": "user", "text": prompt}
            ]
            
            response = await self.ai_service.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Check confidence
            if data.get('confidence', 0) < 0.7:
                logger.info(f"Mood extraction confidence too low: {data.get('confidence')}")
                return None
            
            logger.info(f"Extracted mood data: {data['mood']} ({data['intensity']}/10)")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse mood extraction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Mood extraction failed: {e}")
            return None
