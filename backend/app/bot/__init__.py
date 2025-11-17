"""Telegram bot setup for MISIX assistant."""

from telegram.ext import Application
from app.shared.config import settings

# Initialize application
application = None

if settings.telegram_bot_token:
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # TODO: Register handlers when migrating from old handlers.py
    # from .handlers import handle_text_message, handle_start_command
    # application.add_handler(CommandHandler("start", handle_start_command))
    # application.add_handler(MessageHandler(filters.TEXT, handle_text_message))
else:
    # Telegram bot is optional
    pass
