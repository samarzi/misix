"""Telegram bot setup for MISIX assistant."""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.shared.config import settings

logger = logging.getLogger(__name__)

# Initialize application
application = None
scheduler = None

if settings.telegram_bot_token:
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Register handlers
    from .handlers.command import (
        handle_start_command,
        handle_help_command,
        handle_profile_command,
        handle_tasks_command,
        handle_finances_command,
        handle_mood_command,
        handle_reminders_command,
        handle_reminder_callback
    )
    from .handlers.message import handle_text_message, handle_voice_message
    from .handlers.sleep import handle_sleep_start, handle_sleep_stop
    from telegram.ext import CallbackQueryHandler
    
    # Command handlers
    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(CommandHandler("help", handle_help_command))
    application.add_handler(CommandHandler("profile", handle_profile_command))
    application.add_handler(CommandHandler("tasks", handle_tasks_command))
    application.add_handler(CommandHandler("finances", handle_finances_command))
    application.add_handler(CommandHandler("mood", handle_mood_command))
    application.add_handler(CommandHandler("reminders", handle_reminders_command))
    application.add_handler(CommandHandler("sleep", handle_sleep_start))
    application.add_handler(CommandHandler("wake", handle_sleep_stop))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_reminder_callback, pattern="^reminder_"))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    
    # Setup scheduler for reminders
    try:
        from .scheduler import setup_scheduler, start_scheduler, stop_scheduler
        scheduler = setup_scheduler(application.bot)
        logger.info("Scheduler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
else:
    # Telegram bot is optional
    pass


def start_bot_with_scheduler():
    """Start the bot and scheduler together."""
    if scheduler:
        try:
            from .scheduler import start_scheduler
            start_scheduler()
            logger.info("Bot scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def stop_bot_with_scheduler():
    """Stop the bot and scheduler gracefully."""
    if scheduler:
        try:
            from .scheduler import stop_scheduler
            stop_scheduler()
            logger.info("Bot scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
