"""Telegram bot setup for MISIX assistant."""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.shared.config import settings

logger = logging.getLogger(__name__)

# Initialize application, scheduler, polling manager, and webhook manager as None
application = None
scheduler = None
polling_manager = None
webhook_manager = None

def _create_application():
    """Create and configure Telegram application."""
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping bot initialization")
        return None
    
    try:
        # Create application with standard configuration
        # Python 3.11 is fully compatible with python-telegram-bot
        app = Application.builder().token(settings.telegram_bot_token).build()
        logger.info("Telegram application created successfully")
    except Exception as e:
        logger.error(
            f"Failed to create Telegram application: {e}. "
            "Bot functionality will be disabled.",
            exc_info=True
        )
        return None
    
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


def get_polling_manager():
    """Get or create the polling manager."""
    global polling_manager
    if polling_manager is None:
        app = get_application()
        if app:
            try:
                from .polling import PollingManager
                polling_manager = PollingManager(app)
                logger.info("Polling manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize polling manager: {e}", exc_info=True)
    return polling_manager


def get_webhook_manager():
    """Get or create the webhook manager."""
    global webhook_manager
    if webhook_manager is None:
        app = get_application()
        if app:
            try:
                from .webhook import WebhookManager
                webhook_manager = WebhookManager(app)
                logger.info("Webhook manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize webhook manager: {e}", exc_info=True)
    return webhook_manager


def get_webhook_url() -> str:
    """Determine webhook URL from configuration.
    
    Priority:
    1. TELEGRAM_WEBHOOK_URL environment variable (explicit)
    2. BACKEND_BASE_URL + /bot/webhook (derived)
    
    Returns:
        Webhook URL or empty string if not configured
    """
    # Check explicit webhook URL
    webhook_url = settings.telegram_webhook_url
    
    if webhook_url:
        logger.debug(f"Using explicit TELEGRAM_WEBHOOK_URL: {webhook_url}")
        return webhook_url
    
    # Derive from backend base URL
    backend_url = settings.backend_base_url
    if backend_url:
        webhook_url = f"{backend_url}/bot/webhook"
        logger.debug(f"Derived webhook URL from BACKEND_BASE_URL: {webhook_url}")
        return webhook_url
    
    logger.warning("No webhook URL configured (TELEGRAM_WEBHOOK_URL or BACKEND_BASE_URL)")
    return ""
