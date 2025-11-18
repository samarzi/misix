"""Telegram webhook manager for MISIX bot."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.error import TelegramError, InvalidToken, NetworkError
from telegram.ext import Application


logger = logging.getLogger(__name__)


@dataclass
class WebhookInfo:
    """Information about current webhook status from Telegram API."""
    url: str
    has_custom_certificate: bool
    pending_update_count: int
    last_error_date: Optional[int] = None
    last_error_message: Optional[str] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[list[str]] = None


@dataclass
class WebhookSetupResult:
    """Result of webhook setup operation."""
    success: bool
    webhook_url: str
    pending_updates_processed: int = 0
    error_message: Optional[str] = None


class WebhookManager:
    """Manages Telegram webhook lifecycle.
    
    This class handles:
    - Setting webhook URL in Telegram API
    - Deleting webhook from Telegram API
    - Checking webhook status
    - Processing pending updates after webhook setup
    """
    
    def __init__(self, application: Application):
        """Initialize webhook manager.
        
        Args:
            application: Telegram Application instance
        """
        self.application = application
        self.webhook_url: Optional[str] = None
        self.is_set: bool = False
        
        logger.debug("WebhookManager initialized")
    
    async def get_webhook_info(self) -> Optional[WebhookInfo]:
        """Get current webhook status from Telegram API.
        
        Returns:
            WebhookInfo object with current status, or None if request fails
        """
        try:
            logger.info("🔍 Checking current webhook status...")
            
            info = await self.application.bot.get_webhook_info()
            
            webhook_info = WebhookInfo(
                url=info.url or "",
                has_custom_certificate=info.has_custom_certificate,
                pending_update_count=info.pending_update_count,
                last_error_date=info.last_error_date,
                last_error_message=info.last_error_message,
                max_connections=info.max_connections,
                allowed_updates=info.allowed_updates
            )
            
            # Log webhook status
            if webhook_info.url:
                logger.info(
                    f"📡 Webhook is set: {webhook_info.url} "
                    f"(pending: {webhook_info.pending_update_count})"
                )
            else:
                logger.info("📡 No webhook is currently set")
            
            if webhook_info.last_error_message:
                logger.warning(
                    f"⚠️  Last webhook error: {webhook_info.last_error_message} "
                    f"(date: {webhook_info.last_error_date})"
                )
            
            return webhook_info
            
        except InvalidToken as e:
            logger.error(f"❌ Invalid bot token: {e}")
            raise
        except TelegramError as e:
            logger.error(f"❌ Failed to get webhook info: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error getting webhook info: {e}", exc_info=True)
            return None
    
    async def set_webhook(
        self,
        url: str,
        max_connections: int = 40,
        allowed_updates: Optional[list[str]] = None
    ) -> WebhookSetupResult:
        """Set webhook URL in Telegram API.
        
        This method:
        1. Validates the webhook URL
        2. Sets the webhook in Telegram API
        3. Verifies the webhook was set correctly
        4. Processes any pending updates
        
        Args:
            url: Webhook URL (must be HTTPS)
            max_connections: Maximum allowed simultaneous connections (1-100)
            allowed_updates: List of update types to receive (None = all types)
        
        Returns:
            WebhookSetupResult with success status and details
        """
        start_time = datetime.utcnow()
        
        # Validate URL
        if not url:
            error_msg = "Webhook URL cannot be empty"
            logger.error(f"❌ {error_msg}")
            return WebhookSetupResult(
                success=False,
                webhook_url=url,
                error_message=error_msg
            )
        
        if not url.startswith("https://"):
            error_msg = f"Webhook URL must use HTTPS: {url}"
            logger.error(f"❌ {error_msg}")
            return WebhookSetupResult(
                success=False,
                webhook_url=url,
                error_message=error_msg
            )
        
        # Check for invalid domains
        invalid_domains = ["localhost", "127.0.0.1", "example.com", "0.0.0.0"]
        if any(domain in url.lower() for domain in invalid_domains):
            error_msg = f"Webhook URL contains invalid domain: {url}"
            logger.error(f"❌ {error_msg}")
            return WebhookSetupResult(
                success=False,
                webhook_url=url,
                error_message=error_msg
            )
        
        logger.info(f"🔧 Setting webhook to: {url}")
        logger.info(f"   Max connections: {max_connections}")
        logger.info(f"   Allowed updates: {allowed_updates or 'all'}")
        
        # Retry logic for network errors
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                # Set webhook in Telegram API
                success = await self.application.bot.set_webhook(
                    url=url,
                    max_connections=max_connections,
                    allowed_updates=allowed_updates or Update.ALL_TYPES
                )
                
                if not success:
                    error_msg = "Telegram API returned False for set_webhook"
                    logger.error(f"❌ {error_msg}")
                    
                    if attempt < max_retries:
                        logger.info(f"🔄 Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        continue
                    
                    return WebhookSetupResult(
                        success=False,
                        webhook_url=url,
                        error_message=error_msg
                    )
                
                # Verify webhook was set
                info = await self.get_webhook_info()
                if not info or info.url != url:
                    error_msg = f"Webhook verification failed. Expected: {url}, Got: {info.url if info else 'None'}"
                    logger.error(f"❌ {error_msg}")
                    
                    if attempt < max_retries:
                        logger.info(f"🔄 Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        continue
                    
                    return WebhookSetupResult(
                        success=False,
                        webhook_url=url,
                        error_message=error_msg
                    )
                
                # Success!
                self.webhook_url = url
                self.is_set = True
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"✅ Webhook set successfully in {elapsed:.2f}s")
                logger.info(f"📡 Webhook URL: {url}")
                logger.info(f"📨 Pending updates: {info.pending_update_count}")
                
                # Process pending updates
                pending_processed = 0
                if info.pending_update_count > 0:
                    logger.info(f"🔄 Processing {info.pending_update_count} pending updates...")
                    pending_processed = await self.process_pending_updates()
                    logger.info(f"✅ Processed {pending_processed} pending updates")
                
                return WebhookSetupResult(
                    success=True,
                    webhook_url=url,
                    pending_updates_processed=pending_processed
                )
                
            except InvalidToken as e:
                error_msg = f"Invalid bot token: {e}"
                logger.error(f"❌ {error_msg}")
                raise  # Don't retry on invalid token
                
            except NetworkError as e:
                error_msg = f"Network error setting webhook: {e}"
                logger.warning(f"⚠️  {error_msg}")
                
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                
                logger.error(f"❌ Failed after {max_retries} attempts")
                return WebhookSetupResult(
                    success=False,
                    webhook_url=url,
                    error_message=error_msg
                )
                
            except TelegramError as e:
                error_msg = f"Telegram API error: {e}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                
                return WebhookSetupResult(
                    success=False,
                    webhook_url=url,
                    error_message=error_msg
                )
                
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                
                if attempt < max_retries:
                    logger.info(f"🔄 Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                
                return WebhookSetupResult(
                    success=False,
                    webhook_url=url,
                    error_message=error_msg
                )
        
        # Should not reach here, but just in case
        return WebhookSetupResult(
            success=False,
            webhook_url=url,
            error_message="Failed after all retries"
        )
    
    async def delete_webhook(self, drop_pending_updates: bool = False) -> bool:
        """Delete webhook from Telegram API.
        
        Args:
            drop_pending_updates: If True, discard pending updates
        
        Returns:
            True if webhook was deleted successfully, False otherwise
        """
        try:
            logger.info("🗑️  Deleting webhook...")
            
            success = await self.application.bot.delete_webhook(
                drop_pending_updates=drop_pending_updates
            )
            
            if success:
                self.webhook_url = None
                self.is_set = False
                logger.info("✅ Webhook deleted successfully")
                
                if drop_pending_updates:
                    logger.info("🗑️  Pending updates were dropped")
            else:
                logger.warning("⚠️  Telegram API returned False for delete_webhook")
            
            return success
            
        except TelegramError as e:
            logger.error(f"❌ Failed to delete webhook: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting webhook: {e}", exc_info=True)
            return False
    
    async def process_pending_updates(self) -> int:
        """Process any pending updates after webhook setup.
        
        This method fetches pending updates from Telegram and processes them
        through the application's handlers. It's resilient to individual
        update processing errors.
        
        Returns:
            Number of updates successfully processed
        """
        processed_count = 0
        error_count = 0
        
        try:
            logger.info("📥 Fetching pending updates...")
            
            # Get pending updates (offset=0 to get all pending)
            updates = await self.application.bot.get_updates(
                offset=0,
                limit=100,
                timeout=10
            )
            
            if not updates:
                logger.info("📭 No pending updates to process")
                return 0
            
            logger.info(f"📨 Found {len(updates)} pending update(s)")
            
            # Process each update
            for i, update in enumerate(updates, 1):
                try:
                    logger.debug(f"Processing update {i}/{len(updates)}: {update.update_id}")
                    
                    # Process through application handlers
                    await self.application.process_update(update)
                    processed_count += 1
                    
                    logger.debug(f"✅ Update {update.update_id} processed successfully")
                    
                except Exception as e:
                    # Log error but continue with other updates
                    error_count += 1
                    logger.error(
                        f"❌ Error processing update {update.update_id}: {e}",
                        exc_info=True
                    )
                    # Continue processing other updates
                    continue
            
            # Acknowledge all updates by setting offset
            if updates:
                last_update_id = updates[-1].update_id
                await self.application.bot.get_updates(
                    offset=last_update_id + 1,
                    limit=1,
                    timeout=0
                )
                logger.debug(f"✅ Acknowledged updates up to {last_update_id}")
            
            # Log summary
            logger.info(
                f"✅ Pending updates processing complete: "
                f"{processed_count} processed, {error_count} errors"
            )
            
            return processed_count
            
        except TelegramError as e:
            logger.error(f"❌ Failed to fetch pending updates: {e}", exc_info=True)
            return processed_count
        except Exception as e:
            logger.error(f"❌ Unexpected error processing pending updates: {e}", exc_info=True)
            return processed_count
