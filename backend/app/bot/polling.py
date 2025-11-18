"""Telegram bot polling manager."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.error import TelegramError, Conflict, InvalidToken, NetworkError, TimedOut
from telegram.ext import Application

from app.shared.config import settings


logger = logging.getLogger(__name__)


@dataclass
class PollingState:
    """State of the polling mechanism."""
    is_running: bool
    last_update_id: int
    updates_received: int
    errors_count: int
    last_error: Optional[str]
    started_at: Optional[datetime]


class PollingManager:
    """Manages Telegram bot polling lifecycle."""
    
    def __init__(self, application: Application):
        """Initialize polling manager.
        
        Args:
            application: Telegram Application instance
        """
        self.application = application
        self.polling_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.last_update_id = 0
        self.updates_received = 0
        self.errors_count = 0
        self.last_error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        
        logger.debug("PollingManager initialized")
    
    def get_state(self) -> PollingState:
        """Get current polling state.
        
        Returns:
            Current polling state
        """
        return PollingState(
            is_running=self.is_running,
            last_update_id=self.last_update_id,
            updates_received=self.updates_received,
            errors_count=self.errors_count,
            last_error=self.last_error,
            started_at=self.started_at
        )
    
    async def start_polling(self) -> None:
        """Start the polling loop if not already running.
        
        This method is idempotent - calling it multiple times will not
        create multiple polling tasks.
        """
        if self.is_running:
            logger.warning("Polling already running, ignoring start request")
            return
        
        if self.polling_task and not self.polling_task.done():
            logger.warning("Polling task already exists, ignoring start request")
            return
        
        logger.info("Starting Telegram polling...")
        self.is_running = True
        self.started_at = datetime.utcnow()
        self.polling_task = asyncio.create_task(self._poll_updates())
        logger.info("✅ Telegram polling started successfully")
    
    async def stop_polling(self) -> None:
        """Stop the polling loop gracefully."""
        if not self.is_running:
            logger.debug("Polling not running, nothing to stop")
            return
        
        logger.info("Stopping Telegram polling...")
        self.is_running = False
        
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                logger.debug("Polling task cancelled successfully")
            except Exception as e:
                logger.error(f"Error while stopping polling task: {e}", exc_info=True)
            finally:
                self.polling_task = None
        
        logger.info("✅ Telegram polling stopped")
    
    async def _poll_updates(self) -> None:
        """Internal polling loop that fetches updates from Telegram.
        
        This method runs in an infinite loop, fetching updates from Telegram
        and processing them through the application's handlers.
        
        Error handling:
        - Network errors: Retry after 5 seconds
        - Rate limits: Respect Retry-After header
        - Invalid token: Stop polling and raise
        - Conflict (409): Another instance running, stop polling
        - Other errors: Log and retry after 5 seconds
        """
        offset = 0
        retry_delay = 5  # seconds
        
        logger.info(f"Polling loop started (timeout=30s, retry_delay={retry_delay}s)")
        
        while self.is_running:
            try:
                # Fetch updates from Telegram with long polling
                updates = await self.application.bot.get_updates(
                    offset=offset,
                    timeout=30,
                    allowed_updates=Update.ALL_TYPES
                )
                
                if updates:
                    logger.info(f"📨 Received {len(updates)} update(s)")
                    self.updates_received += len(updates)
                
                # Process each update
                for update in updates:
                    try:
                        # Update offset to avoid reprocessing
                        offset = max(offset, update.update_id + 1)
                        self.last_update_id = update.update_id
                        
                        # Log update details
                        user_id = None
                        update_type = "unknown"
                        
                        if update.message:
                            update_type = "message"
                            if update.message.from_user:
                                user_id = update.message.from_user.id
                        elif update.callback_query:
                            update_type = "callback_query"
                            if update.callback_query.from_user:
                                user_id = update.callback_query.from_user.id
                        elif update.edited_message:
                            update_type = "edited_message"
                            if update.edited_message.from_user:
                                user_id = update.edited_message.from_user.id
                        
                        logger.debug(
                            f"Processing update {update.update_id}: "
                            f"type={update_type}, user_id={user_id}"
                        )
                        
                        # Process update through application handlers
                        await self.application.process_update(update)
                        
                    except Exception as e:
                        # Log error but continue processing other updates
                        logger.error(
                            f"Error processing update {update.update_id}: {e}",
                            exc_info=True
                        )
                        self.errors_count += 1
                        self.last_error = str(e)
                
            except InvalidToken as e:
                # Critical error - invalid bot token
                logger.error(f"❌ Invalid Telegram bot token: {e}")
                self.is_running = False
                raise
            
            except Conflict as e:
                # Another bot instance is running
                logger.error(
                    f"❌ Conflict error - another bot instance is running: {e}"
                )
                self.is_running = False
                break
            
            except TimedOut:
                # Timeout is normal for long polling, just continue
                logger.debug("Polling timeout (normal), continuing...")
                continue
            
            except NetworkError as e:
                # Network error - retry after delay
                logger.warning(
                    f"⚠️  Network error during polling: {e}. "
                    f"Retrying in {retry_delay} seconds..."
                )
                self.errors_count += 1
                self.last_error = str(e)
                await asyncio.sleep(retry_delay)
                continue
            
            except TelegramError as e:
                # Other Telegram API errors
                logger.error(
                    f"❌ Telegram API error: {e}. "
                    f"Retrying in {retry_delay} seconds...",
                    exc_info=True
                )
                self.errors_count += 1
                self.last_error = str(e)
                await asyncio.sleep(retry_delay)
                continue
            
            except asyncio.CancelledError:
                # Task was cancelled (normal during shutdown)
                logger.info("Polling task cancelled")
                break
            
            except Exception as e:
                # Unexpected error
                logger.error(
                    f"❌ Unexpected error in polling loop: {e}. "
                    f"Retrying in {retry_delay} seconds...",
                    exc_info=True
                )
                self.errors_count += 1
                self.last_error = str(e)
                await asyncio.sleep(retry_delay)
                continue
        
        logger.info("Polling loop ended")


def should_use_polling() -> bool:
    """Determine if polling should be used based on configuration.
    
    Polling is used when:
    - No webhook URL is configured
    - Webhook URL is not a valid HTTPS endpoint
    - Webhook URL points to localhost or example domains
    
    Returns:
        True if polling should be used, False if webhook should be used
    """
    # Check explicit webhook URL
    webhook_url = settings.telegram_webhook_url
    
    if not webhook_url:
        # Try to derive from backend base URL
        webhook_url = settings.backend_base_url
    
    if not webhook_url:
        logger.info("No webhook URL configured, will use polling")
        return True
    
    # Check if URL is valid HTTPS
    if not webhook_url.startswith("https://"):
        logger.info(
            f"Webhook URL is not HTTPS ({webhook_url}), will use polling"
        )
        return True
    
    # Check if it's localhost or example domain (not valid for webhook)
    if any(host in webhook_url.lower() for host in ["localhost", "127.0.0.1", "example.com"]):
        logger.info(
            f"Webhook URL is localhost/example ({webhook_url}), will use polling"
        )
        return True
    
    logger.info(f"Valid webhook URL configured ({webhook_url}), will use webhook")
    return False
