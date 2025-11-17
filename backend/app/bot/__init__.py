"""Telegram bot setup for MISIX assistant."""

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.shared.config import settings

# Initialize application
application = None

if settings.telegram_bot_token:
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Register handlers
    from .handlers.command import handle_start_command, handle_help_command, handle_profile_command
    from .handlers.message import handle_text_message, handle_voice_message
    from .handlers.sleep import handle_sleep_start, handle_sleep_stop
    
    # Command handlers
    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(CommandHandler("help", handle_help_command))
    application.add_handler(CommandHandler("profile", handle_profile_command))
    application.add_handler(CommandHandler("sleep", handle_sleep_start))
    application.add_handler(CommandHandler("wake", handle_sleep_stop))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
else:
    # Telegram bot is optional
    pass
