"""Unit tests for IntentProcessor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.intent_processor import IntentProcessor


class TestIntentProcessor:
    """Test suite for IntentProcessor."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "extraction": AsyncMock(),
            "task": AsyncMock(),
            "finance": AsyncMock(),
            "note": AsyncMock(),
            "mood": AsyncMock()
        }
    
    @pytest.fixture
    def intent_processor(self, mock_services):
        """Create IntentProcessor with mocked services."""
        processor = IntentProcessor()
        processor.extraction_service = mock_services["extraction"]
        processor.task_service = mock_services["task"]
        processor.finance_service = mock_services["finance"]
        processor.note_service = mock_services["note"]
        processor.mood_service = mock_services["mood"]
        return processor
    
    @pytest.mark.asyncio
    async def test_process_single_task_intent(self, intent_processor, mock_services):
        """Test processing single task intent."""
        # Arrange
        intents = [{"type": "create_task", "confidence": 0.95}]
        message = "напомни купить молоко"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_task_data.return_value = {
            "title": "купить молоко",
            "deadline": None,
            "priority": "medium"
        }
        mock_services["task"].create.return_value = {
            "id": "task-id",
            "title": "купить молоко",
            "status": "new"
        }
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "task"
        mock_services["extraction"].extract_task_data.assert_called_once_with(message)
        mock_services["task"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_multiple_intents(self, intent_processor, mock_services):
        """Test processing multiple intents in one message."""
        # Arrange
        intents = [
            {"type": "add_expense", "confidence": 0.95},
            {"type": "create_task", "confidence": 0.9}
        ]
        message = "потратил 200₽ на такси и напомни купить молоко"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_finance_data.return_value = {
            "amount": 200,
            "type": "expense",
            "category": "транспорт"
        }
        mock_services["extraction"].extract_task_data.return_value = {
            "title": "купить молоко",
            "deadline": None,
            "priority": "medium"
        }
        mock_services["finance"].create.return_value = {
            "id": "finance-id",
            "amount": 200,
            "type": "expense"
        }
        mock_services["task"].create.return_value = {
            "id": "task-id",
            "title": "купить молоко"
        }
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]["type"] == "finance"
        assert result[1]["type"] == "task"
    
    @pytest.mark.asyncio
    async def test_filter_low_confidence_intents(self, intent_processor, mock_services):
        """Test that low confidence intents are filtered out."""
        # Arrange
        intents = [
            {"type": "create_task", "confidence": 0.5},  # Too low
            {"type": "add_expense", "confidence": 0.95}  # OK
        ]
        message = "test message"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_finance_data.return_value = {
            "amount": 100,
            "type": "expense",
            "category": "другое"
        }
        mock_services["finance"].create.return_value = {"id": "finance-id"}
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 1  # Only expense, task filtered out
        assert result[0]["type"] == "finance"
        mock_services["extraction"].extract_task_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_skip_general_chat_intent(self, intent_processor, mock_services):
        """Test that general_chat intent is skipped."""
        # Arrange
        intents = [{"type": "general_chat", "confidence": 0.95}]
        message = "привет"
        user_id = "test-user-id"
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 0
        # No extraction services should be called
        mock_services["extraction"].extract_task_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_extraction_failure(self, intent_processor, mock_services):
        """Test handling when extraction returns None."""
        # Arrange
        intents = [{"type": "create_task", "confidence": 0.95}]
        message = "test"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_task_data.return_value = None
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 0
        mock_services["task"].create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_service_error(self, intent_processor, mock_services):
        """Test handling when service raises exception."""
        # Arrange
        intents = [{"type": "create_task", "confidence": 0.95}]
        message = "test"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_task_data.return_value = {
            "title": "test",
            "deadline": None,
            "priority": "medium"
        }
        mock_services["task"].create.side_effect = Exception("Database error")
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 0  # Error should be caught and logged
    
    @pytest.mark.asyncio
    async def test_process_mood_intent(self, intent_processor, mock_services):
        """Test processing mood tracking intent."""
        # Arrange
        intents = [{"type": "track_mood", "confidence": 0.95}]
        message = "сегодня отличное настроение"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_mood_data.return_value = {
            "mood": "happy",
            "intensity": 9,
            "note": None
        }
        mock_services["mood"].save_mood.return_value = {
            "id": "mood-id",
            "mood": "happy",
            "intensity": 9
        }
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "mood"
        mock_services["mood"].save_mood.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_note_intent(self, intent_processor, mock_services):
        """Test processing save note intent."""
        # Arrange
        intents = [{"type": "save_note", "confidence": 0.9}]
        message = "запомни встреча завтра"
        user_id = "test-user-id"
        
        mock_services["extraction"].extract_note_data.return_value = {
            "title": "Встреча",
            "content": "встреча завтра"
        }
        mock_services["note"].create.return_value = {
            "id": "note-id",
            "title": "Встреча"
        }
        
        # Act
        result = await intent_processor.process_intents(intents, message, user_id)
        
        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "note"
