"""Command handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

HELP_MESSAGE = """
🤖 **MISIX - Ваш персональный AI-ассистент**

Я помогу вам управлять задачами, финансами, заметками и настроением!

**📋 Команды:**
/start - Начать работу
/help - Показать эту справку
/tasks - Список ваших задач
/finances - Финансовая сводка
/mood - История настроения
/profile - Ваш профиль

**💬 Как пользоваться:**
Просто пишите мне естественным языком (текстом или голосом):
• "Напомни завтра купить молоко"
• "Потратил 500 рублей на обед"
• "Запомни что встреча в офисе на Ленина 5"
• "Сегодня отличное настроение!"

Я автоматически распознаю, что вы хотите сделать!

**🎤 Голосовые сообщения:**
Отправляйте голосовые - я распознаю речь и обработаю как текст!

**🌐 Веб-интерфейс:**
https://misix.netlify.app
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



async def handle_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command - show user's tasks.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from app.services.task_service import get_task_service
        
        user_telegram = update.effective_user
        
        # Get user
        user_repo = get_user_repository()
        user = await user_repo.get_by_telegram_id(user_telegram.id)
        
        if not user:
            await update.message.reply_text(
                "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
            )
            return
        
        # Get tasks
        task_service = get_task_service()
        tasks = await task_service.get_by_user(str(user["id"]))
        
        if not tasks:
            await update.message.reply_text(
                "📋 У вас пока нет задач.\n\nСоздайте задачу, написав мне, например:\n\"Напомни завтра купить молоко\""
            )
            return
        
        # Format tasks
        active_tasks = [t for t in tasks if t.get("status") != "completed"]
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        message = "📋 **Ваши задачи:**\n\n"
        
        if active_tasks:
            message += "**Активные:**\n"
            for task in active_tasks[:10]:  # Show max 10
                title = task.get("title", "Без названия")
                deadline = task.get("deadline")
                priority = task.get("priority", "medium")
                
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                
                message += f"{priority_emoji} {title}"
                if deadline:
                    from datetime import datetime
                    if isinstance(deadline, str):
                        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    message += f" (до {deadline.strftime('%d.%m')})"
                message += "\n"
        
        if completed_tasks:
            message += f"\n✅ Выполнено: {len(completed_tasks)}"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"User {user_telegram.id} viewed tasks")
        
    except Exception as e:
        logger.error(f"Failed to show tasks: {e}")
        await update.message.reply_text(
            "Не удалось загрузить задачи. Попробуйте позже."
        )


async def handle_finances_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /finances command - show financial summary.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from app.services.finance_service import get_finance_service
        from datetime import datetime, timedelta
        
        user_telegram = update.effective_user
        
        # Get user
        user_repo = get_user_repository()
        user = await user_repo.get_by_telegram_id(user_telegram.id)
        
        if not user:
            await update.message.reply_text(
                "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
            )
            return
        
        # Get finances for last 30 days
        finance_service = get_finance_service()
        records = await finance_service.get_by_user(str(user["id"]))
        
        if not records:
            await update.message.reply_text(
                "💰 У вас пока нет финансовых записей.\n\nДобавьте расход, написав:\n\"Потратил 500₽ на кофе\""
            )
            return
        
        # Calculate stats
        total_expenses = sum(r.get("amount", 0) for r in records if r.get("type") == "expense")
        total_income = sum(r.get("amount", 0) for r in records if r.get("type") == "income")
        balance = total_income - total_expenses
        
        # Group by category
        from collections import defaultdict
        expenses_by_category = defaultdict(float)
        for r in records:
            if r.get("type") == "expense":
                category = r.get("category", "другое")
                expenses_by_category[category] += r.get("amount", 0)
        
        message = "💰 **Финансовая сводка:**\n\n"
        message += f"💸 Расходы: {total_expenses:,.0f}₽\n"
        message += f"💵 Доходы: {total_income:,.0f}₽\n"
        message += f"{'📈' if balance >= 0 else '📉'} Баланс: {balance:+,.0f}₽\n"
        
        if expenses_by_category:
            message += "\n**По категориям:**\n"
            sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
            for category, amount in sorted_categories[:5]:
                message += f"• {category}: {amount:,.0f}₽\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"User {user_telegram.id} viewed finances")
        
    except Exception as e:
        logger.error(f"Failed to show finances: {e}")
        await update.message.reply_text(
            "Не удалось загрузить финансы. Попробуйте позже."
        )


async def handle_mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mood command - show mood history.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from app.services.mood_service import get_mood_service
        
        user_telegram = update.effective_user
        
        # Get user
        user_repo = get_user_repository()
        user = await user_repo.get_by_telegram_id(user_telegram.id)
        
        if not user:
            await update.message.reply_text(
                "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
            )
            return
        
        # Get mood history
        mood_service = get_mood_service()
        history = await mood_service.get_mood_history(str(user["id"]), days=7)
        
        if not history:
            await update.message.reply_text(
                "😊 У вас пока нет записей о настроении.\n\nРасскажите как вы себя чувствуете!"
            )
            return
        
        # Get trends
        trends = await mood_service.analyze_mood_trends(str(user["id"]), days=7)
        
        mood_emojis = {
            "happy": "😊",
            "sad": "😢",
            "anxious": "😰",
            "calm": "😌",
            "excited": "🤩",
            "tired": "😴",
            "stressed": "😫",
            "angry": "😠",
            "neutral": "😐"
        }
        
        message = "😊 **Ваше настроение (последние 7 дней):**\n\n"
        message += f"📊 Средняя интенсивность: {trends.average_intensity:.1f}/10\n"
        message += f"🎯 Чаще всего: {mood_emojis.get(trends.most_common_mood, '😊')} {trends.most_common_mood}\n"
        
        message += "\n**Последние записи:**\n"
        for entry in history[:5]:
            mood = entry.get("mood", "")
            intensity = entry.get("intensity", 5)
            emoji = mood_emojis.get(mood, "😊")
            message += f"{emoji} {mood} ({intensity}/10)\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"User {user_telegram.id} viewed mood")
        
    except Exception as e:
        logger.error(f"Failed to show mood: {e}")
        await update.message.reply_text(
            "Не удалось загрузить данные о настроении. Попробуйте позже."
        )
