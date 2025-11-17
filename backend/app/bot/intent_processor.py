"""Intent processor for handling user intents and extracting data."""

import logging
from typing import List, Optional

from app.services.extraction_service import get_extraction_service
from app.services.task_service import get_task_service
from app.services.finance_service import get_finance_service
from app.services.note_service import get_note_service
from app.services.mood_service import get_mood_service

logger = logging.getLogger(__name__)


class IntentProcessor:
    """Processor for handling classified intents and creating entities."""
    
    def __init__(self):
        self.extraction_service = get_extraction_service()
        self.task_service = get_task_service()
        self.finance_service = get_finance_service()
        self.note_service = get_note_service()
        self.mood_service = get_mood_service()
    
    async def process_intents(
        self,
        intents: List[dict],
        message: str,
        user_id: str
    ) -> List[dict]:
        """Process list of intents and create corresponding entities.
        
        Args:
            intents: List of intent dicts with type and confidence
            message: Original user message
            user_id: User ID
            
        Returns:
            List of created entities with metadata
        """
        created_entities = []
        
        for intent in intents:
            intent_type = intent.get("type")
            confidence = intent.get("confidence", 0)
            
            # Skip low confidence intents
            if confidence < 0.7:
                logger.info(f"Skipping intent {intent_type} due to low confidence: {confidence}")
                continue
            
            # Skip general chat
            if intent_type == "general_chat":
                continue
            
            try:
                entity = await self._process_single_intent(
                    intent_type=intent_type,
                    message=message,
                    user_id=user_id
                )
                
                if entity:
                    created_entities.append(entity)
                    
            except Exception as e:
                logger.error(f"Failed to process intent {intent_type}: {e}")
                continue
        
        return created_entities
    
    async def _process_single_intent(
        self,
        intent_type: str,
        message: str,
        user_id: str
    ) -> Optional[dict]:
        """Process single intent and create entity.
        
        Args:
            intent_type: Type of intent
            message: User message
            user_id: User ID
            
        Returns:
            Created entity dict or None
        """
        if intent_type == "create_task":
            return await self._handle_create_task(message, user_id)
        elif intent_type in ["add_expense", "add_income"]:
            return await self._handle_finance(message, user_id)
        elif intent_type == "save_note":
            return await self._handle_save_note(message, user_id)
        elif intent_type == "track_mood":
            return await self._handle_track_mood(message, user_id)
        else:
            logger.warning(f"Unknown intent type: {intent_type}")
            return None


def get_intent_processor() -> IntentProcessor:
    """Get intent processor instance."""
    return IntentProcessor()

    async def _handle_create_task(self, message: str, user_id: str) -> Optional[dict]:
        """Handle task creation intent.
        
        Args:
            message: User message
            user_id: User ID
            
        Returns:
            Created task entity or None
        """
        try:
            # Extract task data
            task_data = await self.extraction_service.extract_task_data(message)
            
            if not task_data:
                logger.info("Task extraction returned no data")
                return None
            
            # Create task
            task = await self.task_service.create(
                user_id=user_id,
                title=task_data['title'],
                description=task_data.get('description'),
                deadline=task_data.get('deadline'),
                priority=task_data.get('priority', 'medium'),
                status='new'
            )
            
            logger.info(f"Created task: {task['title']}")
            
            return {
                "type": "task",
                "data": task,
                "title": task['title'],
                "deadline": task.get('deadline')
            }
            
        except Exception as e:
            logger.error(f"Failed to handle create_task: {e}")
            return None

    async def _handle_finance(self, message: str, user_id: str) -> Optional[dict]:
        """Handle finance (expense/income) intent.
        
        Args:
            message: User message
            user_id: User ID
            
        Returns:
            Created finance entity or None
        """
        try:
            # Extract finance data
            finance_data = await self.extraction_service.extract_finance_data(message)
            
            if not finance_data:
                logger.info("Finance extraction returned no data")
                return None
            
            # Create finance record
            finance = await self.finance_service.create(
                user_id=user_id,
                amount=finance_data['amount'],
                type=finance_data['type'],
                category=finance_data.get('category', 'другое'),
                description=finance_data.get('description')
            )
            
            logger.info(f"Created finance record: {finance['amount']} ({finance['type']})")
            
            return {
                "type": "finance",
                "data": finance,
                "amount": finance['amount'],
                "finance_type": finance['type'],
                "category": finance.get('category')
            }
            
        except Exception as e:
            logger.error(f"Failed to handle finance: {e}")
            return None

    async def _handle_save_note(self, message: str, user_id: str) -> Optional[dict]:
        """Handle save note intent.
        
        Args:
            message: User message
            user_id: User ID
            
        Returns:
            Created note entity or None
        """
        try:
            # Extract note data
            note_data = await self.extraction_service.extract_note_data(message)
            
            if not note_data:
                logger.info("Note extraction returned no data")
                return None
            
            # Create note
            note = await self.note_service.create(
                user_id=user_id,
                title=note_data['title'],
                content=note_data['content']
            )
            
            logger.info(f"Created note: {note['title']}")
            
            return {
                "type": "note",
                "data": note,
                "title": note['title']
            }
            
        except Exception as e:
            logger.error(f"Failed to handle save_note: {e}")
            return None

    async def _handle_track_mood(self, message: str, user_id: str) -> Optional[dict]:
        """Handle track mood intent.
        
        Args:
            message: User message
            user_id: User ID
            
        Returns:
            Created mood entity or None
        """
        try:
            # Extract mood data
            mood_data = await self.extraction_service.extract_mood_data(message)
            
            if not mood_data:
                logger.info("Mood extraction returned no data")
                return None
            
            # Save mood
            mood = await self.mood_service.save_mood(
                user_id=user_id,
                mood=mood_data['mood'],
                intensity=mood_data['intensity'],
                note=mood_data.get('note')
            )
            
            logger.info(f"Saved mood: {mood['mood']} ({mood['intensity']}/10)")
            
            return {
                "type": "mood",
                "data": mood,
                "mood": mood['mood'],
                "intensity": mood['intensity']
            }
            
        except Exception as e:
            logger.error(f"Failed to handle track_mood: {e}")
            return None
