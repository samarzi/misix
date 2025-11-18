"""Property-based and unit tests for WebhookManager.

Feature: telegram-webhook-fix
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck
from telegram import Update
from telegram.ext import Application

from app.bot.webhook import WebhookManager, WebhookInfo, WebhookSetupResult


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.token = "test_token"
    return bot


@pytest.fixture
def mock_application(mock_bot):
    """Create a mock Telegram application."""
    app = MagicMock(spec=Application)
    app.bot = mock_bot
    return app


@pytest.fixture
def webhook_manager(mock_application):
    """Create a WebhookManager instance with mocked application."""
    return WebhookManager(mock_application)


# ============================================================================
# Property 1: Webhook установка в production
# Feature: telegram-webhook-fix, Property 1: Webhook установка в production
# Validates: Requirements 1.1, 3.1, 3.5
# ============================================================================

# Strategy for valid HTTPS URLs
valid_https_urls = st.builds(
    lambda domain, path: f"https://{domain}{path}",
    domain=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), min_codepoint=97, max_codepoint=122),
        min_size=5,
        max_size=20
    ).filter(lambda x: x not in ["localhost", "example"] and "127.0.0.1" not in x),
    path=st.sampled_from(["/bot/webhook", "/webhook", "/api/telegram"])
)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(webhook_url=valid_https_urls)
@pytest.mark.asyncio
async def test_property_webhook_setup_in_production(webhook_url, mock_application):
    """Property 1: For any production environment with valid HTTPS webhook URL,
    after application startup, the webhook SHALL be registered in Telegram API with that URL.
    
    Feature: telegram-webhook-fix, Property 1
    Validates: Requirements 1.1, 3.1, 3.5
    """
    # Arrange
    manager = WebhookManager(mock_application)
    
    # Mock successful webhook setup
    mock_application.bot.set_webhook = AsyncMock(return_value=True)
    
    # Mock webhook info to verify setup
    mock_webhook_info = MagicMock()
    mock_webhook_info.url = webhook_url
    mock_webhook_info.has_custom_certificate = False
    mock_webhook_info.pending_update_count = 0
    mock_webhook_info.last_error_date = None
    mock_webhook_info.last_error_message = None
    mock_webhook_info.max_connections = 40
    mock_webhook_info.allowed_updates = None
    
    mock_application.bot.get_webhook_info = AsyncMock(return_value=mock_webhook_info)
    mock_application.bot.get_updates = AsyncMock(return_value=[])
    
    # Act
    result = await manager.set_webhook(webhook_url)
    
    # Assert
    assert result.success, f"Webhook setup should succeed for valid URL: {webhook_url}"
    assert result.webhook_url == webhook_url
    assert manager.is_set, "Manager should mark webhook as set"
    assert manager.webhook_url == webhook_url, "Manager should store webhook URL"
    
    # Verify Telegram API was called
    mock_application.bot.set_webhook.assert_called_once()
    call_args = mock_application.bot.set_webhook.call_args
    assert call_args.kwargs["url"] == webhook_url


# ============================================================================
# Property 4: Устойчивость к ошибкам обработки
# Feature: telegram-webhook-fix, Property 4: Устойчивость к ошибкам обработки
# Validates: Requirements 4.3
# ============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_updates=st.integers(min_value=1, max_value=20),
    failing_indices=st.lists(st.integers(min_value=0, max_value=19), max_size=10, unique=True)
)
@pytest.mark.asyncio
async def test_property_error_resilience_in_update_processing(
    num_updates,
    failing_indices,
    mock_application
):
    """Property 4: For any update that fails to process, the system SHALL log the error
    and continue processing remaining updates without stopping.
    
    Feature: telegram-webhook-fix, Property 4
    Validates: Requirements 4.3
    """
    # Arrange
    manager = WebhookManager(mock_application)
    
    # Create mock updates
    mock_updates = []
    for i in range(num_updates):
        update = MagicMock(spec=Update)
        update.update_id = i + 1
        mock_updates.append(update)
    
    # Mock get_updates to return our updates
    mock_application.bot.get_updates = AsyncMock(side_effect=[
        mock_updates,  # First call returns updates
        []  # Second call (acknowledgment) returns empty
    ])
    
    # Mock process_update to fail for specific indices
    async def mock_process_update(update):
        if update.update_id - 1 in failing_indices:
            raise Exception(f"Simulated error for update {update.update_id}")
    
    mock_application.process_update = AsyncMock(side_effect=mock_process_update)
    
    # Act
    processed_count = await manager.process_pending_updates()
    
    # Assert
    expected_successful = num_updates - len([i for i in failing_indices if i < num_updates])
    assert processed_count == expected_successful, (
        f"Should process {expected_successful} updates successfully "
        f"(total: {num_updates}, failing: {len([i for i in failing_indices if i < num_updates])})"
    )
    
    # Verify all updates were attempted
    assert mock_application.process_update.call_count == num_updates, (
        "Should attempt to process all updates despite errors"
    )


# ============================================================================
# Unit Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_webhook_info_success(webhook_manager, mock_bot):
    """Test successful webhook info retrieval."""
    # Arrange
    mock_info = MagicMock()
    mock_info.url = "https://example.com/webhook"
    mock_info.has_custom_certificate = False
    mock_info.pending_update_count = 5
    mock_info.last_error_date = None
    mock_info.last_error_message = None
    mock_info.max_connections = 40
    mock_info.allowed_updates = None
    
    mock_bot.get_webhook_info = AsyncMock(return_value=mock_info)
    
    # Act
    result = await webhook_manager.get_webhook_info()
    
    # Assert
    assert result is not None
    assert isinstance(result, WebhookInfo)
    assert result.url == "https://example.com/webhook"
    assert result.pending_update_count == 5


@pytest.mark.asyncio
async def test_get_webhook_info_no_webhook_set(webhook_manager, mock_bot):
    """Test webhook info when no webhook is set."""
    # Arrange
    mock_info = MagicMock()
    mock_info.url = ""
    mock_info.has_custom_certificate = False
    mock_info.pending_update_count = 0
    mock_info.last_error_date = None
    mock_info.last_error_message = None
    mock_info.max_connections = None
    mock_info.allowed_updates = None
    
    mock_bot.get_webhook_info = AsyncMock(return_value=mock_info)
    
    # Act
    result = await webhook_manager.get_webhook_info()
    
    # Assert
    assert result is not None
    assert result.url == ""
    assert result.pending_update_count == 0


@pytest.mark.asyncio
async def test_set_webhook_invalid_url_empty(webhook_manager):
    """Test webhook setup with empty URL."""
    # Act
    result = await webhook_manager.set_webhook("")
    
    # Assert
    assert not result.success
    assert "cannot be empty" in result.error_message.lower()


@pytest.mark.asyncio
async def test_set_webhook_invalid_url_http(webhook_manager):
    """Test webhook setup with HTTP URL (not HTTPS)."""
    # Act
    result = await webhook_manager.set_webhook("http://example.com/webhook")
    
    # Assert
    assert not result.success
    assert "https" in result.error_message.lower()


@pytest.mark.asyncio
async def test_set_webhook_invalid_url_localhost(webhook_manager):
    """Test webhook setup with localhost URL."""
    # Act
    result = await webhook_manager.set_webhook("https://localhost/webhook")
    
    # Assert
    assert not result.success
    assert "invalid domain" in result.error_message.lower()


@pytest.mark.asyncio
async def test_set_webhook_success_with_pending_updates(webhook_manager, mock_bot):
    """Test successful webhook setup with pending updates."""
    # Arrange
    webhook_url = "https://misix.onrender.com/webhook"
    
    # Mock successful webhook setup
    mock_bot.set_webhook = AsyncMock(return_value=True)
    
    # Mock webhook info with pending updates
    mock_info = MagicMock()
    mock_info.url = webhook_url
    mock_info.has_custom_certificate = False
    mock_info.pending_update_count = 3
    mock_info.last_error_date = None
    mock_info.last_error_message = None
    mock_info.max_connections = 40
    mock_info.allowed_updates = None
    
    mock_bot.get_webhook_info = AsyncMock(return_value=mock_info)
    
    # Mock pending updates
    mock_updates = [
        MagicMock(spec=Update, update_id=1),
        MagicMock(spec=Update, update_id=2),
        MagicMock(spec=Update, update_id=3),
    ]
    mock_bot.get_updates = AsyncMock(side_effect=[mock_updates, []])
    
    webhook_manager.application.process_update = AsyncMock()
    
    # Act
    result = await webhook_manager.set_webhook(webhook_url)
    
    # Assert
    assert result.success
    assert result.webhook_url == webhook_url
    assert result.pending_updates_processed == 3


@pytest.mark.asyncio
async def test_delete_webhook_success(webhook_manager, mock_bot):
    """Test successful webhook deletion."""
    # Arrange
    webhook_manager.webhook_url = "https://example.com/webhook"
    webhook_manager.is_set = True
    
    mock_bot.delete_webhook = AsyncMock(return_value=True)
    
    # Act
    result = await webhook_manager.delete_webhook()
    
    # Assert
    assert result is True
    assert webhook_manager.webhook_url is None
    assert webhook_manager.is_set is False


@pytest.mark.asyncio
async def test_delete_webhook_with_drop_pending(webhook_manager, mock_bot):
    """Test webhook deletion with dropping pending updates."""
    # Arrange
    mock_bot.delete_webhook = AsyncMock(return_value=True)
    
    # Act
    result = await webhook_manager.delete_webhook(drop_pending_updates=True)
    
    # Assert
    assert result is True
    mock_bot.delete_webhook.assert_called_once_with(drop_pending_updates=True)


@pytest.mark.asyncio
async def test_process_pending_updates_no_updates(webhook_manager, mock_bot):
    """Test processing pending updates when there are none."""
    # Arrange
    mock_bot.get_updates = AsyncMock(return_value=[])
    
    # Act
    result = await webhook_manager.process_pending_updates()
    
    # Assert
    assert result == 0


@pytest.mark.asyncio
async def test_process_pending_updates_with_errors(webhook_manager, mock_bot):
    """Test processing pending updates with some failing."""
    # Arrange
    mock_updates = [
        MagicMock(spec=Update, update_id=1),
        MagicMock(spec=Update, update_id=2),
        MagicMock(spec=Update, update_id=3),
    ]
    
    mock_bot.get_updates = AsyncMock(side_effect=[mock_updates, []])
    
    # Make second update fail
    async def mock_process(update):
        if update.update_id == 2:
            raise Exception("Processing error")
    
    webhook_manager.application.process_update = AsyncMock(side_effect=mock_process)
    
    # Act
    result = await webhook_manager.process_pending_updates()
    
    # Assert
    assert result == 2  # 2 successful, 1 failed
    assert webhook_manager.application.process_update.call_count == 3
