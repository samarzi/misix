"""Unit tests for TaskService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.services.task_service import TaskService


class TestTaskService:
    """Test suite for TaskService."""
    
    @pytest.fixture
    def mock_task_repo(self):
        """Create mock task repository."""
        mock = MagicMock()
        mock.create = AsyncMock()
        mock.get_by_id = AsyncMock()
        mock.get_by_user_id = AsyncMock()
        mock.update = AsyncMock()
        mock.delete = AsyncMock()
        mock.get_by_status = AsyncMock()
        return mock
    
    @pytest.fixture
    def task_service(self, mock_task_repo):
        """Create TaskService with mocked repository."""
        service = TaskService()
        service.task_repo = mock_task_repo
        return service
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, task_service, mock_task_repo):
        """Test successful task creation."""
        # Arrange
        user_id = "user-123"
        title = "Test task"
        mock_task_repo.create.return_value = {
            "id": "task-123",
            "user_id": user_id,
            "title": title,
            "status": "new"
        }
        
        # Act
        result = await task_service.create(
            user_id=user_id,
            title=title
        )
        
        # Assert
        assert result["id"] == "task-123"
        assert result["title"] == title
        mock_task_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_task_with_deadline(self, task_service, mock_task_repo):
        """Test task creation with deadline."""
        # Arrange
        user_id = "user-123"
        title = "Task with deadline"
        deadline = datetime(2025, 11, 18, 10, 0)
        mock_task_repo.create.return_value = {
            "id": "task-123",
            "title": title,
            "deadline": deadline
        }
        
        # Act
        result = await task_service.create(
            user_id=user_id,
            title=title,
            deadline=deadline
        )
        
        # Assert
        assert result["deadline"] == deadline
        call_args = mock_task_repo.create.call_args[0][0]
        assert call_args["deadline"] == deadline
    
    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, task_service, mock_task_repo):
        """Test task creation with priority."""
        # Arrange
        user_id = "user-123"
        title = "High priority task"
        priority = "high"
        mock_task_repo.create.return_value = {
            "id": "task-123",
            "title": title,
            "priority": priority
        }
        
        # Act
        result = await task_service.create(
            user_id=user_id,
            title=title,
            priority=priority
        )
        
        # Assert
        assert result["priority"] == priority
    
    @pytest.mark.asyncio
    async def test_get_by_user(self, task_service, mock_task_repo):
        """Test getting tasks by user."""
        # Arrange
        user_id = "user-123"
        mock_tasks = [
            {"id": "task-1", "title": "Task 1"},
            {"id": "task-2", "title": "Task 2"}
        ]
        mock_task_repo.get_by_user_id.return_value = mock_tasks
        
        # Act
        result = await task_service.get_by_user(user_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "task-1"
        mock_task_repo.get_by_user_id.assert_called_once_with(user_id, limit=None, offset=None)
    
    @pytest.mark.asyncio
    async def test_get_by_user_with_pagination(self, task_service, mock_task_repo):
        """Test getting tasks with pagination."""
        # Arrange
        user_id = "user-123"
        mock_task_repo.get_by_user_id.return_value = []
        
        # Act
        await task_service.get_by_user(user_id, limit=10, offset=20)
        
        # Assert
        mock_task_repo.get_by_user_id.assert_called_once_with(user_id, limit=10, offset=20)
    
    @pytest.mark.asyncio
    async def test_update_task(self, task_service, mock_task_repo):
        """Test updating task."""
        # Arrange
        task_id = "task-123"
        updates = {"status": "completed"}
        mock_task_repo.update.return_value = {
            "id": task_id,
            "status": "completed"
        }
        
        # Act
        result = await task_service.update(task_id, updates)
        
        # Assert
        assert result["status"] == "completed"
        mock_task_repo.update.assert_called_once_with(task_id, updates)
    
    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, mock_task_repo):
        """Test deleting task."""
        # Arrange
        task_id = "task-123"
        mock_task_repo.delete.return_value = True
        
        # Act
        result = await task_service.delete(task_id)
        
        # Assert
        assert result is True
        mock_task_repo.delete.assert_called_once_with(task_id)
    
    @pytest.mark.asyncio
    async def test_get_by_status(self, task_service, mock_task_repo):
        """Test getting tasks by status."""
        # Arrange
        user_id = "user-123"
        status = "completed"
        mock_tasks = [{"id": "task-1", "status": "completed"}]
        mock_task_repo.get_by_status.return_value = mock_tasks
        
        # Act
        result = await task_service.get_by_status(user_id, status)
        
        # Assert
        assert len(result) == 1
        assert result[0]["status"] == "completed"
        mock_task_repo.get_by_status.assert_called_once()
