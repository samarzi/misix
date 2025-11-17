"""Command handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

HELP_MESSAGE = """
🤖 **MISIX - Ваш персональный AI-ассистент**

Я помогу вам управлять задачами, финансами, заметками и многим другим!

**Основные команды:**
/start - Начать работу
/help - Показать эту справку
/profile - Ваш профиль

**Как пользоваться:**
Просто пишите мне естественным языком:
• "Добавь задачу: купить молоко"
• "Потратил 500 рублей на обед"
• "Напомни завтра в 9:00 позвонить"
• "Сохрани заметку: идеи для проекта"

Я автоматически распознаю, что вы хотите сделать!

**Веб-интерфейс:**
Управляйте всеми данными через веб-панель: https://misix.app
"""


async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    welcome_message = f"""
👋 Привет, {user.first_name}!

Я MISIX - ваш персональный AI-ассистент.

Я помогу вам:
• 📝 Управлять задачами и напоминаниями
• 💰 Отслеживать финансы
• 📓 Сохранять заметки
• 🎯 Достигать целей

Просто пишите мне естественным языком, и я пойму, что вам нужно!

Используйте /help для подробной справки.
"""
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user.id} started bot")


async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
    logger.info(f"User {update.effective_user.id} requested help")


async def handle_profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profile command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    # TODO: Fetch user profile from database
    profile_message = f"""
👤 **Ваш профиль**

Имя: {user.first_name}
Telegram ID: {user.id}
Username: @{user.username if user.username else 'не указан'}

Для управления профилем используйте веб-интерфейс: https://misix.app
"""
    
    await update.message.reply_text(profile_message, parse_mode="Markdown")
    logger.info(f"User {user.id} viewed profile")
