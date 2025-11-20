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
/reminders - Настройки напоминаний
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

**⏰ Напоминания:**
Получайте напоминания о задачах и ежедневную утреннюю сводку!

**🌐 Веб-интерфейс:**
https://misix.netlify.app
"""


async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
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
    
    # Add quick action buttons
    keyboard = [
        [
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
            InlineKeyboardButton("📋 Задачи", callback_data="tasks")
        ],
        [
            InlineKeyboardButton("💰 Финансы", callback_data="finances"),
            InlineKeyboardButton("😊 Настроение", callback_data="mood")
        ],
        [
            InlineKeyboardButton("🛌 Я спать", callback_data="sleep")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
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


async def handle_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reminders command - manage reminder settings.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    try:
        from app.repositories.user import get_user_repository
        from app.repositories.user_settings import get_user_settings_repository
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        user_telegram = update.effective_user
        
        # Get user
        user_repo = get_user_repository()
        user = await user_repo.get_by_telegram_id(user_telegram.id)
        
        if not user:
            await update.message.reply_text(
                "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
            )
            return
        
        # Get settings
        settings_repo = get_user_settings_repository()
        settings = await settings_repo.get_settings(str(user["id"]))
        
        # Build message
        enabled = settings.get("reminders_enabled", True)
        summary_time = settings.get("daily_summary_time", "09:00")
        minutes_before = settings.get("reminder_minutes_before", 60)
        
        status_emoji = "✅" if enabled else "❌"
        
        message = f"""⏰ **Настройки напоминаний**

{status_emoji} Напоминания: {'Включены' if enabled else 'Выключены'}
🌅 Утренняя сводка: {summary_time}
⏱ Напоминать за: {minutes_before} минут

**Что я делаю:**
• Напоминаю о задачах перед дедлайном
• Отправляю утреннюю сводку задач
• Показываю просроченные задачи

Используйте кнопки ниже для настройки:
"""
        
        # Build keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Включить" if not enabled else "❌ Выключить",
                    callback_data=f"reminder_toggle:{user['id']}"
                )
            ],
            [
                InlineKeyboardButton("⏱ 15 мин", callback_data=f"reminder_time:15:{user['id']}"),
                InlineKeyboardButton("⏱ 30 мин", callback_data=f"reminder_time:30:{user['id']}"),
                InlineKeyboardButton("⏱ 60 мин", callback_data=f"reminder_time:60:{user['id']}")
            ],
            [
                InlineKeyboardButton("🌅 Изменить время сводки", callback_data=f"reminder_summary:{user['id']}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info(f"User {user_telegram.id} viewed reminder settings")
        
    except Exception as e:
        logger.error(f"Failed to show reminder settings: {e}", exc_info=True)
        await update.message.reply_text(
            "Не удалось загрузить настройки напоминаний. Попробуйте позже."
        )


async def handle_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from reminder settings.
    
    Args:
        update: Telegram update with callback query
        context: Bot context
    """
    try:
        from app.repositories.user_settings import get_user_settings_repository
        
        query = update.callback_query
        await query.answer()
        
        data = query.data
        settings_repo = get_user_settings_repository()
        
        if data.startswith("reminder_toggle:"):
            user_id = data.split(":")[1]
            settings = await settings_repo.get_settings(user_id)
            new_state = not settings.get("reminders_enabled", True)
            
            await settings_repo.update_settings(
                user_id=user_id,
                reminders_enabled=new_state
            )
            
            status = "включены" if new_state else "выключены"
            await query.edit_message_text(
                f"✅ Напоминания {status}!\n\nИспользуйте /reminders чтобы изменить настройки."
            )
            
        elif data.startswith("reminder_time:"):
            parts = data.split(":")
            minutes = int(parts[1])
            user_id = parts[2]
            
            await settings_repo.update_settings(
                user_id=user_id,
                reminder_minutes_before=minutes
            )
            
            await query.edit_message_text(
                f"✅ Буду напоминать за {minutes} минут до дедлайна!\n\nИспользуйте /reminders чтобы изменить настройки."
            )
            
        elif data.startswith("reminder_summary:"):
            await query.edit_message_text(
                "🌅 Чтобы изменить время утренней сводки, напишите:\n\n"
                "\"Установи время сводки на 08:00\"\n\n"
                "Или используйте /reminders для других настроек."
            )
        
        logger.info(f"Processed reminder callback: {data}")
        
    except Exception as e:
        logger.error(f"Failed to handle reminder callback: {e}", exc_info=True)
        try:
            await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")
        except:
            pass



async def handle_quick_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from quick action buttons.
    
    Args:
        update: Telegram update with callback query
        context: Bot context
    """
    try:
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        logger.info(f"Processing callback action: {action} from user {query.from_user.id}")
        
        # Route to appropriate handler
        if action == "help":
            await query.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
            logger.info(f"User {query.from_user.id} requested help via button")
            
        elif action == "tasks":
            # Call handler directly with callback query context
            try:
                await _handle_tasks_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle tasks callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить задачи. Попробуйте команду /tasks"
                )
            
        elif action == "finances":
            try:
                await _handle_finances_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle finances callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить финансы. Попробуйте команду /finances"
                )
            
        elif action == "mood":
            try:
                await _handle_mood_for_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle mood callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось загрузить настроение. Попробуйте команду /mood"
                )
            
        elif action == "sleep":
            try:
                from app.bot.handlers.sleep import handle_sleep_start_callback
                await handle_sleep_start_callback(query, context)
            except Exception as e:
                logger.error(f"Failed to handle sleep callback: {e}", exc_info=True)
                await query.message.reply_text(
                    "Не удалось начать трекинг сна. Попробуйте команду /sleep"
                )
        
        logger.info(f"Successfully processed callback action: {action}")
        
    except Exception as e:
        logger.error(f"Failed to handle quick action callback: {e}", exc_info=True)
        try:
            await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")
        except:
            pass


async def _handle_tasks_for_callback(query, context):
    """Handle tasks command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.task_service import get_task_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get tasks
    task_service = get_task_service()
    tasks = await task_service.get_by_user(str(user["id"]))
    
    if not tasks:
        await query.message.reply_text(
            "📋 У вас пока нет задач.\n\nСоздайте задачу, написав мне, например:\n\"Напомни завтра купить молоко\""
        )
        return
    
    # Format tasks
    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    message = "📋 **Ваши задачи:**\n\n"
    
    if active_tasks:
        message += "**Активные:**\n"
        for task in active_tasks[:10]:
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
    
    await query.message.reply_text(message, parse_mode="Markdown")


async def _handle_finances_for_callback(query, context):
    """Handle finances command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.finance_service import get_finance_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get finances
    finance_service = get_finance_service()
    records = await finance_service.get_by_user(str(user["id"]))
    
    if not records:
        await query.message.reply_text(
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
    
    await query.message.reply_text(message, parse_mode="Markdown")


async def _handle_mood_for_callback(query, context):
    """Handle mood command from callback query."""
    from app.repositories.user import get_user_repository
    from app.services.mood_service import get_mood_service
    
    user_telegram = query.from_user
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.get_by_telegram_id(user_telegram.id)
    
    if not user:
        await query.message.reply_text(
            "Сначала отправьте мне любое сообщение, чтобы я вас зарегистрировал."
        )
        return
    
    # Get mood history
    mood_service = get_mood_service()
    history = await mood_service.get_mood_history(str(user["id"]), days=7)
    
    if not history:
        await query.message.reply_text(
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
    
    await query.message.reply_text(message, parse_mode="Markdown")
