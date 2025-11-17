"""Message handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from users.
    
    This is a simplified handler. The full implementation should:
    1. Extract user message
    2. Call AI service for response
    3. Process structured data (tasks, finances, etc.)
    4. Send response back to user
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"Received message from user {user.id}: {message_text[:50]}...")
    
    # TODO: Implement full message processing
    # For now, just acknowledge receipt
    await update.message.reply_text(
        "Сообщение получено! Полная обработка будет реализована после завершения рефакторинга."
    )


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages from users.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    logger.info(f"Received voice message from user {user.id}")
    
    # TODO: Implement voice transcription
    await update.message.reply_text(
        "Голосовые сообщения будут поддерживаться после завершения рефакторинга."
    )
