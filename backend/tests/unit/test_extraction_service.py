"""Unit tests for ExtractionService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.extraction_service import ExtractionService


class TestExtractionService:
    """Test suite for ExtractionService."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service."""
        mock = MagicMock()
        mock.available = True
        mock.gpt_client = AsyncMock()
        return mock
    
    @pytest.fixture
    def extraction_service(self, mock_ai_service):
        """Create ExtractionService with mocked AI service."""
        return ExtractionService(ai_service=mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_extract_task_data_success(self, extraction_service, mock_ai_service):
        """Test successful task data extraction."""
        # Arrange
        message = "напомни завтра купить молоко"
        mock_response = '{"title": "купить молоко", "deadline": "tomorrow", "priority": "medium", "confidence": 0.95}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_task_data(message)
        
        # Assert
        assert result is not None
        assert result["title"] == "купить молоко"
        assert result["priority"] == "medium"
        assert result["deadline"] is not None  # Should be parsed
        mock_ai_service.gpt_client.chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_task_data_low_confidence(self, extraction_service, mock_ai_service):
        """Test task extraction with low confidence."""
        # Arrange
        message = "привет"
        mock_response = '{"title": "привет", "deadline": null, "priority": "medium", "confidence": 0.3}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_task_data(message)
        
        # Assert
        assert result is None  # Should be filtered out due to low confidence
    
    @pytest.mark.asyncio
    async def test_extract_finance_data_expense(self, extraction_service, mock_ai_service):
        """Test finance data extraction for expense."""
        # Arrange
        message = "потратил 500₽ на кофе"
        mock_response = '{"amount": 500, "type": "expense", "category": "еда и напитки", "description": "кофе", "confidence": 0.95}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_finance_data(message)
        
        # Assert
        assert result is not None
        assert result["amount"] == 500
        assert result["type"] == "expense"
        assert result["category"] == "еда и напитки"
    
    @pytest.mark.asyncio
    async def test_extract_finance_data_income(self, extraction_service, mock_ai_service):
        """Test finance data extraction for income."""
        # Arrange
        message = "заработал 50000 рублей"
        mock_response = '{"amount": 50000, "type": "income", "category": "другое", "description": "доход", "confidence": 0.9}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_finance_data(message)
        
        # Assert
        assert result is not None
        assert result["amount"] == 50000
        assert result["type"] == "income"
    
    @pytest.mark.asyncio
    async def test_extract_note_data(self, extraction_service, mock_ai_service):
        """Test note data extraction."""
        # Arrange
        message = "запомни что встреча в офисе на Ленина 5"
        mock_response = '{"title": "Встреча в офисе", "content": "встреча в офисе на Ленина 5", "confidence": 0.9}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_note_data(message)
        
        # Assert
        assert result is not None
        assert result["title"] == "Встреча в офисе"
        assert "Ленина 5" in result["content"]
    
    @pytest.mark.asyncio
    async def test_extract_mood_data(self, extraction_service, mock_ai_service):
        """Test mood data extraction."""
        # Arrange
        message = "сегодня отличное настроение!"
        mock_response = '{"mood": "happy", "intensity": 9, "note": null, "confidence": 0.95}'
        mock_ai_service.gpt_client.chat.return_value = mock_response
        
        # Act
        result = await extraction_service.extract_mood_data(message)
        
        # Assert
        assert result is not None
        assert result["mood"] == "happy"
        assert result["intensity"] == 9
    
    @pytest.mark.asyncio
    async def test_extraction_with_ai_unavailable(self, mock_ai_service):
        """Test extraction when AI service is unavailable."""
        # Arrange
        mock_ai_service.available = False
        extraction_service = ExtractionService(ai_service=mock_ai_service)
        
        # Act
        result = await extraction_service.extract_task_data("test message")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_extraction_with_invalid_json(self, extraction_service, mock_ai_service):
        """Test extraction with invalid JSON response."""
        # Arrange
        message = "test"
        mock_ai_service.gpt_client.chat.return_value = "invalid json {"
        
        # Act
        result = await extraction_service.extract_task_data(message)
        
        # Assert
        assert result is None
    
    def test_parse_deadline_tomorrow(self, extraction_service):
        """Test parsing 'tomorrow' deadline."""
        # Act
        result = extraction_service._parse_deadline("tomorrow")
        
        # Assert
        assert result is not None
        # Should be tomorrow's date
    
    def test_parse_deadline_today(self, extraction_service):
        """Test parsing 'today' deadline."""
        # Act
        result = extraction_service._parse_deadline("today")
        
        # Assert
        assert result is not None
        # Should be today's date
    
    def test_parse_deadline_relative_days(self, extraction_service):
        """Test parsing relative days deadline."""
        # Act
        result = extraction_service._parse_deadline("через 2 дня")
        
        # Assert
        assert result is not None
        # Should be 2 days from now
    
    def test_parse_deadline_null(self, extraction_service):
        """Test parsing null deadline."""
        # Act
        result = extraction_service._parse_deadline("null")
        
        # Assert
        assert result is None
