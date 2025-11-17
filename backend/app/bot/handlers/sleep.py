"""Sleep tracking handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_sleep_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sleep tracking start.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    logger.info(f"User {user.id} started sleep tracking")
    
    # TODO: Implement sleep tracking
    await update.message.reply_text(
        "🛌 Трекинг сна будет реализован после завершения рефакторинга."
    )


async def handle_sleep_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sleep tracking stop.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    logger.info(f"User {user.id} stopped sleep tracking")
    
    # TODO: Implement sleep tracking
    await update.message.reply_text(
        "☀️ Трекинг сна будет реализован после завершения рефакторинга."
    )
