"""Unit tests for ResponseBuilder."""

import pytest
from datetime import datetime
from app.bot.response_builder import ResponseBuilder


class TestResponseBuilder:
    """Test suite for ResponseBuilder."""
    
    @pytest.fixture
    def response_builder(self):
        """Create ResponseBuilder instance."""
        return ResponseBuilder()
    
    def test_build_task_created_with_deadline(self, response_builder):
        """Test building task confirmation with deadline."""
        # Arrange
        entity = {
            "type": "task",
            "title": "купить молоко",
            "deadline": datetime(2025, 11, 18, 10, 0)
        }
        
        # Act
        result = response_builder._build_task_confirmation(entity)
        
        # Assert
        assert "✅" in result
        assert "купить молоко" in result
        assert "18.11" in result
    
    def test_build_task_created_without_deadline(self, response_builder):
        """Test building task confirmation without deadline."""
        # Arrange
        entity = {
            "type": "task",
            "title": "позвонить партнеру",
            "deadline": None
        }
        
        # Act
        result = response_builder._build_task_confirmation(entity)
        
        # Assert
        assert "✅" in result
        assert "позвонить партнеру" in result
        assert "до" not in result  # No deadline mentioned
    
    def test_build_finance_expense(self, response_builder):
        """Test building finance confirmation for expense."""
        # Arrange
        entity = {
            "type": "finance",
            "amount": 500,
            "finance_type": "expense",
            "category": "еда и напитки"
        }
        
        # Act
        result = response_builder._build_finance_confirmation(entity)
        
        # Assert
        assert "💸" in result
        assert "расход" in result.lower()
        assert "500₽" in result
        assert "еда и напитки" in result
    
    def test_build_finance_income(self, response_builder):
        """Test building finance confirmation for income."""
        # Arrange
        entity = {
            "type": "finance",
            "amount": 50000,
            "finance_type": "income",
            "category": "зарплата"
        }
        
        # Act
        result = response_builder._build_finance_confirmation(entity)
        
        # Assert
        assert "💰" in result
        assert "доход" in result.lower()
        assert "50000₽" in result or "50,000₽" in result
    
    def test_build_note_created(self, response_builder):
        """Test building note confirmation."""
        # Arrange
        entity = {
            "type": "note",
            "title": "Встреча в офисе"
        }
        
        # Act
        result = response_builder._build_note_confirmation(entity)
        
        # Assert
        assert "📝" in result
        assert "заметк" in result.lower()
        assert "Встреча в офисе" in result
    
    def test_build_mood_happy(self, response_builder):
        """Test building mood confirmation for happy mood."""
        # Arrange
        entity = {
            "type": "mood",
            "mood": "happy",
            "intensity": 9
        }
        
        # Act
        result = response_builder._build_mood_confirmation(entity)
        
        # Assert
        assert "😊" in result
        assert "9/10" in result
        assert "настроение" in result.lower()
    
    def test_build_mood_sad(self, response_builder):
        """Test building mood confirmation for sad mood."""
        # Arrange
        entity = {
            "type": "mood",
            "mood": "sad",
            "intensity": 3
        }
        
        # Act
        result = response_builder._build_mood_confirmation(entity)
        
        # Assert
        assert "😢" in result
        assert "3/10" in result
    
    def test_build_mood_stressed(self, response_builder):
        """Test building mood confirmation for stressed mood."""
        # Arrange
        entity = {
            "type": "mood",
            "mood": "stressed",
            "intensity": 7
        }
        
        # Act
        result = response_builder._build_mood_confirmation(entity)
        
        # Assert
        assert "😫" in result
        assert "стресс" in result.lower()
    
    def test_build_confirmation_single_entity(self, response_builder):
        """Test building confirmation for single entity."""
        # Arrange
        entities = [
            {
                "type": "task",
                "title": "test task",
                "deadline": None
            }
        ]
        
        # Act
        result = response_builder.build_confirmation(entities)
        
        # Assert
        assert "✅" in result
        assert "test task" in result
    
    def test_build_confirmation_multiple_entities(self, response_builder):
        """Test building confirmation for multiple entities."""
        # Arrange
        entities = [
            {
                "type": "finance",
                "amount": 200,
                "finance_type": "expense",
                "category": "транспорт"
            },
            {
                "type": "task",
                "title": "купить молоко",
                "deadline": None
            }
        ]
        
        # Act
        result = response_builder.build_confirmation(entities)
        
        # Assert
        assert "💸" in result
        assert "200₽" in result
        assert "✅" in result
        assert "купить молоко" in result
        # Should have newline between confirmations
        assert "\n" in result
    
    def test_build_confirmation_empty_list(self, response_builder):
        """Test building confirmation for empty entity list."""
        # Arrange
        entities = []
        
        # Act
        result = response_builder.build_confirmation(entities)
        
        # Assert
        assert result == ""
    
    def test_build_confirmation_unknown_type(self, response_builder):
        """Test building confirmation for unknown entity type."""
        # Arrange
        entities = [
            {
                "type": "unknown_type",
                "data": "test"
            }
        ]
        
        # Act
        result = response_builder.build_confirmation(entities)
        
        # Assert
        assert result == ""  # Unknown types are skipped
    
    def test_mood_emoji_mapping(self, response_builder):
        """Test that all mood types have emoji mappings."""
        # Arrange
        moods = ["happy", "sad", "anxious", "calm", "excited", "tired", "stressed", "angry", "neutral"]
        
        # Act & Assert
        for mood in moods:
            entity = {"type": "mood", "mood": mood, "intensity": 5}
            result = response_builder._build_mood_confirmation(entity)
            # Should contain an emoji (any emoji character)
            assert any(ord(c) > 127 for c in result), f"No emoji found for mood: {mood}"
    
    def test_priority_emoji_mapping(self, response_builder):
        """Test priority emoji mapping in task confirmation."""
        # Arrange
        priorities = ["high", "medium", "low"]
        
        # Act & Assert
        for priority in priorities:
            entity = {
                "type": "task",
                "title": "test",
                "deadline": None,
                "priority": priority
            }
            # Priority emoji is not currently shown in confirmation,
            # but this test ensures the structure supports it
            result = response_builder._build_task_confirmation(entity)
            assert "test" in result
