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
    try:
        from app.repositories.user import get_user_repository
        from datetime import datetime
        
        user_telegram = update.effective_user
        
        # Get or create user
        user_repo = get_user_repository()
        user = await user_repo.get_or_create_by_telegram_id(
            telegram_id=user_telegram.id,
            username=user_telegram.username,
            first_name=user_telegram.first_name,
            last_name=user_telegram.last_name
        )
        
        logger.info(f"User {user_telegram.id} started sleep tracking")
        
        # TODO: Save sleep start time to database
        # For now, just acknowledge
        await update.message.reply_text(
            "🛌 Спокойной ночи! Я запомнил, что вы легли спать.\n\n"
            "Напишите /wake когда проснетесь, чтобы я записал продолжительность сна."
        )
        
    except Exception as e:
        logger.error(f"Failed to start sleep tracking: {e}", exc_info=True)
        await update.message.reply_text(
            "Не удалось начать трекинг сна. Попробуйте позже."
        )


async def handle_sleep_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sleep tracking stop.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        
        user_telegram = update.effective_user
        
        # Get user
        user_repo = get_user_repository()
        user = await user_repo.get_by_telegram_id(user_telegram.id)
        
        if not user:
            await update.message.reply_text(
                "Сначала отправьте мне /sleep когда ложитесь спать."
            )
            return
        
        logger.info(f"User {user_telegram.id} stopped sleep tracking")
        
        # TODO: Calculate sleep duration and save to database
        # For now, just acknowledge
        await update.message.reply_text(
            "☀️ Доброе утро! Надеюсь, вы хорошо выспались!\n\n"
            "Полный трекинг сна будет доступен в следующей версии."
        )
        
    except Exception as e:
        logger.error(f"Failed to stop sleep tracking: {e}", exc_info=True)
        await update.message.reply_text(
            "Не удалось завершить трекинг сна. Попробуйте позже."
        )


async def handle_sleep_start_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sleep tracking start from callback query.
    
    Args:
        query: Callback query
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from datetime import datetime
        
        user_telegram = query.from_user
        
        # Get or create user
        user_repo = get_user_repository()
        user = await user_repo.get_or_create_by_telegram_id(
            telegram_id=user_telegram.id,
            username=user_telegram.username,
            first_name=user_telegram.first_name,
            last_name=user_telegram.last_name
        )
        
        logger.info(f"User {user_telegram.id} started sleep tracking via button")
        
        # TODO: Save sleep start time to database
        # For now, just acknowledge
        await query.message.reply_text(
            "🛌 Спокойной ночи! Я запомнил, что вы легли спать.\n\n"
            "Напишите /wake когда проснетесь, чтобы я записал продолжительность сна."
        )
        
    except Exception as e:
        logger.error(f"Failed to start sleep tracking: {e}", exc_info=True)
        await query.message.reply_text(
            "Не удалось начать трекинг сна. Попробуйте позже."
        )
