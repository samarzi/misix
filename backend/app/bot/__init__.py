"""Telegram bot setup for MISIX assistant."""

from telegram.ext import Application
from app.shared.config import settings
from .handlers import register_handlers  # noqa: F401

application = Application.builder().token(settings.telegram_bot_token).build()
register_handlers(application)
