"""Unit tests for AIService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_service import AIService


class TestAIService:
    """Test suite for AIService."""
    
    @pytest.fixture
    def mock_gpt_client(self):
        """Create mock Yandex GPT client."""
        mock = AsyncMock()
        mock.chat = AsyncMock()
        return mock
    
    @pytest.fixture
    def ai_service(self, mock_gpt_client):
        """Create AIService with mocked GPT client."""
        service = AIService(gpt_client=mock_gpt_client)
        service.available = True
        return service
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service, mock_gpt_client):
        """Test successful response generation."""
        # Arrange
        user_message = "Привет!"
        mock_gpt_client.chat.return_value = "Привет! Как дела?"
        
        # Act
        result = await ai_service.generate_response(user_message)
        
        # Assert
        assert result == "Привет! Как дела?"
        mock_gpt_client.chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, ai_service, mock_gpt_client):
        """Test response generation with conversation context."""
        # Arrange
        user_message = "А что дальше?"
        context = "Пользователь спрашивал о задачах"
        mock_gpt_client.chat.return_value = "Давайте продолжим с задачами"
        
        # Act
        result = await ai_service.generate_response(
            user_message,
            conversation_context=context
        )
        
        # Assert
        assert "Давайте продолжим" in result
        # Check that context was included in messages
        call_args = mock_gpt_client.chat.call_args
        messages = call_args.kwargs.get("messages", [])
        assert any("Context" in msg.get("text", "") for msg in messages)
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, ai_service, mock_gpt_client):
        """Test response generation with custom system prompt."""
        # Arrange
        user_message = "test"
        system_prompt = "Ты - строгий учитель"
        mock_gpt_client.chat.return_value = "Ответ"
        
        # Act
        result = await ai_service.generate_response(
            user_message,
            system_prompt=system_prompt
        )
        
        # Assert
        call_args = mock_gpt_client.chat.call_args
        messages = call_args.kwargs.get("messages", [])
        assert any("строгий учитель" in msg.get("text", "") for msg in messages)
    
    @pytest.mark.asyncio
    async def test_classify_intent_single(self, ai_service, mock_gpt_client):
        """Test intent classification for single intent."""
        # Arrange
        message = "напомни купить молоко"
        mock_response = '{"intents": [{"type": "create_task", "confidence": 0.95}]}'
        mock_gpt_client.chat.return_value = mock_response
        
        # Act
        result = await ai_service.classify_intent(message)
        
        # Assert
        assert "intents" in result
        assert len(result["intents"]) == 1
        assert result["intents"][0]["type"] == "create_task"
        assert result["intents"][0]["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_intent_multiple(self, ai_service, mock_gpt_client):
        """Test intent classification for multiple intents."""
        # Arrange
        message = "потратил 200₽ и напомни купить молоко"
        mock_response = '''{"intents": [
            {"type": "add_expense", "confidence": 0.95},
            {"type": "create_task", "confidence": 0.9}
        ]}'''
        mock_gpt_client.chat.return_value = mock_response
        
        # Act
        result = await ai_service.classify_intent(message)
        
        # Assert
        assert len(result["intents"]) == 2
        # Should be sorted by confidence (descending)
        assert result["intents"][0]["confidence"] >= result["intents"][1]["confidence"]
    
    @pytest.mark.asyncio
    async def test_classify_intent_invalid_json(self, ai_service, mock_gpt_client):
        """Test intent classification with invalid JSON response."""
        # Arrange
        message = "test"
        mock_gpt_client.chat.return_value = "invalid json {"
        
        # Act
        result = await ai_service.classify_intent(message)
        
        # Assert
        assert result == {"intents": []}
    
    @pytest.mark.asyncio
    async def test_classify_intent_unavailable(self):
        """Test intent classification when AI is unavailable."""
        # Arrange
        service = AIService()
        service.available = False
        
        # Act
        result = await service.classify_intent("test")
        
        # Assert
        assert result == {"intents": []}
    
    @pytest.mark.asyncio
    async def test_extract_structured_data_task(self, ai_service, mock_gpt_client):
        """Test structured data extraction for task."""
        # Arrange
        message = "напомни завтра позвонить"
        mock_response = '{"title": "позвонить", "deadline": "tomorrow", "priority": "medium"}'
        mock_gpt_client.chat.return_value = mock_response
        
        # Act
        result = await ai_service.extract_structured_data(message, "task")
        
        # Assert
        assert result is not None
        assert result["title"] == "позвонить"
        assert result["deadline"] == "tomorrow"
    
    @pytest.mark.asyncio
    async def test_extract_structured_data_expense(self, ai_service, mock_gpt_client):
        """Test structured data extraction for expense."""
        # Arrange
        message = "потратил 500₽ на кофе"
        mock_response = '{"amount": 500, "category": "еда и напитки", "description": "кофе"}'
        mock_gpt_client.chat.return_value = mock_response
        
        # Act
        result = await ai_service.extract_structured_data(message, "expense")
        
        # Assert
        assert result is not None
        assert result["amount"] == 500
        assert result["category"] == "еда и напитки"
    
    @pytest.mark.asyncio
    async def test_extract_structured_data_invalid_type(self, ai_service, mock_gpt_client):
        """Test structured data extraction with invalid type."""
        # Arrange
        message = "test"
        
        # Act
        result = await ai_service.extract_structured_data(message, "invalid_type")
        
        # Assert
        assert result is None
        mock_gpt_client.chat.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fallback_response_greeting(self):
        """Test fallback response for greeting."""
        # Arrange
        service = AIService()
        service.available = False
        
        # Act
        result = await service.generate_response("Привет!")
        
        # Assert
        assert "Привет" in result or "👋" in result
    
    @pytest.mark.asyncio
    async def test_fallback_response_thanks(self):
        """Test fallback response for thanks."""
        # Arrange
        service = AIService()
        service.available = False
        
        # Act
        result = await service.generate_response("Спасибо!")
        
        # Assert
        assert "Пожалуйста" in result or "😊" in result
    
    @pytest.mark.asyncio
    async def test_fallback_response_help(self):
        """Test fallback response for help request."""
        # Arrange
        service = AIService()
        service.available = False
        
        # Act
        result = await service.generate_response("Помощь")
        
        # Assert
        assert "задач" in result.lower() or "финанс" in result.lower()
    
    def test_get_default_system_prompt(self, ai_service):
        """Test default system prompt generation."""
        # Act
        prompt = ai_service._get_default_system_prompt()
        
        # Assert
        assert "MISIX" in prompt
        assert "ассистент" in prompt.lower()
        assert "задач" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, ai_service, mock_gpt_client):
        """Test error handling in response generation."""
        # Arrange
        user_message = "test"
        mock_gpt_client.chat.side_effect = Exception("API Error")
        
        # Act
        result = await ai_service.generate_response(user_message)
        
        # Assert
        # Should return fallback response instead of raising
        assert isinstance(result, str)
        assert len(result) > 0
