"""Telegram bot setup for MISIX assistant."""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.shared.config import settings

logger = logging.getLogger(__name__)

# Initialize application and scheduler as None
application = None
scheduler = None

def _create_application():
    """Create and configure Telegram application."""
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping bot initialization")
        return None
    
    try:
        # Create application without job_queue to avoid weak reference error in Python 3.13
        # Job queue functionality is handled by APScheduler instead
        app = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .job_queue(None)  # Disable job_queue to avoid weak reference error
            .build()
        )
        logger.info("Telegram application created successfully")
        return app
    except TypeError as e:
        if "weak reference" in str(e):
            logger.error(
                "Failed to create Telegram application due to Python 3.13 compatibility issue. "
                "Bot functionality will be disabled. Error: %s", e
            )
            return None
        raise
    
    if not app:
        return None
    
    # Import handlers
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
    
    # Register command handlers
    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(CommandHandler("profile", handle_profile_command))
    app.add_handler(CommandHandler("tasks", handle_tasks_command))
    app.add_handler(CommandHandler("finances", handle_finances_command))
    app.add_handler(CommandHandler("mood", handle_mood_command))
    app.add_handler(CommandHandler("reminders", handle_reminders_command))
    app.add_handler(CommandHandler("sleep", handle_sleep_start))
    app.add_handler(CommandHandler("wake", handle_sleep_stop))
    
    # Register callback query handlers
    app.add_handler(CallbackQueryHandler(handle_reminder_callback, pattern="^reminder_"))
    
    # Register message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    
    return app

def get_application():
    """Get or create the Telegram application."""
    global application
    if application is None and settings.telegram_bot_token:
        application = _create_application()
        logger.info("Telegram application created")
    return application

def get_scheduler():
    """Get or create the scheduler."""
    global scheduler
    if scheduler is None:
        app = get_application()
        if app:
            try:
                from .scheduler import setup_scheduler
                scheduler = setup_scheduler(app.bot)
                logger.info("Scheduler initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
    return scheduler


def start_bot_with_scheduler():
    """Start the bot and scheduler together."""
    sched = get_scheduler()
    if sched:
        try:
            from .scheduler import start_scheduler
            start_scheduler()
            logger.info("Bot scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def stop_bot_with_scheduler():
    """Stop the bot and scheduler gracefully."""
    sched = get_scheduler()
    if sched:
        try:
            from .scheduler import stop_scheduler
            stop_scheduler()
            logger.info("Bot scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
