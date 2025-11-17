"""Response builder for creating confirmation messages."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Builder for creating user-friendly confirmation messages."""
    
    @staticmethod
    def build_confirmation(entities: List[dict]) -> str:
        """Build confirmation message for created entities.
        
        Args:
            entities: List of created entity dicts
            
        Returns:
            Confirmation message string
        """
        if not entities:
            return ""
        
        confirmations = []
        
        for entity in entities:
            entity_type = entity.get("type")
            
            if entity_type == "task":
                conf = ResponseBuilder._build_task_confirmation(entity)
            elif entity_type == "finance":
                conf = ResponseBuilder._build_finance_confirmation(entity)
            elif entity_type == "note":
                conf = ResponseBuilder._build_note_confirmation(entity)
            elif entity_type == "mood":
                conf = ResponseBuilder._build_mood_confirmation(entity)
            else:
                continue
            
            if conf:
                confirmations.append(conf)
        
        return "\n".join(confirmations)
    
    @staticmethod
    def _build_task_confirmation(entity: dict) -> str:
        """Build task confirmation message."""
        title = entity.get("title", "задача")
        deadline = entity.get("deadline")
        
        if deadline:
            return f"✅ Создал задачу: {title} (до {deadline.strftime('%d.%m.%Y')})"
        else:
            return f"✅ Создал задачу: {title}"
    
    @staticmethod
    def _build_finance_confirmation(entity: dict) -> str:
        """Build finance confirmation message."""
        amount = entity.get("amount", 0)
        finance_type = entity.get("finance_type", "expense")
        category = entity.get("category", "")
        
        if finance_type == "expense":
            emoji = "💸"
            action = "Записал расход"
        else:
            emoji = "💰"
            action = "Записал доход"
        
        if category:
            return f"{emoji} {action}: {amount}₽ ({category})"
        else:
            return f"{emoji} {action}: {amount}₽"
    
    @staticmethod
    def _build_note_confirmation(entity: dict) -> str:
        """Build note confirmation message."""
        title = entity.get("title", "заметка")
        return f"📝 Сохранил заметку: {title}"
    
    @staticmethod
    def _build_mood_confirmation(entity: dict) -> str:
        """Build mood confirmation message."""
        mood = entity.get("mood", "")
        intensity = entity.get("intensity", 5)
        
        # Map mood to emoji
        mood_emojis = {
            "happy": "😊",
            "sad": "😢",
            "anxious": "😰",
            "calm": "😌",
            "excited": "🤩",
            "tired": "😴",
            "stressed": "😫",
            "angry": "😠",
            "neutral": "😐"
        }
        
        emoji = mood_emojis.get(mood, "😊")
        
        # Translate mood to Russian
        mood_translations = {
            "happy": "хорошее настроение",
            "sad": "грустное настроение",
            "anxious": "тревожное состояние",
            "calm": "спокойное состояние",
            "excited": "возбужденное состояние",
            "tired": "усталость",
            "stressed": "стресс",
            "angry": "злость",
            "neutral": "нейтральное настроение"
        }
        
        mood_ru = mood_translations.get(mood, mood)
        
        return f"{emoji} Отметил {mood_ru} (интенсивность: {intensity}/10)"


def get_response_builder() -> ResponseBuilder:
    """Get response builder instance."""
    return ResponseBuilder()
