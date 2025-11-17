"""AI service for Yandex GPT integration."""

import logging
from typing import Optional

from app.bot.yandex_gpt import YandexGPTClient, YandexGPTConfigurationError, get_yandex_gpt_client
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

# Fallback responses when AI is unavailable
FALLBACK_RESPONSES = [
    "Извините, сейчас я не могу обработать ваш запрос. Попробуйте позже.",
    "Временные технические неполадки. Пожалуйста, повторите запрос через минуту.",
    "Не удалось получить ответ от AI. Проверьте подключение и попробуйте снова.",
]


class AIService:
    """Service for AI-powered responses and text processing."""
    
    def __init__(self, gpt_client: Optional[YandexGPTClient] = None):
        """Initialize AI service.
        
        Args:
            gpt_client: Yandex GPT client (injected for testing)
        """
        try:
            self.gpt_client = gpt_client or get_yandex_gpt_client()
            self.available = True
        except YandexGPTConfigurationError as e:
            logger.warning(f"Yandex GPT not configured: {e}")
            self.gpt_client = None
            self.available = False
    
    async def generate_response(
        self,
        user_message: str,
        conversation_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate AI response to user message.
        
        Args:
            user_message: User's message
            conversation_context: Optional conversation history
            system_prompt: Optional system prompt (persona)
            
        Returns:
            AI-generated response
            
        Raises:
            ExternalServiceError: If AI service fails
        """
        if not self.available or not self.gpt_client:
            return self._get_fallback_response(user_message)
        
        try:
            # Build messages for AI
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({
                    "role": "system",
                    "text": system_prompt,
                })
            else:
                messages.append({
                    "role": "system",
                    "text": self._get_default_system_prompt(),
                })
            
            # Add conversation context if available
            if conversation_context:
                messages.append({
                    "role": "system",
                    "text": f"Context from previous conversation:\n{conversation_context}",
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "text": user_message,
            })
            
            # Get response from Yandex GPT
            response = await self.gpt_client.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            
            logger.info(f"Generated AI response (length: {len(response)})")
            return response
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._get_fallback_response(user_message)
    
    async def classify_intent(self, user_message: str) -> dict:
        """Classify user intent(s) from message.
        
        Can detect multiple intents in one message.
        
        Args:
            user_message: User's message
            
        Returns:
            Dictionary with list of intents: {"intents": [{"type": "...", "confidence": 0.0-1.0}]}
        """
        if not self.available or not self.gpt_client:
            return {"intents": []}
        
        try:
            prompt = f"""
Проанализируй сообщение и определи ВСЕ намерения пользователя:
"{user_message}"

Возможные намерения:
- create_task: хочет создать задачу или напоминание
- add_expense: сообщает о расходе
- add_income: сообщает о доходе
- save_note: хочет сохранить информацию/заметку
- track_mood: выражает настроение или эмоцию
- general_chat: просто общается

Верни JSON:
{{
    "intents": [
        {{"type": "create_task", "confidence": 0.95}},
        {{"type": "add_expense", "confidence": 0.85}}
    ]
}}

Примеры:
"потратил 200₽ на такси и напомни купить молоко" -> {{"intents": [{{"type": "add_expense", "confidence": 0.95}}, {{"type": "create_task", "confidence": 0.9}}]}}
"сегодня отличное настроение!" -> {{"intents": [{{"type": "track_mood", "confidence": 0.95}}]}}
"как дела?" -> {{"intents": [{{"type": "general_chat", "confidence": 0.95}}]}}

Верни ТОЛЬКО JSON, без дополнительного текста.
"""
            
            messages = [
                {"role": "system", "text": "Ты - классификатор намерений. Отвечай только JSON."},
                {"role": "user", "text": prompt},
            ]
            
            response = await self.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200,
            )
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.strip())
                # Sort by confidence
                if "intents" in result:
                    result["intents"] = sorted(
                        result["intents"],
                        key=lambda x: x.get("confidence", 0),
                        reverse=True
                    )
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent classification: {response}")
                return {"intents": []}
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {"intents": []}
    
    async def extract_structured_data(
        self,
        user_message: str,
        data_type: str,
    ) -> Optional[dict]:
        """Extract structured data from user message.
        
        Args:
            user_message: User's message
            data_type: Type of data to extract (task, expense, note)
            
        Returns:
            Extracted data or None
        """
        if not self.available or not self.gpt_client:
            return None
        
        try:
            prompts = {
                "task": """
Extract task information from this message:
"{message}"

Respond with JSON: {{"title": "...", "deadline": "YYYY-MM-DD or null", "priority": "low/medium/high"}}
""",
                "expense": """
Extract expense information from this message:
"{message}"

Respond with JSON: {{"amount": 0.0, "category": "...", "description": "..."}}
""",
                "note": """
Extract note information from this message:
"{message}"

Respond with JSON: {{"title": "...", "content": "..."}}
""",
            }
            
            if data_type not in prompts:
                return None
            
            prompt = prompts[data_type].format(message=user_message)
            
            messages = [
                {"role": "system", "text": "You are a data extractor. Respond only with JSON."},
                {"role": "user", "text": prompt},
            ]
            
            response = await self.gpt_client.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=200,
            )
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse extracted data: {response}")
                return None
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return None
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for AI.
        
        Returns:
            System prompt text
        """
        return """
Ты - MISIX, персональный AI-ассистент пользователя.

Твоя задача:
- Помогать пользователю управлять задачами, финансами и заметками
- Отвечать дружелюбно и по существу
- Быть кратким, но информативным
- Использовать эмодзи для наглядности

Ты можешь:
- Создавать задачи и напоминания
- Записывать расходы и доходы
- Сохранять заметки
- Отвечать на вопросы
- Вести дружескую беседу

Отвечай на русском языке.
"""
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Get fallback response when AI is unavailable.
        
        Args:
            user_message: User's message
            
        Returns:
            Fallback response
        """
        # Simple keyword-based responses
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["привет", "здравствуй", "hi", "hello"]):
            return "Привет! 👋 Как я могу помочь?"
        
        if any(word in message_lower for word in ["спасибо", "благодарю", "thanks"]):
            return "Пожалуйста! Рад помочь! 😊"
        
        if any(word in message_lower for word in ["помощь", "help", "что ты умеешь"]):
            return """
Я могу помочь вам с:
📝 Задачами и напоминаниями
💰 Финансами и расходами
📓 Заметками и записями

Просто напишите, что вам нужно!
"""
        
        # Default fallback
        import random
        return random.choice(FALLBACK_RESPONSES)


def get_ai_service() -> AIService:
    """Get AI service instance."""
    return AIService()
